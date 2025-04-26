import os
import sys
import argparse
from normalizer import SatelliteImageNormalizer
import logging
from app import app

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Normalize brightness of satellite images')
    parser.add_argument('--zip', '-z', required=True, help='Path to the ZIP file containing satellite images')
    parser.add_argument('--output', '-o', default='.', help='Output directory for normalized images')
    parser.add_argument('--target', '-t', type=float, help='Target intensity (default: use global average)')
    parser.add_argument('--web', '-w', action='store_true', help='Run as web application')
    
    args = parser.parse_args()
    
    if args.web:
        # Run the web application
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=True)
        return
    
    # Validate arguments
    if not os.path.exists(args.zip):
        logger.error(f"ZIP file not found: {args.zip}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Initialize and run the normalizer
    try:
        normalizer = SatelliteImageNormalizer(
            zip_path=args.zip,
            output_dir=args.output,
            target_intensity=args.target
        )
        
        success, result, saved_paths = normalizer.process_all()
        
        if success:
            logger.info(f"Normalization completed successfully!")
            logger.info(f"Global average intensity: {result['global_average']:.2f}")
            logger.info(f"Processed {result['image_count']} images")
            
            for img_stats in result['normalized_images']:
                logger.info(f"  - {img_stats['filename']}: "
                            f"Average intensity = {img_stats['average_intensity']:.2f}, "
                            f"Difference from target = {img_stats['difference_from_target']:.2f}")
            
            logger.info(f"Normalized images saved to: {args.output}")
        else:
            logger.error(f"Normalization failed: {result}")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error during normalization: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
