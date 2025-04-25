import os
import numpy as np
from PIL import Image
import zipfile
import argparse

def generate_test_images(output_dir, num_images=10, size=256, min_intensity=50, max_intensity=200):
    """
    Generate test images with varying intensities.
    
    Args:
        output_dir: Directory to save the images
        num_images: Number of images to generate
        size: Image dimensions (size x size)
        min_intensity: Minimum average intensity
        max_intensity: Maximum average intensity
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate individual images with different intensities
    intensities = np.linspace(min_intensity, max_intensity, num_images)
    
    image_paths = []
    
    for i, intensity in enumerate(intensities, 1):
        # Create a base image with the target intensity
        img_array = np.ones((size, size), dtype=np.uint8) * intensity
        
        # Add some random noise to make the image more realistic
        noise = np.random.normal(0, 15, (size, size))
        img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        
        # Save the image
        img_path = os.path.join(output_dir, f"image{i}.png")
        Image.fromarray(img_array).save(img_path)
        image_paths.append(img_path)
        
        # Print image info
        actual_intensity = np.mean(img_array)
        print(f"Generated image{i}.png with average intensity: {actual_intensity:.2f}")
    
    # Calculate global average
    global_avg = np.mean(intensities)
    print(f"Global average intensity: {global_avg:.2f}")
    
    return image_paths, global_avg

def create_zip_file(image_paths, zip_path):
    """Create a ZIP file containing the generated images."""
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for img_path in image_paths:
            zipf.write(img_path, os.path.basename(img_path))
    
    print(f"Created ZIP file: {zip_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate test images for satellite image normalization')
    parser.add_argument('--output', '-o', default='test_images', help='Output directory for images')
    parser.add_argument('--num', '-n', type=int, default=10, help='Number of images to generate')
    parser.add_argument('--size', '-s', type=int, default=256, help='Image size (width and height)')
    parser.add_argument('--min', type=float, default=50, help='Minimum average intensity')
    parser.add_argument('--max', type=float, default=200, help='Maximum average intensity')
    parser.add_argument('--zip', '-z', default='test_images.zip', help='Path for output ZIP file')
    
    args = parser.parse_args()
    
    # Generate images
    image_paths, global_avg = generate_test_images(
        args.output, 
        args.num, 
        args.size,
        args.min,
        args.max
    )
    
    # Create ZIP file
    create_zip_file(image_paths, args.zip)
    
    print(f"Generated {args.num} test images with global average intensity: {global_avg:.2f}")
    print(f"Images saved to: {args.output}")
    print(f"ZIP file created: {args.zip}")

if __name__ == "__main__":
    main()