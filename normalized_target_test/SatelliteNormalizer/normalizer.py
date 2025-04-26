import os
import zipfile
import numpy as np
from PIL import Image
import logging
from io import BytesIO

import matplotlib.pyplot as plt


# Add this function at the top
def plot_intensity_distribution(before_path, after_path, title_prefix=""):
    img_before = Image.open(before_path).convert("L")
    img_after = Image.open(after_path).convert("L")
    arr_before = np.array(img_before).flatten()
    arr_after = np.array(img_after).flatten()

    plt.style.use('seaborn-darkgrid')
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor='white')

    axes[0].hist(arr_before, bins=50, color='blue', alpha=0.8)
    axes[0].set_title(f'{title_prefix}Before Normalization')
    axes[0].set_xlabel('Pixel Intensity')
    axes[0].set_ylabel('Frequency')

    axes[1].hist(arr_after, bins=50, color='orange', alpha=0.8)
    axes[1].set_title(f'{title_prefix}After Normalization')
    axes[1].set_xlabel('Pixel Intensity')
    axes[1].set_ylabel('Frequency')

    plt.tight_layout()
    plt.show()


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SatelliteImageNormalizer:
    """Class for normalizing the brightness of satellite images."""
    
    def __init__(self, zip_path=None, output_dir='.', target_intensity=None):
        """
        Initialize the normalizer.
        
        Args:
            zip_path (str): Path to the ZIP file containing images
            output_dir (str): Directory to save normalized images
            target_intensity (float, optional): Target intensity for normalization.
                If None, the global average is used.
        """
        self.zip_path = zip_path
        self.output_dir = output_dir
        self.target_intensity = target_intensity
        self.images = []
        self.image_arrays = []
        self.global_avg = None
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def extract_images(self):
        """Extract images from the ZIP file."""
        logger.info(f"Extracting images from {self.zip_path}")
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                # Get list of image files (assuming PNG files)
                image_files = [f for f in zip_ref.namelist() if f.lower().endswith('.png')]
                
                if not image_files:
                    raise ValueError("No PNG images found in the ZIP file")
                
                # Check expected number of images (10 images required)
                if len(image_files) != 10:
                    logger.warning(f"Expected 10 PNG images, but found {len(image_files)}")
                
                logger.info(f"Found {len(image_files)} images in the ZIP file")
                
                # Extract and load each image
                for img_file in image_files:
                    img_data = zip_ref.read(img_file)
                    img = Image.open(BytesIO(img_data)).convert('L')  # Convert to grayscale
                    
                    # Verify image dimensions (should be 256x256)
                    if img.width != 256 or img.height != 256:
                        logger.warning(f"Image {os.path.basename(img_file)} has dimensions {img.width}x{img.height}, expected 256x256")
                        # Resize if needed
                        img = img.resize((256, 256))
                    
                    self.images.append((os.path.basename(img_file), img))
                
                logger.info(f"Successfully extracted {len(self.images)} images")
                return len(self.images)
        
        except (zipfile.BadZipFile, IOError) as e:
            logger.error(f"Error extracting images: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while extracting images: {str(e)}")
            raise ValueError(f"Error processing ZIP file: {str(e)}")
    
    def load_images(self):
        """Load images into NumPy arrays for processing."""
        logger.info("Converting images to arrays")
        
        self.image_arrays = []
        for _, img in self.images:
            # Convert PIL image to NumPy array
            img_array = np.array(img, dtype=np.float32)
            self.image_arrays.append(img_array)
        
        logger.info(f"Converted {len(self.image_arrays)} images to arrays")
    
    def calculate_global_average(self):
        """Calculate the global average intensity across all images."""
        if not self.image_arrays:
            raise ValueError("No images loaded. Call load_images() first.")
        
        # Concatenate all arrays and calculate the mean
        all_pixels = np.concatenate([img.flatten() for img in self.image_arrays])
        self.global_avg = np.mean(all_pixels)
        
        logger.info(f"Global average intensity: {self.global_avg}")
        return self.global_avg
    
    def normalize_images(self):
        """Normalize each image to match the global average intensity."""
        if self.global_avg is None:
            self.calculate_global_average()
        
        # Use target intensity if provided, otherwise use global average
        target = self.target_intensity if self.target_intensity is not None else self.global_avg
        logger.info(f"Normalizing images to target intensity: {target}")
        
        normalized_images = []
        
        for i, img_array in enumerate(self.image_arrays):
            # Calculate current average intensity
            current_avg = np.mean(img_array)
            logger.debug(f"Image {i+1} - Current average: {current_avg}")
            
            # Calculate scaling factor
            if current_avg > 0:  # Avoid division by zero
                scaling_factor = target / current_avg
            else:
                scaling_factor = 1.0
                logger.warning(f"Image {i+1} has zero average intensity, using scaling factor of 1.0")
            
            # Apply scaling factor (optimize by doing in-place if possible)
            normalized = img_array * scaling_factor
            
            # Ensure values are within 0-255 range
            normalized = np.clip(normalized, 0, 255)
            
            # Convert back to proper image format
            normalized = normalized.astype(np.uint8)
            
            # Calculate new average to verify
            new_avg = np.mean(normalized)
            logger.debug(f"Image {i+1} - New average: {new_avg}, Target: {target}")
            
            # Verify normalization accuracy
            if abs(new_avg - target) > 1.0:
                logger.warning(f"Image {i+1} - Normalization not within ±1 threshold: {new_avg} vs {target}")
                
                # Apply fine adjustment if needed (more accurate adjustment)
                adjustment = target - new_avg
                # Convert back to float32 for precise adjustment
                normalized = np.clip(normalized.astype(np.float32) + adjustment, 0, 255).astype(np.uint8)
                final_avg = np.mean(normalized)
                logger.debug(f"Image {i+1} - After adjustment: {final_avg}")
                
                # If still not within threshold, apply a secondary proportional adjustment
                if abs(final_avg - target) > 1.0:
                    logger.warning(f"Image {i+1} - Secondary adjustment needed")
                    sec_factor = target / final_avg
                    normalized = np.clip(normalized.astype(np.float32) * sec_factor, 0, 255).astype(np.uint8)
                    final_avg = np.mean(normalized)
                    logger.debug(f"Image {i+1} - After secondary adjustment: {final_avg}")
            
            # Create PIL image from array
            normalized_img = Image.fromarray(normalized)
            normalized_images.append(normalized_img)
        
        logger.info(f"Successfully normalized {len(normalized_images)} images")
        return normalized_images
    
    def save_normalized_images(self, normalized_images=None):
        """Save the normalized images with proper naming."""
        if normalized_images is None:
            normalized_images = self.normalize_images()
        
        saved_paths = []
        
        for i, img in enumerate(normalized_images):
            output_path = os.path.join(self.output_dir, f"normalized_image{i+1}.png")
            img.save(output_path)
            logger.info(f"Saved normalized image to {output_path}")
            saved_paths.append(output_path)
        
        return saved_paths
    
    def process_all(self):
        """Run the complete normalization process."""
        try:
            import time
            start_time = time.time()
            
            self.extract_images()
            self.load_images()
            self.calculate_global_average()
            normalized_images = self.normalize_images()
            saved_paths = self.save_normalized_images(normalized_images)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Calculate and return statistics
            stats = {
                "global_average": self.global_avg,
                "image_count": len(self.images),
                "processing_time": processing_time,
                "normalized_images": []
            }
            
            # Verify all images are within target range (±1)
            images_within_threshold = 0
            target = self.target_intensity if self.target_intensity is not None else self.global_avg
            
            for i, img in enumerate(normalized_images):
                img_array = np.array(img)
                avg_intensity = np.mean(img_array)
                difference = abs(avg_intensity - target)
                
                # Check if within threshold
                within_threshold = difference <= 1.0
                if within_threshold:
                    images_within_threshold += 1
                
                stats["normalized_images"].append({
                    "filename": f"normalized_image{i+1}.png",
                    "average_intensity": avg_intensity,
                    "difference_from_target": difference,
                    "within_threshold": within_threshold
                })
            
            # Add score calculation as per requirements
            stats["images_within_threshold"] = images_within_threshold
            stats["score"] = (images_within_threshold / len(normalized_images)) * 10 if normalized_images else 0
            
            logger.info(f"Processing completed in {processing_time:.2f} seconds")
            logger.info(f"Score: {stats['score']:.1f}/10 ({images_within_threshold}/{len(normalized_images)} images within threshold)")
            
            return True, stats, saved_paths
        
        except Exception as e:
            logger.error(f"Error in processing: {str(e)}")
            return False, str(e), []
