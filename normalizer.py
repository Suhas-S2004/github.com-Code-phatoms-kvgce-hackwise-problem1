import os
import zipfile
import numpy as np
from PIL import Image
import logging
from io import BytesIO

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
                
                logger.info(f"Found {len(image_files)} images in the ZIP file")
                
                # Extract and load each image
                for img_file in image_files:
                    img_data = zip_ref.read(img_file)
                    img = Image.open(BytesIO(img_data)).convert('L')  # Convert to grayscale
                    self.images.append((os.path.basename(img_file), img))
                
                logger.info(f"Successfully extracted {len(self.images)} images")
                return len(self.images)
        
        except (zipfile.BadZipFile, IOError) as e:
            logger.error(f"Error extracting images: {str(e)}")
            raise
    
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
            
            # Apply scaling factor
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
                
                # Apply fine adjustment if needed
                adjustment = target - new_avg
                normalized = np.clip(normalized.astype(np.float32) + adjustment, 0, 255).astype(np.uint8)
                final_avg = np.mean(normalized)
                logger.debug(f"Image {i+1} - After adjustment: {final_avg}")
            
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
            self.extract_images()
            self.load_images()
            self.calculate_global_average()
            normalized_images = self.normalize_images()
            saved_paths = self.save_normalized_images(normalized_images)
            
            # Calculate and return statistics
            stats = {
                "global_average": self.global_avg,
                "image_count": len(self.images),
                "normalized_images": []
            }
            
            for i, img in enumerate(normalized_images):
                img_array = np.array(img)
                avg_intensity = np.mean(img_array)
                stats["normalized_images"].append({
                    "filename": f"normalized_image{i+1}.png",
                    "average_intensity": avg_intensity,
                    "difference_from_target": abs(avg_intensity - self.global_avg)
                })
            
            return True, stats, saved_paths
        
        except Exception as e:
            logger.error(f"Error in processing: {str(e)}")
            return False, str(e), []
