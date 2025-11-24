"""
Flask Application Factory
=========================

Main Flask application with all API blueprints.
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os


def _initialize_mesh_persistence(app):
    """Initialize mesh persistence by reloading meshes from database."""
    try:
        from acs.core.database import get_database
        from acs.web.routes import mesh_processor

        db = get_database()
        stats = mesh_processor.reload_from_database(db)

        print(f"[Mesh Persistence] Reloaded {stats['loaded']} meshes from database")
        if stats['failed'] > 0:
            print(f"[Mesh Persistence] Failed to reload {stats['failed']} meshes")
            for error in stats['errors']:
                print(f"  - {error}")

    except Exception as e:
        print(f"[Mesh Persistence] Error during initialization: {str(e)}")


def create_app(config=None):
    """Create and configure Flask application."""

    app = Flask(__name__)

    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/tmp/acs_uploads')
    app.config['TAXONOMY_DB'] = os.getenv('TAXONOMY_DB', '/tmp/acs_taxonomy.json')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')

    if config:
        app.config.update(config)

    # Enable CORS with specific origins
    CORS(app, resources={
        r"/api/*": {
            "origins": os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5000').split(','),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Access-Token"],
            "supports_credentials": True
        }
    })

    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register API blueprints
    from acs.api.blueprints.auth import auth_bp
    from acs.api.blueprints.mesh import mesh_bp
    from acs.api.blueprints.morphometric import morphometric_bp
    from acs.api.blueprints.classification import classification_bp
    from acs.api.blueprints.agents import agents_bp
    from acs.api.blueprints.savignano import savignano_bp

    app.register_blueprint(auth_bp)  # Auth at /api/auth
    app.register_blueprint(mesh_bp, url_prefix='/api/mesh')
    app.register_blueprint(morphometric_bp, url_prefix='/api/morphometric')
    app.register_blueprint(classification_bp, url_prefix='/api/classification')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(savignano_bp, url_prefix='/api/savignano')

    # Initialize authentication: create default admin if no users exist
    with app.app_context():
        from acs.core.auth import create_default_admin
        admin = create_default_admin()
        if admin:
            print("[Auth] ⚠️  Default admin created:")
            print(f"[Auth]     Username: admin")
            print(f"[Auth]     Password: admin123")
            print(f"[Auth]     ⚠️  CHANGE PASSWORD IMMEDIATELY!")
        else:
            print("[Auth] ✓ Users already exist, skipping default admin creation")

    # Register Web UI blueprint
    from acs.web.routes import web_bp
    app.register_blueprint(web_bp, url_prefix='/web')

    # Initialize mesh persistence: reload meshes from database
    # DISABLED: Slows down startup significantly with large meshes (e.g., 214MB Savignano meshes)
    # Meshes are loaded on-demand when needed instead
    # with app.app_context():
    #     _initialize_mesh_persistence(app)

    # Root endpoint - redirect to web interface
    @app.route('/')
    def index():
        from flask import redirect
        return redirect('/web/')

    # API info endpoint
    @app.route('/api')
    def api_index():
        return jsonify({
            'name': 'Archaeological Classifier System API',
            'version': '0.1.0',
            'web_interface': '/web/',
            'endpoints': {
                'mesh': '/api/mesh',
                'morphometric': '/api/morphometric',
                'classification': '/api/classification',
                'agents': '/api/agents',
                'savignano': '/api/savignano',
                'docs': '/api/docs'
            }
        })

    # API documentation endpoint
    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            'mesh': {
                'POST /api/mesh/upload': 'Upload and process single mesh file',
                'POST /api/mesh/batch': 'Batch process multiple meshes',
                'GET /api/mesh/<artifact_id>': 'Get artifact features',
                'GET /api/mesh/<id1>/distance/<id2>': 'Compute mesh distance'
            },
            'morphometric': {
                'POST /api/morphometric/pca': 'Fit PCA model',
                'POST /api/morphometric/cluster': 'Hierarchical clustering',
                'POST /api/morphometric/dbscan': 'DBSCAN clustering',
                'POST /api/morphometric/similarity': 'Compute similarity matrix',
                'POST /api/morphometric/find-similar': 'Find similar artifacts'
            },
            'classification': {
                'POST /api/classification/define-class': 'Define new taxonomic class',
                'POST /api/classification/classify': 'Classify artifact',
                'POST /api/classification/modify-class': 'Modify class parameters',
                'POST /api/classification/discover': 'Discover new classes',
                'GET /api/classification/classes': 'List all classes',
                'GET /api/classification/classes/<class_id>': 'Get class details',
                'GET /api/classification/export': 'Export taxonomy',
                'GET /api/classification/statistics': 'Get taxonomy statistics'
            },
            'agents': {
                'POST /api/agents/analyze': 'Run multi-agent analysis (placeholder)'
            }
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run Flask development server."""
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
