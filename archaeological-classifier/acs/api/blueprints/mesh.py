"""
Mesh Processing Blueprint
=========================

Endpoints for 3D mesh upload, processing, and feature extraction.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import time
from acs.core.mesh_processor import MeshProcessor
from acs.core.auth import login_required, role_required

mesh_bp = Blueprint('mesh', __name__)

# Global mesh processor instance
processor = MeshProcessor()

ALLOWED_EXTENSIONS = {'.obj', '.ply', '.stl'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


@mesh_bp.route('/upload', methods=['POST'])
@role_required('admin', 'archaeologist')
def upload_mesh():
    """
    Upload and process a single mesh file.

    Requires: admin or archaeologist role

    Returns:
        JSON with extracted features
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    try:
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Get artifact ID from request or use filename
        artifact_id = request.form.get('artifact_id')

        # Process mesh
        start_time = time.time()
        features = processor.load_mesh(filepath, artifact_id)
        processing_time = time.time() - start_time

        return jsonify({
            'status': 'success',
            'artifact_id': features['id'],
            'features': features,
            'processing_time': processing_time,
            'message': f'Mesh processed successfully'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mesh_bp.route('/batch', methods=['POST'])
@role_required('admin', 'archaeologist')
def batch_process():
    """
    Batch process multiple uploaded meshes.

    Requires: admin or archaeologist role

    Expects: Multiple files in 'files[]' field

    Returns:
        JSON with processing results
    """
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')

    if not files:
        return jsonify({'error': 'No files selected'}), 400

    results = []
    filepaths = []

    # Save all files
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            filepaths.append(filepath)

    # Process batch
    try:
        batch_results = processor.batch_process(filepaths)

        successful = sum(1 for r in batch_results if r['status'] == 'success')
        failed = sum(1 for r in batch_results if r['status'] == 'error')

        return jsonify({
            'status': 'completed',
            'total': len(batch_results),
            'successful': successful,
            'failed': failed,
            'results': batch_results
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mesh_bp.route('/<artifact_id>', methods=['GET'])
@login_required
def get_artifact(artifact_id):
    """
    Get features for a specific artifact.

    Requires: any authenticated user

    Args:
        artifact_id: Artifact identifier

    Returns:
        JSON with artifact features
    """
    if artifact_id not in processor.meshes:
        return jsonify({'error': f'Artifact {artifact_id} not found'}), 404

    try:
        mesh = processor.meshes[artifact_id]
        features = processor._extract_features(mesh, artifact_id)

        return jsonify({
            'status': 'success',
            'artifact_id': artifact_id,
            'features': features
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mesh_bp.route('/<id1>/distance/<id2>', methods=['GET'])
@login_required
def compute_distance(id1, id2):
    """
    Compute distance between two meshes.

    Requires: any authenticated user

    Args:
        id1: First artifact ID
        id2: Second artifact ID

    Query params:
        method: Distance method ('hausdorff' or 'chamfer')

    Returns:
        JSON with distance value
    """
    method = request.args.get('method', 'hausdorff')

    if id1 not in processor.meshes:
        return jsonify({'error': f'Artifact {id1} not found'}), 404

    if id2 not in processor.meshes:
        return jsonify({'error': f'Artifact {id2} not found'}), 404

    try:
        distance = processor.compute_distance(id1, id2, method=method)

        return jsonify({
            'status': 'success',
            'artifact_1': id1,
            'artifact_2': id2,
            'method': method,
            'distance': distance
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mesh_bp.route('/export', methods=['POST'])
@role_required('admin')
def export_features():
    """
    Export all extracted features to file.

    Requires: admin role

    Body:
        format: 'json' or 'csv'

    Returns:
        JSON with export status
    """
    data = request.get_json()
    format_type = data.get('format', 'json')

    if format_type not in ['json', 'csv']:
        return jsonify({'error': 'Invalid format. Use json or csv'}), 400

    try:
        output_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            f'features_export.{format_type}'
        )

        processor.export_features(output_path, format=format_type)

        return jsonify({
            'status': 'success',
            'filepath': output_path,
            'format': format_type,
            'n_artifacts': len(processor.meshes)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
