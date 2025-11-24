"""
Flask web application for Archaeological Axe Classification System (ACS).
Provides web interface for uploading mesh files and generating comprehensive reports.
"""

from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os
import sys
from pathlib import Path
import logging

# Add archaeological-classifier to path
sys.path.insert(0, str(Path(__file__).parent / 'archaeological-classifier'))

from acs.savignano.comprehensive_report import SavignanoComprehensiveReport
from acs.savignano.morphometric_extractor import SavignanoMorphometricExtractor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'obj'}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Main page with upload form."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle mesh file upload and generate report."""
    try:
        # Check if file was uploaded
        if 'mesh_file' not in request.files:
            return jsonify({'error': 'Nessun file caricato'}), 400

        file = request.files['mesh_file']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'Nessun file selezionato'}), 400

        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({'error': 'Formato file non valido. Solo file .obj sono supportati'}), 400

        # Get artifact ID from form
        artifact_id = request.form.get('artifact_id', '').strip()
        if not artifact_id:
            # Generate artifact ID from filename
            artifact_id = Path(file.filename).stem

        # Get language from form
        language = request.form.get('language', 'it')

        # Save uploaded file
        filename = secure_filename(file.filename)
        mesh_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(mesh_path)

        logger.info(f"File uploaded: {mesh_path}")
        logger.info(f"Generating report for artifact: {artifact_id}")

        # Generate report
        report = SavignanoComprehensiveReport(
            mesh_path=mesh_path,
            artifact_id=artifact_id,
            language=language
        )

        result = report.generate()

        if result['status'] == 'success':
            pdf_path = result['comprehensive_report']
            logger.info(f"Report generated successfully: {pdf_path}")

            return jsonify({
                'status': 'success',
                'message': 'Report generato con successo',
                'artifact_id': artifact_id,
                'pdf_url': f'/download/{artifact_id}'
            })
        else:
            logger.error(f"Report generation failed: {result.get('error', 'Unknown error')}")
            return jsonify({
                'status': 'error',
                'message': f"Errore nella generazione del report: {result.get('error', 'Errore sconosciuto')}"
            }), 500

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Errore durante il processamento: {str(e)}'
        }), 500

@app.route('/download/<artifact_id>')
def download_report(artifact_id):
    """Download generated PDF report."""
    try:
        # Find report in .acs/reports directory
        reports_dir = Path.home() / '.acs' / 'reports' / artifact_id

        # Try to find PDF report (Italian or English)
        pdf_files = list(reports_dir.glob(f'{artifact_id}_comprehensive_report_*.pdf'))

        if not pdf_files:
            return jsonify({'error': 'Report non trovato'}), 404

        pdf_path = pdf_files[0]  # Get first matching PDF

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{artifact_id}_report.pdf'
        )

    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}", exc_info=True)
        return jsonify({'error': f'Errore nel download: {str(e)}'}), 500

@app.route('/reports')
def list_reports():
    """List all generated reports."""
    try:
        reports_dir = Path.home() / '.acs' / 'reports'

        if not reports_dir.exists():
            return render_template('reports.html', reports=[])

        reports = []
        for artifact_dir in reports_dir.iterdir():
            if artifact_dir.is_dir():
                # Find PDF reports in this artifact directory
                pdf_files = list(artifact_dir.glob('*_comprehensive_report_*.pdf'))
                if pdf_files:
                    pdf_path = pdf_files[0]
                    reports.append({
                        'artifact_id': artifact_dir.name,
                        'filename': pdf_path.name,
                        'size': f'{pdf_path.stat().st_size / 1024:.1f} KB',
                        'modified': pdf_path.stat().st_mtime
                    })

        # Sort by modification time (newest first)
        reports.sort(key=lambda x: x['modified'], reverse=True)

        return render_template('reports.html', reports=reports)

    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}", exc_info=True)
        return jsonify({'error': f'Errore nel caricamento della lista: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
