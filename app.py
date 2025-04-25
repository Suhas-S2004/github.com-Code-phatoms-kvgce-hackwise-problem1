import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import tempfile
from normalizer import SatelliteImageNormalizer

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure upload settings
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    # Check for target intensity parameter
    target_intensity = None
    if request.form.get('target_intensity'):
        try:
            target_intensity = float(request.form.get('target_intensity'))
            if target_intensity < 0 or target_intensity > 255:
                flash('Target intensity must be between 0 and 255')
                return redirect(request.url)
            logger.info(f"Using specified target intensity: {target_intensity}")
        except ValueError:
            flash('Invalid target intensity value. Please enter a valid number.')
            return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create output directory
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Process the file
        normalizer = SatelliteImageNormalizer(
            zip_path=file_path,
            output_dir=output_dir,
            target_intensity=target_intensity
        )
        
        success, result, saved_paths = normalizer.process_all()
        
        if success:
            return render_template('results.html', 
                                  stats=result, 
                                  output_dir='output')
        else:
            flash(f'Error processing file: {result}')
            return redirect(request.url)
    else:
        flash('File type not allowed. Please upload a ZIP file.')
        return redirect(request.url)

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'output'),
                               filename, as_attachment=True)

@app.route('/output/<path:filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'output'),
                               filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
