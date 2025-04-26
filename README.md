=======================================================
SATELLITE IMAGE BRIGHTNESS NORMALIZER
=======================================================



A comprehensive Python tool for normalizing brightness levels across
satellite imagery to ensure consistent average intensity.

--------------------------------------------------------
OVERVIEW
--------------------------------------------------------

The Satellite Image Brightness Normalizer is designed to process grayscale
satellite images and adjust their brightness to match a global average intensity.
This is essential for applications like change detection, image mosaicking, and
automated image analysis, where consistent brightness across images is critical.

--------------------------------------------------------
FEATURES
--------------------------------------------------------

1. Core Processing:
   - Extracts images from ZIP archives
   - Calculates global average intensity across all images
   - Normalizes each image to match the global average
   - Validates normalized images against tolerance criteria
   - Clips pixel values to ensure they stay within 0-255 range

2. Performance:
   - Processes datasets in under 10 seconds (tested on Intel i5 with 8GB RAM)
   - Reports detailed performance statistics
   - Minimizes memory usage for large datasets

3. Visualization:
   - Interactive dashboard with comprehensive statistics
   - Detailed histograms showing pixel intensity distribution
   - Side-by-side comparison of original and normalized images
   - Pie charts showing brightness distribution by category
   - Bar charts displaying image averages with success indicators
   - Normalization accuracy verdict with clear pass/fail status

--------------------------------------------------------
USAGE
--------------------------------------------------------

Command Line:
  python satellite_normalizer.py <input_zip_file>

Web Interface:
  1. Start the web server: gunicorn --bind 0.0.0.0:5000 main:app.py
  2. Visit http://127.0.0.1:5000 and http://192.168.1.55:5000 in your browser
  3. Upload a ZIP file containing PNG grayscale satellite images
  4. View the interactive dashboard and download normalized images

Example:
  python satellite_normalizer.py sample_dataset.zip

--------------------------------------------------------
NORMALIZATION PROCESS
--------------------------------------------------------

The normalization algorithm follows these steps:

1. Global Average Calculation:
   - Calculate the average pixel intensity across all images

2. Individual Image Processing:
   - For each image:
     a. Calculate the image's current average intensity
     b. Compute a scaling factor = global_average / image_average
     c. Multiply all pixel values by this scaling factor
     d. Clip any values outside the 0-255 range

3. Validation:
   - Verify that each normalized image's average is within ±1 of the global target

--------------------------------------------------------
ACCURACY ASSESSMENT
--------------------------------------------------------

The tool provides an accuracy verdict based on normalization success rate:

- EXCELLENT: 100% of images successfully normalized
- GOOD: 80-99% of images successfully normalized
- MODERATE: 50-79% of images successfully normalized
- POOR: Less than 50% of images successfully normalized

A successful normalization means the image's average intensity is
within ±1.0 of the global target average.

--------------------------------------------------------
DEPENDENCIES
--------------------------------------------------------

- Python 3.10+
- NumPy: For numerical operations
- PIL (Pillow): For image processing
- Matplotlib: For visualization
- Flask: For web interface (optional)

--------------------------------------------------------
PROJECT STRUCTURE
--------------------------------------------------------

- satellite_normalizer.py: Core processing logic
- main.py: Web interface using Flask
- templates/: HTML templates for web interface
- static/: CSS files for web interface
- results/: Directory for normalized output images

--------------------------------------------------------
