import os
import time
import base64
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
from cloud_removal import CloudRemover
from analysis_engine import AnalysisEngine

app = Flask(__name__)

# Base directory configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
RESULTS_FOLDER = os.path.join(BASE_DIR, 'static', 'results')
ANALYSIS_FOLDER = os.path.join(BASE_DIR, 'static', 'analysis')

# Auto-create necessary directories
for folder in [UPLOAD_FOLDER, RESULTS_FOLDER, ANALYSIS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['ANALYSIS_FOLDER'] = ANALYSIS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB max upload limit

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tif', 'tiff', 'webp'}

remover = CloudRemover()
analyzer = AnalysisEngine()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file type. Please upload PNG, JPG, BMP, or TIFF satellite images.'}), 400

    try:
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        saved_filename = f"{timestamp}_{filename}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        output_filename = f"clear_{saved_filename}"
        output_path = os.path.join(app.config['RESULTS_FOLDER'], output_filename)
        
        mask_filename = f"mask_{saved_filename}"
        mask_path = os.path.join(app.config['RESULTS_FOLDER'], mask_filename)

        file.save(input_path)

        # Process cloud removal & calculate metrics
        metrics = remover.process(input_path, output_path, mask_path)

        # Read processed image into Base64 for instant frontend preview
        with open(output_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        return jsonify({
            'success': True,
            'filename': output_filename,
            'original_filename': saved_filename,
            'output_image': encoded_string,
            'input_image_url': f"/static/uploads/{saved_filename}",
            'output_image_url': f"/static/results/{output_filename}",
            'mask_image_url': f"/static/results/{mask_filename}",
            'processing_time': metrics['processing_time'],
            'input_size': metrics['input_size_kb'],
            'output_size': metrics['output_size_kb'],
            'contrast_improvement': metrics['contrast_improvement'],
            'haze_reduction_percent': metrics['haze_reduction_percent'],
            'cloud_coverage_est': metrics.get('cloud_coverage_est', 0),
            'histogram_labels': metrics.get('histogram_labels', []),
            'histogram_before': metrics.get('histogram_before', []),
            'histogram_after': metrics.get('histogram_after', [])
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/<module_name>', methods=['POST'])
def run_analysis(module_name):
    data = request.get_json() or {}
    filename = data.get('filename')

    if not filename:
        return jsonify({'error': 'Filename missing for analysis.'}), 400

    input_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
    if not os.path.exists(input_path):
        # Fallback to upload directory if result file doesn't exist
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(input_path):
        return jsonify({'error': f"Target image '{filename}' not found."}), 404

    analysis_filename = f"analysis_{module_name}_{filename}"
    output_path = os.path.join(app.config['ANALYSIS_FOLDER'], analysis_filename)

    try:
        if module_name == 'ndvi':
            result = analyzer.run_ndvi(input_path, output_path)
        elif module_name == 'flood':
            result = analyzer.run_flood_detection(input_path, output_path)
        elif module_name == 'building':
            result = analyzer.run_building_detection(input_path, output_path)
        elif module_name == 'landcover':
            result = analyzer.run_land_cover(input_path, output_path)
        else:
            return jsonify({'error': f"Unknown analysis module '{module_name}'."}), 400

        result['analysis_image_url'] = f"/static/analysis/{analysis_filename}?t={int(time.time())}"
        result['download_url'] = f"/download/{analysis_filename}?folder=analysis"
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    folder_type = request.args.get('folder', 'results')
    if folder_type == 'analysis':
        directory = app.config['ANALYSIS_FOLDER']
    elif folder_type == 'uploads':
        directory = app.config['UPLOAD_FOLDER']
    else:
        directory = app.config['RESULTS_FOLDER']

    return send_from_directory(directory, filename, as_attachment=True)

if __name__ == '__main__':
    print("=" * 60)
    print("[SAT] Satellite Cloud Removal & Analysis System Backend Active")
    print("[SIH] SIH 2026 Space Technology Solution (ID: 26209)")
    print("[URL] Access Dashboard at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
