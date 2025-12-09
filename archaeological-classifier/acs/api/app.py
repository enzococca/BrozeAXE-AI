"""
Flask Application Factory
=========================

Main Flask application with all API blueprints.
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
import atexit
import signal
import sys


# Track if shutdown backup has already been done
_shutdown_backup_done = False


def _perform_shutdown_backup():
    """Backup database to cloud storage before shutdown.

    This is critical for Railway deployments where storage is ephemeral.
    Without this, user accounts and AI cache would be lost on each deploy.
    """
    global _shutdown_backup_done

    # Avoid duplicate backups (can be called by both atexit and signal)
    if _shutdown_backup_done:
        return
    _shutdown_backup_done = True

    storage_backend = os.getenv('STORAGE_BACKEND', 'local')
    if storage_backend == 'local':
        print("[Shutdown] ℹ️  Using local storage, skipping cloud backup")
        return

    try:
        from acs.core.database import backup_database_to_storage

        print("[Shutdown] 🔄 Backing up database before shutdown...")
        result = backup_database_to_storage()

        if result.get('status') == 'success':
            print(f"[Shutdown] ✅ Database backed up: {result.get('backup_filename')}")
        elif result.get('status') == 'error':
            print(f"[Shutdown] ⚠️  Backup failed: {result.get('error')}")
        else:
            print(f"[Shutdown] ℹ️  Backup status: {result.get('status')}")
    except Exception as e:
        print(f"[Shutdown] ⚠️  Backup error: {e}")


def _signal_handler(signum, frame):
    """Handle shutdown signals (SIGTERM, SIGINT) by backing up first."""
    signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
    print(f"[Shutdown] Received {signal_name}, initiating graceful shutdown...")
    _perform_shutdown_backup()
    sys.exit(0)


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

    # Register shutdown hooks for database backup (critical for Railway ephemeral storage)
    storage_backend = os.getenv('STORAGE_BACKEND', 'local')
    if storage_backend != 'local':
        print(f"[Shutdown Hook] Registering database backup handlers for {storage_backend}...")
        # Register atexit handler (called on normal Python exit)
        atexit.register(_perform_shutdown_backup)
        # Register signal handlers (called on SIGTERM from Railway, SIGINT from Ctrl+C)
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
        print("[Shutdown Hook] ✅ Backup handlers registered")

    # Register API blueprints
    from acs.api.blueprints.auth import auth_bp
    from acs.api.blueprints.projects import projects_bp
    from acs.api.blueprints.mesh import mesh_bp
    from acs.api.blueprints.morphometric import morphometric_bp
    from acs.api.blueprints.classification import classification_bp
    from acs.api.blueprints.agents import agents_bp
    from acs.api.blueprints.savignano import savignano_bp
    from acs.api.blueprints.system import system_bp

    app.register_blueprint(auth_bp)  # Auth at /api/auth
    app.register_blueprint(projects_bp)  # Projects at /api/projects
    app.register_blueprint(mesh_bp, url_prefix='/api/mesh')
    app.register_blueprint(morphometric_bp, url_prefix='/api/morphometric')
    app.register_blueprint(classification_bp, url_prefix='/api/classification')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(savignano_bp, url_prefix='/api/savignano')
    app.register_blueprint(system_bp, url_prefix='/api/system')

    # Auto-sync database with cloud storage (Dropbox/Google Drive)
    # Restores from cloud if local DB is empty, or backs up to cloud if local has data
    with app.app_context():
        try:
            storage_backend = os.getenv('STORAGE_BACKEND', 'local')
            db_path = os.getenv('DATABASE_PATH', '/data/acs_artifacts.db')

            print(f"[DB Sync] 📋 Configuration:")
            print(f"[DB Sync]    STORAGE_BACKEND = {storage_backend}")
            print(f"[DB Sync]    DATABASE_PATH = {db_path}")
            print(f"[DB Sync]    DB exists = {os.path.exists(db_path)}")
            if os.path.exists(db_path):
                print(f"[DB Sync]    DB size = {os.path.getsize(db_path)} bytes")

            if storage_backend != 'local':
                from acs.core.database import auto_sync_database
                print(f"[DB Sync] 🔄 Auto-syncing database with {storage_backend}...")
                sync_result = auto_sync_database()

                # Use 'or {}' because values might be explicitly None
                restore_result = sync_result.get('restore') or {}
                backup_result = sync_result.get('backup') or {}

                print(f"[DB Sync] 📊 Sync result: {sync_result}")

                if restore_result.get('status') == 'success':
                    print(f"[DB Sync] ✅ Restored from cloud: {restore_result.get('restored_from')}")
                elif backup_result.get('status') == 'success':
                    print(f"[DB Sync] ✅ Backed up to cloud: {backup_result.get('backup_filename')}")
                elif restore_result.get('status') == 'skipped':
                    print(f"[DB Sync] ℹ️  Skipped: {restore_result.get('reason')}")
                    if restore_result.get('error'):
                        print(f"[DB Sync]    Error detail: {restore_result.get('error')}")
                elif sync_result.get('error'):
                    print(f"[DB Sync] ⚠️  Error: {sync_result.get('error')}")
            else:
                print(f"[DB Sync] ℹ️  Using local storage, no cloud sync")
        except Exception as e:
            import traceback
            print(f"[DB Sync] ⚠️  Auto-sync failed: {e}")
            traceback.print_exc()

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


def run_server(host='0.0.0.0', port=5001, debug=False):
    """Run Flask development server."""
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
