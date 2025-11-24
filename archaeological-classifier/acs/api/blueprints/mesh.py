"""
Mesh Processing Blueprint
=========================

Endpoints for 3D mesh upload, processing, and feature extraction.
"""

from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.utils import secure_filename
import os
import time
from acs.core.mesh_processor import MeshProcessor
from acs.core.database import ArtifactDatabase
from acs.core.auth import login_required, role_required
from acs.core.file_validator import (
    FileValidator,
    FileValidationError,
    upload_rate_limiter
)

mesh_bp = Blueprint('mesh', __name__)

# Global instances
processor = MeshProcessor()
db = ArtifactDatabase()


@mesh_bp.route('/upload', methods=['POST'])
@role_required('admin', 'archaeologist')
def upload_mesh():
    """
    Upload and process a single mesh file.

    Requires: admin or archaeologist role

    Security:
    - Max file size: 100 MB (web), 500 MB (API)
    - File type validation (magic bytes)
    - Mesh integrity check
    - Rate limiting: 10 uploads/minute

    Returns:
        JSON with extracted features
    """
    # Rate limiting
    user_id = str(g.current_user.get('user_id', 'anonymous'))
    if not upload_rate_limiter.is_allowed(user_id):
        remaining = upload_rate_limiter.get_remaining(user_id)
        return jsonify({
            'error': 'Rate limit exceeded. Please try again later.',
            'code': 'RATE_LIMIT_EXCEEDED',
            'remaining': remaining
        }), 429

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        # Determine max size based on source (web vs API)
        is_web_upload = request.headers.get('X-Upload-Source') == 'web'
        max_size = FileValidator.MAX_SIZE_WEB if is_web_upload else FileValidator.MAX_SIZE_API

        # Validate file
        safe_filename, detected_type = FileValidator.validate_upload(
            file,
            max_size=max_size,
            check_integrity=False  # We'll check after saving
        )

        # Save file
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(filepath)

        # Validate mesh integrity
        is_valid, error_msg = FileValidator.validate_mesh_integrity(filepath)
        if not is_valid:
            # Clean up invalid file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({
                'error': error_msg,
                'code': 'INVALID_MESH'
            }), 400

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
            'file_type': detected_type,
            'message': f'Mesh processed successfully'
        })

    except FileValidationError as e:
        return jsonify({
            'error': e.message,
            'code': e.error_code
        }), 400

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


@mesh_bp.route('/artifacts', methods=['GET'])
@login_required
def get_artifacts():
    """
    Get paginated list of artifacts from database.

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)

    Returns:
        JSON with paginated artifacts and metadata:
        - artifacts: List of artifact objects
        - total: Total number of artifacts
        - page: Current page
        - per_page: Items per page
        - pages: Total number of pages
    """
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Validate parameters
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20
        elif per_page > 100:
            per_page = 100  # Max 100 items per page

        # Get paginated artifacts
        result = db.get_artifacts_paginated(page=page, per_page=per_page)

        return jsonify({
            'status': 'success',
            **result
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mesh_bp.route('/artifacts/<artifact_id>', methods=['GET'])
@login_required
def get_artifact_from_db(artifact_id):
    """
    Get details for a specific artifact from database.

    Args:
        artifact_id: ID of the artifact

    Returns:
        JSON with artifact details including features
    """
    try:
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({
                'error': f'Artifact {artifact_id} not found'
            }), 404

        # Get features if available
        try:
            features = db.get_features(artifact_id)
            artifact['features'] = features
        except:
            artifact['features'] = {}

        return jsonify({
            'status': 'success',
            'artifact': artifact
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mesh_bp.route('/artifacts/<artifact_id>', methods=['DELETE'])
@role_required('admin', 'archaeologist')
def delete_artifact(artifact_id):
    """
    Delete an artifact and all associated data.

    Requires: admin or archaeologist role

    This will delete:
    - Artifact record from database
    - All features
    - All classifications
    - All training samples
    - All comparisons
    - Associated mesh file (if exists)

    Args:
        artifact_id: ID of the artifact to delete

    Returns:
        JSON with deletion status
    """
    try:
        # Check if artifact exists in database
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({
                'error': f'Artifact {artifact_id} not found'
            }), 404

        # Delete from database (includes all related data)
        deleted = db.delete_artifact(artifact_id)

        if not deleted:
            return jsonify({
                'error': f'Failed to delete artifact {artifact_id}'
            }), 500

        # Remove from mesh processor memory if loaded
        if artifact_id in processor.meshes:
            del processor.meshes[artifact_id]

        # Delete mesh file if exists
        mesh_file = artifact.get('file_path')
        if mesh_file and os.path.exists(mesh_file):
            try:
                os.remove(mesh_file)
            except Exception as e:
                # Log but don't fail if file deletion fails
                print(f"Warning: Could not delete mesh file {mesh_file}: {e}")

        return jsonify({
            'status': 'success',
            'message': f'Artifact {artifact_id} deleted successfully',
            'artifact_id': artifact_id
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
