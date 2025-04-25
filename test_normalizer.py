from normalizer import SatelliteImageNormalizer
import os
import numpy as np
from PIL import Image
import argparse

def verify_normalized_images(input_zip, output_dir, target_intensity=None):
    """Test the normalizer and verify the results."""
    print(f"Testing normalizer with input: {input_zip}")
    print(f"Output directory: {output_dir}")
    print(f"Target intensity: {target_intensity}")
    
    # Create and run the normalizer
    normalizer = SatelliteImageNormalizer(
        zip_path=input_zip,
        output_dir=output_dir,
        target_intensity=target_intensity
    )
    
    success, stats, saved_paths = normalizer.process_all()
    
    if not success:
        print(f"Error: {stats}")
        return
    
    # Print statistics
    print("\n--- Normalization Statistics ---")
    print(f"Global average intensity: {stats['global_average']:.2f}")
    print(f"Processing time: {stats['processing_time']:.2f} seconds")
    print(f"Images processed: {stats['image_count']}")
    print(f"Images within threshold: {stats['images_within_threshold']}/{stats['image_count']}")
    print(f"Score: {stats['score']:.1f}/10")
    
    # Print individual image statistics
    print("\n--- Individual Image Results ---")
    for img_stats in stats["normalized_images"]:
        status = "✅ PASSED" if img_stats["within_threshold"] else "❌ FAILED"
        print(f"{img_stats['filename']}: Avg={img_stats['average_intensity']:.2f}, " +
              f"Diff={img_stats['difference_from_target']:.2f}, {status}")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Test the satellite image normalizer')
    parser.add_argument('--input', '-i', default='test_images.zip', help='Input ZIP file')
    parser.add_argument('--output', '-o', default='normalized_output', help='Output directory')
    parser.add_argument('--target', '-t', type=float, default=None, help='Target intensity (optional)')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Run the test
    stats = verify_normalized_images(args.input, args.output, args.target)

if __name__ == "__main__":
    main()