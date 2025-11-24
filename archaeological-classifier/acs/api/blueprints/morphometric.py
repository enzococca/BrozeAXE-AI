"""
Morphometric Analysis Blueprint
===============================

Endpoints for PCA, clustering, and similarity analysis.
"""

from flask import Blueprint, request, jsonify
from acs.core.auth import login_required, role_required
from acs.core.morphometric import MorphometricAnalyzer

morphometric_bp = Blueprint('morphometric', __name__)

# Global analyzer instance
analyzer = MorphometricAnalyzer()


@morphometric_bp.route('/add-features', methods=['POST'])
@role_required('admin', 'archaeologist')
def add_features():
    """
    Add feature vectors for analysis.

    Body:
        artifacts: List of {artifact_id, features} dicts

    Returns:
        JSON confirmation
    """
    data = request.get_json()
    artifacts = data.get('artifacts', [])

    if not artifacts:
        return jsonify({'error': 'No artifacts provided'}), 400

    try:
        for artifact in artifacts:
            artifact_id = artifact.get('artifact_id') or artifact.get('id')
            features = artifact.get('features', artifact)

            analyzer.add_features(artifact_id, features)

        return jsonify({
            'status': 'success',
            'message': f'Added {len(artifacts)} artifacts',
            'total_artifacts': len(analyzer.features)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@morphometric_bp.route('/pca', methods=['POST'])
@role_required('admin', 'archaeologist')
def fit_pca():
    """
    Fit PCA model on loaded features.

    Body:
        n_components: Number of components (optional)
        explained_variance: Target variance (default 0.95)

    Returns:
        JSON with PCA results
    """
    data = request.get_json() or {}
    n_components = data.get('n_components')
    explained_variance = data.get('explained_variance', 0.95)

    try:
        results = analyzer.fit_pca(
            n_components=n_components,
            explained_variance=explained_variance
        )

        return jsonify({
            'status': 'success',
            'results': results
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@morphometric_bp.route('/cluster', methods=['POST'])
@role_required('admin', 'archaeologist')
def hierarchical_cluster():
    """
    Perform hierarchical clustering.

    Body:
        n_clusters: Number of clusters (optional)
        method: Linkage method (default 'ward')
        distance_threshold: Distance threshold (optional)

    Returns:
        JSON with clustering results
    """
    data = request.get_json() or {}
    n_clusters = data.get('n_clusters')
    method = data.get('method', 'ward')
    distance_threshold = data.get('distance_threshold')

    try:
        results = analyzer.hierarchical_clustering(
            n_clusters=n_clusters,
            method=method,
            distance_threshold=distance_threshold
        )

        return jsonify({
            'status': 'success',
            'results': results
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@morphometric_bp.route('/dbscan', methods=['POST'])
@role_required('admin', 'archaeologist')
def dbscan_cluster():
    """
    Perform DBSCAN clustering.

    Body:
        eps: Maximum distance (default 0.5)
        min_samples: Minimum samples (default 3)

    Returns:
        JSON with clustering results
    """
    data = request.get_json() or {}
    eps = data.get('eps', 0.5)
    min_samples = data.get('min_samples', 3)

    try:
        results = analyzer.dbscan_clustering(
            eps=eps,
            min_samples=min_samples
        )

        return jsonify({
            'status': 'success',
            'results': results
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@morphometric_bp.route('/similarity', methods=['POST'])
@login_required
def similarity_matrix():
    """
    Compute pairwise similarity matrix.

    Body:
        metric: Distance metric (default 'euclidean')

    Returns:
        JSON with similarity matrix
    """
    data = request.get_json() or {}
    metric = data.get('metric', 'euclidean')

    try:
        results = analyzer.compute_similarity_matrix(metric=metric)

        return jsonify({
            'status': 'success',
            'results': results
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@morphometric_bp.route('/find-similar', methods=['POST'])
@login_required
def find_similar():
    """
    Find most similar artifacts to query.

    Body:
        query_id: Query artifact ID
        n: Number of results (default 5)
        metric: Distance metric (default 'euclidean')

    Returns:
        JSON with similar artifacts
    """
    data = request.get_json()
    query_id = data.get('query_id')
    n = data.get('n', 5)
    metric = data.get('metric', 'euclidean')

    if not query_id:
        return jsonify({'error': 'query_id is required'}), 400

    try:
        results = analyzer.find_most_similar(
            query_id=query_id,
            n=n,
            metric=metric
        )

        return jsonify({
            'status': 'success',
            'query_id': query_id,
            'similar_artifacts': [
                {'artifact_id': aid, 'similarity': sim}
                for aid, sim in results
            ]
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@morphometric_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """
    Get feature statistics.

    Returns:
        JSON with statistics
    """
    try:
        stats = analyzer.get_feature_statistics()

        return jsonify({
            'status': 'success',
            'statistics': stats
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
