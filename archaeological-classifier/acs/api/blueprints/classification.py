"""
Classification System Blueprint
===============================

Endpoints for formal taxonomy management and classification.
"""

from flask import Blueprint, request, jsonify
from acs.core.auth import login_required, role_required, current_app, send_file
from acs.core.taxonomy import FormalTaxonomySystem
from acs.savignano.taxonomy_rules import SavignanoClassifier, classify_savignano_artifact
import os

classification_bp = Blueprint('classification', __name__)

# Global taxonomy system instances
taxonomy = FormalTaxonomySystem()
savignano_classifier = SavignanoClassifier()


@classification_bp.route('/define-class', methods=['POST'])
@role_required('admin', 'archaeologist')
def define_class():
    """
    Define new taxonomic class from reference group.

    Body:
        class_name: Name for the class
        reference_objects: List of reference artifact features
        parameter_weights: Optional parameter weights
        tolerance_factor: Tolerance factor (default 0.15)

    Returns:
        JSON with new class details
    """
    data = request.get_json()

    class_name = data.get('class_name')
    reference_objects = data.get('reference_objects')
    parameter_weights = data.get('parameter_weights')
    tolerance_factor = data.get('tolerance_factor', 0.15)

    if not class_name or not reference_objects:
        return jsonify({'error': 'class_name and reference_objects required'}), 400

    try:
        new_class = taxonomy.define_class_from_reference_group(
            class_name=class_name,
            reference_objects=reference_objects,
            parameter_weights=parameter_weights,
            tolerance_factor=tolerance_factor
        )

        return jsonify({
            'status': 'success',
            'class': new_class.to_dict(),
            'message': f'Class {class_name} created successfully'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@classification_bp.route('/classify', methods=['POST'])
@role_required('admin', 'archaeologist')
def classify_artifact():
    """
    Classify an artifact using defined taxonomy.

    Body:
        artifact_features: Feature dictionary
        return_all_scores: Return all class scores (default False)

    Returns:
        JSON with classification result
    """
    data = request.get_json()

    artifact_features = data.get('artifact_features')
    return_all_scores = data.get('return_all_scores', False)

    if not artifact_features:
        return jsonify({'error': 'artifact_features required'}), 400

    try:
        result = taxonomy.classify_object(
            obj_features=artifact_features,
            return_all_scores=return_all_scores
        )

        return jsonify({
            'status': 'success',
            'result': result
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@classification_bp.route('/classify-savignano', methods=['POST'])
@role_required('admin', 'archaeologist')
def classify_savignano():
    """
    Classify artifact using Savignano morphometric taxonomy.

    This endpoint uses formal parametric rules to classify Bronze Age axes
    as Savignano type based on morphometric features.

    Body:
        artifact_id: Artifact identifier (optional)
        features: Feature dictionary (can be full features or just Savignano features)

    Returns:
        JSON with Savignano classification result including:
        - classified: Boolean indicating if artifact matches Savignano type
        - type: Classification type (e.g., "Savignano Type", "Savignano Matrix A")
        - confidence: Confidence score (0.0 to 1.0)
        - diagnostic: Detailed parameter analysis
    """
    data = request.get_json()

    artifact_id = data.get('artifact_id', 'unknown')
    features = data.get('features')

    if not features:
        return jsonify({
            'status': 'error',
            'error': 'features required'
        }), 400

    try:
        # Classify using Savignano taxonomy rules
        result = classify_savignano_artifact(artifact_id, features)

        return jsonify({
            'status': 'success',
            'result': result,
            'message': 'Savignano classification complete'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'artifact_id': artifact_id
        }), 500


@classification_bp.route('/savignano-classes', methods=['GET'])
@login_required
def get_savignano_classes():
    """
    Get all defined Savignano taxonomic classes.

    Returns:
        JSON with all Savignano taxonomic classes and their parameters
    """
    try:
        classes_dict = {}

        for class_id, taxonomic_class in savignano_classifier.classes.items():
            classes_dict[class_id] = {
                'class_id': class_id,
                'name': taxonomic_class.name,
                'description': taxonomic_class.description,
                'confidence_threshold': taxonomic_class.confidence_threshold,
                'morphometric_params': {
                    k: v.to_dict() for k, v in taxonomic_class.morphometric_params.items()
                },
                'optional_features': taxonomic_class.optional_features,
                'validated_samples': taxonomic_class.validated_samples,
                'created_by': taxonomic_class.created_by
            }

        return jsonify({
            'status': 'success',
            'classes': classes_dict,
            'count': len(classes_dict)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@classification_bp.route('/modify-class', methods=['POST'])
@role_required('admin', 'archaeologist')
def modify_class():
    """
    Modify class parameters with justification.

    Body:
        class_id: ID of class to modify
        parameter_changes: Dictionary of changes
        justification: Archaeological justification
        operator: Person making the change

    Returns:
        JSON with new class version
    """
    data = request.get_json()

    class_id = data.get('class_id')
    parameter_changes = data.get('parameter_changes')
    justification = data.get('justification')
    operator = data.get('operator')

    if not all([class_id, parameter_changes, justification, operator]):
        return jsonify({
            'error': 'class_id, parameter_changes, justification, and operator required'
        }), 400

    try:
        new_class = taxonomy.modify_class_parameters(
            class_id=class_id,
            parameter_changes=parameter_changes,
            justification=justification,
            operator=operator
        )

        return jsonify({
            'status': 'success',
            'new_class': new_class.to_dict(),
            'message': f'Class modified. New version: {new_class.class_id}'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@classification_bp.route('/discover', methods=['POST'])
@role_required('admin', 'archaeologist')
def discover_classes():
    """
    Discover new classes from unclassified artifacts.

    Body:
        unclassified_objects: List of artifact features
        min_cluster_size: Minimum cluster size (default 5)
        eps: DBSCAN epsilon (default 0.3)

    Returns:
        JSON with discovered classes
    """
    data = request.get_json()

    unclassified_objects = data.get('unclassified_objects')
    min_cluster_size = data.get('min_cluster_size', 5)
    eps = data.get('eps', 0.3)

    if not unclassified_objects:
        return jsonify({'error': 'unclassified_objects required'}), 400

    try:
        new_classes = taxonomy.discover_new_classes(
            unclassified_objects=unclassified_objects,
            min_cluster_size=min_cluster_size,
            eps=eps
        )

        return jsonify({
            'status': 'success',
            'n_discovered': len(new_classes),
            'classes': [c.to_dict() for c in new_classes]
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@classification_bp.route('/classes', methods=['GET'])
@login_required
def list_classes():
    """
    List all defined classes.

    Returns:
        JSON with class list
    """
    try:
        classes_list = [
            {
                'class_id': class_id,
                'name': tax_class.name,
                'description': tax_class.description,
                'n_parameters': len(tax_class.morphometric_params) + len(tax_class.technological_params),
                'confidence_threshold': tax_class.confidence_threshold,
                'parameter_hash': tax_class.parameter_hash
            }
            for class_id, tax_class in taxonomy.classes.items()
        ]

        return jsonify({
            'status': 'success',
            'n_classes': len(classes_list),
            'classes': classes_list
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@classification_bp.route('/classes/<class_id>', methods=['GET'])
@login_required
def get_class_details(class_id):
    """
    Get detailed information about a specific class.

    Args:
        class_id: Class identifier

    Returns:
        JSON with class details
    """
    if class_id not in taxonomy.classes:
        return jsonify({'error': f'Class {class_id} not found'}), 404

    try:
        tax_class = taxonomy.classes[class_id]

        return jsonify({
            'status': 'success',
            'class': tax_class.to_dict()
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@classification_bp.route('/export', methods=['GET'])
@role_required('admin')
def export_taxonomy():
    """
    Export complete taxonomy to JSON file.

    Returns:
        JSON file download
    """
    try:
        filepath = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            'taxonomy_export.json'
        )

        taxonomy.export_taxonomy(filepath)

        return send_file(
            filepath,
            as_attachment=True,
            download_name='taxonomy_export.json',
            mimetype='application/json'
        )

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@classification_bp.route('/import', methods=['POST'])
@role_required('admin')
def import_taxonomy():
    """
    Import taxonomy from JSON file.

    Body:
        File upload with key 'file'

    Returns:
        JSON confirmation
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    try:
        filepath = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            'taxonomy_import.json'
        )

        file.save(filepath)
        taxonomy.import_taxonomy(filepath)

        return jsonify({
            'status': 'success',
            'message': 'Taxonomy imported successfully',
            'n_classes': len(taxonomy.classes)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@classification_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """
    Get taxonomy statistics.

    Returns:
        JSON with statistics
    """
    try:
        stats = taxonomy.get_statistics()

        return jsonify({
            'status': 'success',
            'statistics': stats
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
