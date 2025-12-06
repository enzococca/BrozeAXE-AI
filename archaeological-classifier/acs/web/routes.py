"""
Web Interface Routes
===================

Blueprint for web-based user interface.
"""

from flask import Blueprint, render_template, request, jsonify, session, current_app, make_response, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
import io
from datetime import datetime
import numpy as np

from acs.core.mesh_processor import MeshProcessor
from acs.core.morphometric import MorphometricAnalyzer
from acs.core.taxonomy import FormalTaxonomySystem
from acs.core.database import get_database

web_bp = Blueprint('web', __name__,
                   template_folder='templates',
                   static_folder='static')


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

# Global instances (in production, use proper state management)
mesh_processor = MeshProcessor()
morphometric_analyzer = MorphometricAnalyzer()
taxonomy_system = FormalTaxonomySystem()


def ensure_mesh_loaded(artifact_id: str) -> bool:
    """
    Ensure a mesh is loaded into memory, downloading from storage if needed.

    This enables lazy loading of meshes after a deploy - artifacts are stored
    in the database but meshes need to be downloaded from cloud storage.

    Returns True if mesh is loaded successfully, False otherwise.
    """
    # Already in memory
    if artifact_id in mesh_processor.meshes:
        return True

    try:
        from acs.core.database import get_database
        from acs.core.storage import get_default_storage
        import tempfile
        import logging

        db = get_database()
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            logging.warning(f"Artifact {artifact_id} not found in database")
            return False

        mesh_path = artifact.get('mesh_path')
        if not mesh_path:
            logging.warning(f"No mesh_path for artifact {artifact_id}")
            return False

        # Check if local file exists
        if os.path.isabs(mesh_path) and os.path.exists(mesh_path):
            # Local file - load directly
            mesh_processor.load_mesh(mesh_path, artifact_id)
            logging.info(f"Loaded mesh {artifact_id} from local path")
            return True

        # Remote path - need to download from storage
        try:
            storage = get_default_storage()

            # Create cache directory
            cache_folder = os.path.join(tempfile.gettempdir(), 'acs_mesh_cache')
            os.makedirs(cache_folder, exist_ok=True)

            # Download to cache
            cache_path = os.path.join(cache_folder, f'{artifact_id}.obj')

            if not os.path.exists(cache_path):
                logging.info(f"Downloading mesh {artifact_id} from storage: {mesh_path}")
                storage.download_file(mesh_path, cache_path)

            # Load mesh
            mesh_processor.load_mesh(cache_path, artifact_id)
            logging.info(f"Loaded mesh {artifact_id} from storage cache")
            return True

        except Exception as e:
            logging.error(f"Failed to download mesh {artifact_id}: {e}")
            return False

    except Exception as e:
        import logging
        logging.error(f"Error loading mesh {artifact_id}: {e}")
        return False


def init_default_taxonomy_classes():
    """Initialize default taxonomy classes for Bronze Age axes if none exist."""
    if len(taxonomy_system.classes) > 0:
        return  # Already initialized

    from acs.core.taxonomy import ClassificationParameter, TaxonomicClass
    from datetime import datetime

    # Socketed Axe - Typical Bronze Age socketed axe
    socketed_axe = TaxonomicClass(
        class_id="TYPE_SOCKETED_AXE",
        name="Socketed Axe",
        description="Typical Bronze Age socketed axe with standard proportions",
        morphometric_params={
            'length': ClassificationParameter(
                name='length', value=165.0, min_threshold=140.0, max_threshold=190.0,
                weight=1.5, measurement_unit='mm', tolerance=15.0
            ),
            'width': ClassificationParameter(
                name='width', value=52.0, min_threshold=45.0, max_threshold=60.0,
                weight=1.2, measurement_unit='mm', tolerance=5.0
            ),
            'thickness': ClassificationParameter(
                name='thickness', value=15.0, min_threshold=10.0, max_threshold=20.0,
                weight=1.0, measurement_unit='mm', tolerance=3.0
            ),
            'length_width_ratio': ClassificationParameter(
                name='length_width_ratio', value=3.0, min_threshold=2.5, max_threshold=3.8,
                weight=1.3, measurement_unit='ratio', tolerance=0.4
            ),
        },
        technological_params={},
        optional_features={},
        confidence_threshold=0.70,
        created_by="system",
        validated_samples=[]
    )

    # Flanged Axe - Bronze Age flanged axe
    flanged_axe = TaxonomicClass(
        class_id="TYPE_FLANGED_AXE",
        name="Flanged Axe",
        description="Bronze Age flanged axe with pronounced flanges",
        morphometric_params={
            'length': ClassificationParameter(
                name='length', value=145.0, min_threshold=120.0, max_threshold=170.0,
                weight=1.5, measurement_unit='mm', tolerance=15.0
            ),
            'width': ClassificationParameter(
                name='width', value=48.0, min_threshold=40.0, max_threshold=56.0,
                weight=1.2, measurement_unit='mm', tolerance=5.0
            ),
            'thickness': ClassificationParameter(
                name='thickness', value=12.0, min_threshold=8.0, max_threshold=18.0,
                weight=1.0, measurement_unit='mm', tolerance=3.0
            ),
            'length_width_ratio': ClassificationParameter(
                name='length_width_ratio', value=2.8, min_threshold=2.3, max_threshold=3.5,
                weight=1.3, measurement_unit='ratio', tolerance=0.4
            ),
        },
        technological_params={},
        optional_features={},
        confidence_threshold=0.70,
        created_by="system",
        validated_samples=[]
    )

    # Palstave - Bronze Age palstave type
    palstave = TaxonomicClass(
        class_id="TYPE_PALSTAVE",
        name="Palstave",
        description="Bronze Age palstave with stop-ridge",
        morphometric_params={
            'length': ClassificationParameter(
                name='length', value=155.0, min_threshold=130.0, max_threshold=180.0,
                weight=1.5, measurement_unit='mm', tolerance=15.0
            ),
            'width': ClassificationParameter(
                name='width', value=50.0, min_threshold=42.0, max_threshold=58.0,
                weight=1.2, measurement_unit='mm', tolerance=5.0
            ),
            'thickness': ClassificationParameter(
                name='thickness', value=13.0, min_threshold=9.0, max_threshold=17.0,
                weight=1.0, measurement_unit='mm', tolerance=3.0
            ),
            'length_width_ratio': ClassificationParameter(
                name='length_width_ratio', value=3.1, min_threshold=2.6, max_threshold=3.7,
                weight=1.3, measurement_unit='ratio', tolerance=0.4
            ),
        },
        technological_params={},
        optional_features={},
        confidence_threshold=0.70,
        created_by="system",
        validated_samples=[]
    )

    # Register classes
    taxonomy_system.classes[socketed_axe.class_id] = socketed_axe
    taxonomy_system.classes[flanged_axe.class_id] = flanged_axe
    taxonomy_system.classes[palstave.class_id] = palstave

    print(f"✓ Initialized {len(taxonomy_system.classes)} default taxonomy classes")


# Initialize default classes on startup
init_default_taxonomy_classes()


@web_bp.route('/login')
def login_page():
    """Login page."""
    return render_template('login.html')


@web_bp.route('/dashboard')
def dashboard_page():
    """Dashboard page (requires authentication via JavaScript)."""
    return render_template('dashboard.html')


@web_bp.route('/data-explorer')
def data_explorer_page():
    """Data Explorer - Navigate artifacts, features, training data."""
    return render_template('data_explorer.html')


@web_bp.route('/api/statistics')
def get_statistics():
    """Get statistics for dashboard (protected by JavaScript token check)."""
    try:
        db = get_database()
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'total_artifacts': 0,
            'total_classifications': 0,
            'validated_classifications': 0,
            'training_samples': 0
        })


@web_bp.route('/')
def index():
    """Main dashboard - redirect to new dashboard if logged in."""
    # Check if user might be logged in (via JavaScript check)
    return redirect(url_for('web.dashboard_page'))


@web_bp.route('/test')
def test_page():
    """Test page for CSS debugging."""
    return render_template('test_minimal.html')


@web_bp.route('/upload')
def upload_page():
    """Mesh upload page."""
    return render_template('upload.html')


def background_upload_to_storage(artifact_id, temp_dir, filename, mtl_filename, texture_filenames, mesh_units, enable_savignano, weight):
    """Background task to upload OBJ to cloud storage and run Savignano analysis.

    Note: MTL and texture files are uploaded synchronously in the main upload function
    so they're available immediately for the 3D viewer. This function only handles
    the large OBJ file upload and Savignano analysis.
    """
    import logging
    import shutil

    try:
        from acs.core.storage import get_default_storage
        from acs.core.database import get_database, backup_database_to_storage

        filepath = os.path.join(temp_dir, filename)

        # Upload OBJ to storage (MTL/textures already uploaded synchronously)
        try:
            storage = get_default_storage()
            remote_path = f"meshes/{artifact_id}/{filename}"

            # Upload OBJ (the large file)
            storage.upload_file(filepath, remote_path)
            logging.info(f"✅ [BG] Uploaded {filename} to storage")

            # Update database with remote OBJ path (keep existing MTL/texture paths)
            db = get_database()
            artifact = db.get_artifact(artifact_id)
            if artifact:
                import json
                metadata = json.loads(artifact.get('metadata', '{}')) if artifact.get('metadata') else {}
                metadata['storage_upload_complete'] = True

                # Update mesh_path to remote path, keep existing MTL/texture paths
                db.add_artifact(
                    artifact_id=artifact_id,
                    mesh_path=remote_path,
                    n_vertices=artifact.get('n_vertices', 0),
                    n_faces=artifact.get('n_faces', 0),
                    is_watertight=artifact.get('is_watertight', False),
                    metadata=metadata,
                    project_id=artifact.get('project_id')
                )
                logging.info(f"✅ [BG] Updated database for {artifact_id}")

        except Exception as e:
            logging.error(f"[BG] Storage upload failed for {artifact_id}: {e}")

        # Run Savignano analysis in background
        if enable_savignano:
            try:
                from acs.savignano.morphometric_extractor import extract_savignano_features

                savignano_features = extract_savignano_features(
                    mesh_path=filepath,
                    artifact_id=artifact_id,
                    weight=weight,
                    inventory_number=artifact_id,
                    mesh_units=mesh_units
                )

                # Save Savignano features to database
                db = get_database()
                db.add_features(artifact_id, {'savignano': savignano_features})
                logging.info(f"✅ [BG] Savignano analysis complete for {artifact_id}")

            except Exception as e:
                logging.error(f"[BG] Savignano analysis failed for {artifact_id}: {e}")

        # Backup database
        try:
            storage_backend = os.getenv('STORAGE_BACKEND', 'local')
            if storage_backend != 'local':
                backup_database_to_storage()
                logging.info(f"✅ [BG] Database backup complete")
        except Exception as e:
            logging.error(f"[BG] Database backup failed: {e}")

    except Exception as e:
        logging.error(f"[BG] Background upload failed for {artifact_id}: {e}")

    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


@web_bp.route('/upload-mesh', methods=['POST'])
def upload_mesh():
    """Handle mesh file upload with database persistence and optional Savignano analysis."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)

    # Save to PERSISTENT temp location (not deleted on request end)
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix='acs_upload_')
    temp_filepath = os.path.join(temp_dir, filename)
    file.save(temp_filepath)

    # Handle MTL file if provided
    mtl_filename = None
    if 'mtl_file' in request.files:
        mtl_file = request.files['mtl_file']
        if mtl_file.filename != '':
            mtl_filename = secure_filename(mtl_file.filename)
            mtl_filepath = os.path.join(temp_dir, mtl_filename)
            mtl_file.save(mtl_filepath)

    # Handle texture files if provided (can be multiple)
    texture_filenames = []
    if 'texture_files' in request.files:
        texture_files = request.files.getlist('texture_files')
        for tex_file in texture_files:
            if tex_file.filename != '':
                tex_filename = secure_filename(tex_file.filename)
                tex_filepath = os.path.join(temp_dir, tex_filename)
                tex_file.save(tex_filepath)
                texture_filenames.append(tex_filename)

    # We'll upload to storage after processing
    filepath = temp_filepath

    # Process mesh
    try:
        from acs.core.database import get_database
        from acs.savignano.feature_detector import should_extract_savignano_features

        artifact_id = request.form.get('artifact_id', filename.rsplit('.', 1)[0])
        project_id = request.form.get('project_id') or None  # None if not specified

        # Get category and description for auto-detection
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        material = request.form.get('material', '')

        # Mesh units for scale conversion (mm, cm, m, in)
        mesh_units = request.form.get('mesh_units', 'cm')  # Default to cm for archaeological meshes

        # Auto-detect Savignano analysis (can be overridden by explicit parameter)
        enable_savignano_explicit = request.form.get('enable_savignano')
        if enable_savignano_explicit is not None:
            # User explicitly enabled/disabled - respect their choice
            enable_savignano = enable_savignano_explicit == 'true'
        else:
            # Auto-detect based on artifact characteristics
            enable_savignano = should_extract_savignano_features(
                artifact_id=artifact_id,
                category=category,
                description=description,
                material=material,
                has_3d_mesh=True,
                mesh_path=filepath
            )

        features = mesh_processor.load_mesh(filepath, artifact_id)

        # Add to morphometric analyzer
        morphometric_analyzer.add_features(features['id'], features)

        # Get weight for Savignano (need to extract before background thread)
        weight = None
        if enable_savignano:
            weight_value = request.form.get('weight')
            if weight_value:
                weight = float(weight_value)

            # Or from weights file
            if 'weights_file' in request.files and not weight:
                weights_file = request.files['weights_file']
                if weights_file.filename != '':
                    from acs.utils.weight_importer import import_weights_auto
                    temp_weights_path = os.path.join(temp_dir, secure_filename(weights_file.filename))
                    weights_file.save(temp_weights_path)
                    try:
                        weights_dict = import_weights_auto(temp_weights_path)
                        weight = weights_dict.get(artifact_id) or weights_dict.get(filename.rsplit('.', 1)[0])
                    except:
                        pass

        import logging

        # Upload MTL and textures IMMEDIATELY (they're small) so viewer can use them right away
        stored_mtl_path = None
        stored_texture_paths = []
        storage_backend = os.getenv('STORAGE_BACKEND', 'local')

        if storage_backend != 'local' and (mtl_filename or texture_filenames):
            try:
                from acs.core.storage import get_default_storage
                storage = get_default_storage()

                # Upload MTL file immediately
                if mtl_filename:
                    mtl_remote_path = f"meshes/{artifact_id}/{mtl_filename}"
                    mtl_local = os.path.join(temp_dir, mtl_filename)
                    storage.upload_file(mtl_local, mtl_remote_path)
                    stored_mtl_path = mtl_remote_path
                    logging.info(f"✅ Uploaded MTL {mtl_filename} to storage")

                # Upload texture files immediately
                for tex_filename in texture_filenames:
                    tex_remote_path = f"meshes/{artifact_id}/{tex_filename}"
                    tex_local = os.path.join(temp_dir, tex_filename)
                    storage.upload_file(tex_local, tex_remote_path)
                    stored_texture_paths.append(tex_remote_path)
                    logging.info(f"✅ Uploaded texture {tex_filename} to storage")

            except Exception as e:
                logging.error(f"Failed to upload textures for {artifact_id}: {e}")

        # Save to database - MTL/texture paths set NOW, OBJ path updated by background
        db = get_database()
        mesh = mesh_processor.meshes[artifact_id]
        db.add_artifact(
            artifact_id=artifact_id,
            mesh_path=filepath,  # Temp path - will be updated by background upload
            n_vertices=len(mesh.vertices),
            n_faces=len(mesh.faces),
            is_watertight=mesh.is_watertight,
            metadata={
                'original_filename': file.filename,
                'savignano_enabled': enable_savignano,
                'savignano_auto_detected': enable_savignano_explicit is None,
                'category': category,
                'description': description,
                'material': material,
                'mesh_units': mesh_units,
                'storage_backend': storage_backend,
                'mtl_path': stored_mtl_path,  # SET NOW - textures available immediately
                'texture_paths': stored_texture_paths,  # SET NOW
                'has_textures': bool(stored_mtl_path or stored_texture_paths),
                'storage_upload_complete': False  # OBJ still uploading in background
            },
            project_id=project_id
        )
        db.add_features(artifact_id, features)

        # Start background upload for large OBJ file and Savignano analysis
        if storage_backend != 'local':
            import threading
            upload_thread = threading.Thread(
                target=background_upload_to_storage,
                args=(artifact_id, temp_dir, filename, mtl_filename, texture_filenames, mesh_units, enable_savignano, weight),
                daemon=True
            )
            upload_thread.start()
            logging.info(f"🔄 Started background upload for {artifact_id}")
        else:
            # Local storage - no background needed, just clean up
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

        # Return FAST - processing continues in background
        response_data = {
            'status': 'success',
            'artifact_id': features['id'],
            'features': convert_numpy_types(features),
            'persisted': True,
            'savignano_extracted': False,  # Will happen in background
            'savignano_auto_detected': enable_savignano_explicit is None and enable_savignano,
            'storage_backend': storage_backend,
            'background_processing': storage_backend != 'local',
            'message': 'Upload complete. Cloud sync and analysis running in background.' if storage_backend != 'local' else None
        }
        return jsonify(response_data)
    except Exception as e:
        import logging
        logging.error(f"Upload error for {filename}: {e}", exc_info=True)

        # Clean up temporary directory on error
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

        return jsonify({'error': str(e)}), 500


@web_bp.route('/morphometric')
def morphometric_page():
    """Morphometric analysis page."""
    return render_template('morphometric.html')


@web_bp.route('/run-pca', methods=['POST'])
def run_pca():
    """Run PCA analysis."""
    try:
        n_components = request.json.get('n_components')
        explained_variance = request.json.get('explained_variance', 0.95)

        results = morphometric_analyzer.fit_pca(
            n_components=n_components,
            explained_variance=explained_variance
        )

        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/run-clustering', methods=['POST'])
def run_clustering():
    """Run clustering analysis."""
    try:
        method = request.json.get('method', 'hierarchical')
        n_clusters = request.json.get('n_clusters')

        if method == 'hierarchical':
            results = morphometric_analyzer.hierarchical_clustering(
                n_clusters=n_clusters,
                method=request.json.get('linkage', 'ward')
            )
        elif method == 'dbscan':
            results = morphometric_analyzer.dbscan_clustering(
                eps=request.json.get('eps', 0.5),
                min_samples=request.json.get('min_samples', 3)
            )
        else:
            return jsonify({'error': 'Unknown method'}), 400

        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/taxonomy')
def taxonomy_page():
    """Taxonomy management page."""
    classes_list = [
        {
            'class_id': cid,
            'name': tc.name,
            'description': tc.description,
            'n_parameters': len(tc.morphometric_params) + len(tc.technological_params),
            'confidence_threshold': tc.confidence_threshold,
            'n_samples': len(tc.validated_samples),
            'created_date': tc.created_date.isoformat() if hasattr(tc.created_date, 'isoformat') else str(tc.created_date)
        }
        for cid, tc in taxonomy_system.classes.items()
    ]
    return render_template('taxonomy.html', classes=classes_list)


@web_bp.route('/define-class', methods=['POST'])
def define_class():
    """Define new taxonomic class."""
    try:
        data = request.json
        class_name = data.get('class_name')
        reference_ids = data.get('reference_ids', [])

        # Get features for reference objects
        reference_objects = []
        for aid in reference_ids:
            if aid in mesh_processor.meshes:
                features = mesh_processor._extract_features(
                    mesh_processor.meshes[aid],
                    aid
                )
                reference_objects.append(features)

        if len(reference_objects) < 2:
            return jsonify({'error': 'Need at least 2 reference objects'}), 400

        # Define class
        new_class = taxonomy_system.define_class_from_reference_group(
            class_name=class_name,
            reference_objects=reference_objects,
            parameter_weights=data.get('parameter_weights'),
            tolerance_factor=data.get('tolerance_factor', 0.15)
        )

        return jsonify({
            'status': 'success',
            'class': new_class.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/classify-artifact', methods=['POST'])
def classify_artifact():
    """Classify an artifact."""
    try:
        data = request.json
        artifact_id = data.get('artifact_id')

        # Lazy load mesh from storage if not in memory
        if not ensure_mesh_loaded(artifact_id):
            return jsonify({'error': 'Artifact not found'}), 404

        # Get features
        features = mesh_processor._extract_features(
            mesh_processor.meshes[artifact_id],
            artifact_id
        )

        # Classify
        results = taxonomy_system.classify_object(
            obj_features=features,
            return_all_scores=True
        )

        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/artifacts')
def artifacts_page():
    """Artifacts browser page."""
    artifacts_list = []
    for aid, mesh in mesh_processor.meshes.items():
        features = mesh_processor._extract_features(mesh, aid)

        # Check if artifact is classified
        classified = False
        class_name = None
        for tc_name, tc in taxonomy_system.classes.items():
            if aid in tc.validated_samples:
                classified = True
                class_name = tc_name
                break

        artifacts_list.append({
            'id': aid,
            'volume': features.get('volume'),
            'length': features.get('length'),
            'width': features.get('width'),
            'n_vertices': features.get('n_vertices'),
            'n_faces': features.get('n_faces'),
            'classified': classified,
            'class_name': class_name
        })

    return render_template('artifacts.html', artifacts=artifacts_list)


@web_bp.route('/artifact/<artifact_id>')
def artifact_detail(artifact_id):
    """Artifact detail page with technological analysis."""
    # Lazy load mesh from storage if not in memory
    if not ensure_mesh_loaded(artifact_id):
        return "Artifact not found", 404

    mesh = mesh_processor.meshes[artifact_id]
    features = mesh_processor._extract_features(mesh, artifact_id)

    # Get technological analysis
    tech_features = None
    tech_report = None
    ai_interpretation = None

    try:
        from acs.core.technological_analyzer import get_technological_analyzer
        from acs.core.ai_assistant import get_ai_assistant

        tech_analyzer = get_technological_analyzer()
        tech_features_raw = tech_analyzer.analyze_technology(mesh, artifact_id)
        tech_report = tech_analyzer.generate_technical_report(tech_features_raw, artifact_id)

        # Create flattened view for template display
        tech_features = {
            # Production method
            'production_method': tech_features_raw.get('production_method', {}).get('PRIMARY_METHOD', 'UNKNOWN'),
            'production_confidence': tech_features_raw.get('production_method', {}).get('CONFIDENCE', 0.0),
            'production_description': tech_features_raw.get('production_method', {}).get('TECHNIQUE_DESCRIPTION', ''),

            # Hammering
            'hammering_detected': tech_features_raw.get('hammering', {}).get('detected', False),
            'hammering_intensity': tech_features_raw.get('hammering', {}).get('intensity', 0.0),

            # Casting
            'casting_detected': tech_features_raw.get('casting', {}).get('likely_cast', False),
            'casting_confidence': tech_features_raw.get('casting', {}).get('confidence', 0.0),

            # Wear
            'wear_severity': tech_features_raw.get('wear', {}).get('severity', 'NONE'),
            'edge_rounding': tech_features_raw.get('wear', {}).get('edge_rounding', 0.0),

            # Edge condition
            'edge_sharpness': tech_features_raw.get('edge_analysis', {}).get('condition', 'UNKNOWN'),
            'edge_angle': tech_features_raw.get('edge_analysis', {}).get('angle_degrees', 0.0),
            'edge_usable': tech_features_raw.get('edge_analysis', {}).get('usable', False),

            # Surface
            'surface_smoothness': tech_features_raw.get('surface_treatment', {}).get('smoothness', 0.0),
            'surface_polished': tech_features_raw.get('surface_treatment', {}).get('polished', False),

            # Keep raw data for detailed view
            '_raw': tech_features_raw
        }

        # Get AI interpretation
        try:
            ai = get_ai_assistant()
            print(f"[DEBUG] AI assistant: {ai}")
            if ai:
                print(f"[DEBUG] Calling AI interpretation for {artifact_id}")
                ai_interpretation = ai.interpret_technological_analysis(
                    artifact_id,
                    tech_features_raw,
                    tech_report
                )
                print(f"[DEBUG] AI interpretation result: {ai_interpretation is not None}")
                if ai_interpretation:
                    print(f"[DEBUG] AI interpretation keys: {ai_interpretation.keys()}")
        except Exception as e:
            print(f"[ERROR] AI interpretation failed: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Technological analysis failed: {e}")

    return render_template('artifact_detail.html',
                          artifact_id=artifact_id,
                          features=features,
                          tech_features=tech_features,
                          tech_report=tech_report,
                          ai_interpretation=ai_interpretation)


@web_bp.route('/export-data', methods=['POST'])
def export_data():
    """Export current data."""
    try:
        export_type = request.json.get('type', 'taxonomy')

        export_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'exports')
        os.makedirs(export_folder, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if export_type == 'taxonomy':
            filepath = os.path.join(export_folder, f'taxonomy_{timestamp}.json')
            taxonomy_system.export_taxonomy(filepath)
        elif export_type == 'features':
            filepath = os.path.join(export_folder, f'features_{timestamp}.json')
            mesh_processor.export_features(filepath, format='json')
        else:
            return jsonify({'error': 'Unknown export type'}), 400

        return jsonify({
            'status': 'success',
            'filepath': filepath,
            'filename': os.path.basename(filepath)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/statistics')
def statistics_api():
    """Get current statistics."""
    try:
        stats = {
            'meshes': {
                'loaded': len(mesh_processor.meshes),
                'artifacts': list(mesh_processor.meshes.keys())
            },
            'morphometric': {
                'features': len(morphometric_analyzer.features),
                'statistics': morphometric_analyzer.get_feature_statistics()
            },
            'taxonomy': taxonomy_system.get_statistics()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/viewer')
def viewer_page():
    """3D viewer page."""
    from acs.core.database import get_database

    # Get artifacts from database (persisted) instead of in-memory mesh_processor
    db = get_database()
    db_artifacts = db.get_all_artifacts()
    artifacts = [a['artifact_id'] for a in db_artifacts]

    # Also include any in-memory artifacts not yet in DB
    for aid in mesh_processor.meshes.keys():
        if aid not in artifacts:
            artifacts.append(aid)

    return render_template('viewer3d.html', artifacts=artifacts)


@web_bp.route('/mesh-file/<artifact_id>')
def serve_mesh_file(artifact_id):
    """Serve mesh file for 3D viewer, downloading from storage if needed."""
    try:
        from acs.core.database import get_database
        from acs.core.storage import get_default_storage
        import shutil

        db = get_database()
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({'error': 'Artifact not found'}), 404

        mesh_path = artifact.get('mesh_path')
        if not mesh_path:
            return jsonify({'error': 'Mesh file path not found'}), 404

        # Check if this is a remote storage path (not an absolute local path)
        if not os.path.isabs(mesh_path) or not os.path.exists(mesh_path):
            # Remote storage path - download to cache
            storage = get_default_storage()
            cache_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'mesh_cache')
            os.makedirs(cache_folder, exist_ok=True)

            cache_path = os.path.join(cache_folder, f'{artifact_id}.obj')

            # Download if not cached
            if not os.path.exists(cache_path):
                import logging
                logging.info(f"Downloading {mesh_path} from storage to cache")
                storage.download_file(mesh_path, cache_path)

            serve_path = cache_path
        else:
            # Local path - serve directly
            serve_path = mesh_path

        # Serve the file
        response = send_file(serve_path, mimetype='text/plain')
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
        return response

    except Exception as e:
        import logging
        logging.error(f"Error serving mesh file {artifact_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@web_bp.route('/artifact-metadata/<artifact_id>')
def get_artifact_metadata(artifact_id):
    """Get artifact metadata including mesh_units for 3D viewer scaling."""
    try:
        from acs.core.database import get_database
        import json

        db = get_database()
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({'error': 'Artifact not found'}), 404

        # Parse metadata JSON
        metadata = {}
        if artifact.get('metadata'):
            try:
                metadata = json.loads(artifact['metadata']) if isinstance(artifact['metadata'], str) else artifact['metadata']
            except:
                metadata = {}

        # Return relevant metadata for 3D viewer
        return jsonify({
            'artifact_id': artifact_id,
            'mesh_units': metadata.get('mesh_units', 'cm'),  # Default to cm
            'n_vertices': artifact.get('n_vertices'),
            'n_faces': artifact.get('n_faces'),
            'is_watertight': artifact.get('is_watertight'),
            'category': metadata.get('category', ''),
            'description': metadata.get('description', ''),
            'material': metadata.get('material', ''),
            'savignano_enabled': metadata.get('savignano_enabled', False),
            'has_textures': metadata.get('has_textures', False),
            'mtl_path': metadata.get('mtl_path'),
            'texture_paths': metadata.get('texture_paths', [])
        })

    except Exception as e:
        import logging
        logging.error(f"Error getting artifact metadata {artifact_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@web_bp.route('/mtl-file/<artifact_id>')
def serve_mtl_file(artifact_id):
    """Serve MTL material file for 3D viewer."""
    try:
        from acs.core.database import get_database
        from acs.core.storage import get_default_storage
        import json

        db = get_database()
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({'error': 'Artifact not found'}), 404

        # Parse metadata
        metadata = {}
        if artifact.get('metadata'):
            try:
                metadata = json.loads(artifact['metadata']) if isinstance(artifact['metadata'], str) else artifact['metadata']
            except:
                metadata = {}

        mtl_path = metadata.get('mtl_path')
        if not mtl_path:
            return jsonify({'error': 'No MTL file for this artifact'}), 404

        # Check if remote or local path
        if not os.path.isabs(mtl_path) or not os.path.exists(mtl_path):
            # Remote storage - download to cache
            storage = get_default_storage()
            cache_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'mesh_cache')
            os.makedirs(cache_folder, exist_ok=True)

            mtl_filename = os.path.basename(mtl_path)
            cache_path = os.path.join(cache_folder, f'{artifact_id}_{mtl_filename}')

            if not os.path.exists(cache_path):
                import logging
                logging.info(f"Downloading {mtl_path} from storage to cache")
                storage.download_file(mtl_path, cache_path)

            serve_path = cache_path
        else:
            serve_path = mtl_path

        response = send_file(serve_path, mimetype='text/plain')
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response

    except Exception as e:
        import logging
        logging.error(f"Error serving MTL file {artifact_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@web_bp.route('/texture-file/<artifact_id>/<filename>')
def serve_texture_file(artifact_id, filename):
    """Serve texture file (PNG/JPG) for 3D viewer."""
    try:
        from acs.core.database import get_database
        from acs.core.storage import get_default_storage
        import json

        db = get_database()
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({'error': 'Artifact not found'}), 404

        # Parse metadata
        metadata = {}
        if artifact.get('metadata'):
            try:
                metadata = json.loads(artifact['metadata']) if isinstance(artifact['metadata'], str) else artifact['metadata']
            except:
                metadata = {}

        texture_paths = metadata.get('texture_paths', [])

        # Find the requested texture
        texture_path = None
        for tp in texture_paths:
            if os.path.basename(tp) == filename:
                texture_path = tp
                break

        if not texture_path:
            # Try constructing the path
            texture_path = f"meshes/{artifact_id}/{filename}"

        # Check if remote or local path
        if not os.path.isabs(texture_path) or not os.path.exists(texture_path):
            # Remote storage - download to cache
            storage = get_default_storage()
            cache_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'mesh_cache')
            os.makedirs(cache_folder, exist_ok=True)

            cache_path = os.path.join(cache_folder, f'{artifact_id}_{filename}')

            if not os.path.exists(cache_path):
                import logging
                logging.info(f"Downloading {texture_path} from storage to cache")
                storage.download_file(texture_path, cache_path)

            serve_path = cache_path
        else:
            serve_path = texture_path

        # Determine mimetype
        ext = filename.lower().split('.')[-1]
        mimetypes = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'tga': 'image/x-tga',
            'bmp': 'image/bmp'
        }
        mimetype = mimetypes.get(ext, 'application/octet-stream')

        response = send_file(serve_path, mimetype=mimetype)
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response

    except Exception as e:
        import logging
        logging.error(f"Error serving texture file {artifact_id}/{filename}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@web_bp.route('/compare-artifacts', methods=['POST'])
def compare_artifacts():
    """Compare two artifacts with morphometric and stylistic analysis."""
    try:
        from acs.core.stylistic_analyzer import get_stylistic_analyzer

        data = request.json
        artifact1 = data.get('artifact1')
        artifact2 = data.get('artifact2')

        # Lazy load meshes from storage if not in memory
        if not ensure_mesh_loaded(artifact1) or not ensure_mesh_loaded(artifact2):
            return jsonify({'error': 'One or both artifacts not found'}), 404

        # Get morphometric features
        features1 = mesh_processor._extract_features(mesh_processor.meshes[artifact1], artifact1)
        features2 = mesh_processor._extract_features(mesh_processor.meshes[artifact2], artifact2)

        # Analyze stylistic features
        stylistic = get_stylistic_analyzer()
        style1 = stylistic.analyze_style(mesh_processor.meshes[artifact1], artifact1, features1)
        style2 = stylistic.analyze_style(mesh_processor.meshes[artifact2], artifact2, features2)

        # Make sure styles are in the database (analyze_style should do this, but ensure it)
        if artifact1 not in stylistic.style_database:
            stylistic.style_database[artifact1] = style1
        if artifact2 not in stylistic.style_database:
            stylistic.style_database[artifact2] = style2

        # Compute morphometric similarity
        import numpy as np
        feature_keys = ['volume', 'surface_area', 'length', 'width', 'height', 'compactness']

        feature_differences = {}
        morphometric_similarity = 0
        valid_features = 0

        for key in feature_keys:
            if key in features1 and key in features2:
                val1 = features1[key]
                val2 = features2[key]
                max_val = max(abs(val1), abs(val2))

                if max_val > 1e-10:  # Avoid division by zero
                    diff = abs(val1 - val2) / max_val
                    similarity = max(0, min(1, 1 - diff))  # Clamp to [0, 1]

                    feature_differences[key] = {
                        'artifact1': float(val1),
                        'artifact2': float(val2),
                        'difference': float(diff),
                        'similarity': float(similarity)
                    }
                    morphometric_similarity += similarity
                    valid_features += 1

        if valid_features > 0:
            morphometric_similarity /= valid_features
        else:
            morphometric_similarity = 0.0

        # Compute stylistic similarity
        stylistic_similarities = stylistic.compare_styles(artifact1, artifact2)

        # DEBUG LOGGING
        print(f"\n=== COMPARISON DEBUG ===")
        print(f"Morphometric similarity BEFORE nan_to_num: {morphometric_similarity}")
        print(f"Stylistic similarities: {stylistic_similarities}")
        print(f"Feature differences: {feature_differences}")

        # Combined overall similarity (60% morphometric, 40% stylistic)
        if 'overall_style_similarity' in stylistic_similarities:
            style_sim = stylistic_similarities['overall_style_similarity']
            print(f"Style similarity value: {style_sim}, is NaN: {np.isnan(style_sim) if isinstance(style_sim, (int, float)) else 'not a number'}")
            # Handle NaN in stylistic similarity
            if np.isnan(style_sim) or style_sim is None:
                overall_similarity = morphometric_similarity
            else:
                overall_similarity = (0.6 * morphometric_similarity + 0.4 * style_sim)
        else:
            overall_similarity = morphometric_similarity
            print(f"No overall_style_similarity found in stylistic_similarities")

        print(f"Overall similarity BEFORE nan_to_num: {overall_similarity}")

        # Ensure no NaN in final result - MA NON CONVERTIRE VALORI VALIDI A 0!
        if np.isnan(overall_similarity):
            overall_similarity = 0.0
        if np.isnan(morphometric_similarity):
            morphometric_similarity = 0.0

        overall_similarity = float(overall_similarity)
        morphometric_similarity = float(morphometric_similarity)

        print(f"Final overall similarity: {overall_similarity}")
        print(f"Final morphometric similarity: {morphometric_similarity}")
        print(f"=== END DEBUG ===\n")

        return jsonify({
            'status': 'success',
            'morphometric_similarity': float(morphometric_similarity),
            'stylistic_similarities': stylistic_similarities,
            'overall_similarity': float(overall_similarity),
            'feature_differences': feature_differences,
            'style1': style1,
            'style2': style2
        })
    except Exception as e:
        import traceback
        error_details = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"\n❌ Error in compare-artifacts endpoint:")
        print(traceback.format_exc())
        return jsonify(error_details), 500


@web_bp.route('/find-similar', methods=['POST'])
def find_similar_artifacts():
    """Find similar artifacts using batch comparison (1:many)."""
    try:
        from acs.core.similarity_search import get_similarity_engine
        from acs.core.stylistic_analyzer import get_stylistic_analyzer
        from acs.core.database import get_database

        data = request.json
        query_id = data.get('query_id')
        n_results = data.get('n_results', 10)
        metric = data.get('metric', 'cosine')  # cosine or euclidean
        min_similarity = data.get('min_similarity', 0.0)

        # Lazy load query mesh from storage if not in memory
        if not ensure_mesh_loaded(query_id):
            return jsonify({'error': 'Query artifact not found'}), 404

        # Build similarity search index
        search_engine = get_similarity_engine()
        stylistic = get_stylistic_analyzer()

        # Get all artifact IDs from database and lazy-load them
        db = get_database()
        all_artifacts = db.get_all_artifacts()
        for artifact in all_artifacts:
            artifact_id = artifact['artifact_id']
            if ensure_mesh_loaded(artifact_id):
                mesh = mesh_processor.meshes[artifact_id]
                morph_features = mesh_processor._extract_features(mesh, artifact_id)
                style_features = stylistic.analyze_style(mesh, artifact_id, morph_features)
                search_engine.add_artifact_features(artifact_id, morph_features, style_features)

        # Build index
        search_engine.build_index()

        # Find similar artifacts using SIMPLE comparison (same as 1:1)
        # Don't use search_engine's complex cosine similarity
        query_features = mesh_processor._extract_features(
            mesh_processor.meshes[query_id],
            query_id
        )

        similar_artifacts = []
        feature_keys = ['volume', 'surface_area', 'length', 'width', 'height', 'compactness']

        for artifact_id, mesh in mesh_processor.meshes.items():
            if artifact_id == query_id:
                continue

            # Compare using same method as 1:1 comparison
            other_features = mesh_processor._extract_features(mesh, artifact_id)

            similarity_sum = 0
            valid_features = 0

            for key in feature_keys:
                if key in query_features and key in other_features:
                    val1 = query_features[key]
                    val2 = other_features[key]
                    max_val = max(abs(val1), abs(val2))

                    if max_val > 1e-10:
                        diff = abs(val1 - val2) / max_val
                        similarity = max(0, min(1, 1 - diff))
                        similarity_sum += similarity
                        valid_features += 1

            if valid_features > 0:
                avg_similarity = similarity_sum / valid_features
                if avg_similarity >= min_similarity:
                    similar_artifacts.append((artifact_id, avg_similarity))

        # Sort by similarity descending
        similar_artifacts.sort(key=lambda x: x[1], reverse=True)
        similar_artifacts = similar_artifacts[:n_results]

        import sys
        print(f"\n=== FIND SIMILAR DEBUG ===", flush=True)
        print(f"Query ID: {query_id}", flush=True)
        print(f"Min similarity threshold: {min_similarity}", flush=True)
        print(f"Found {len(similar_artifacts)} similar artifacts", flush=True)
        print(f"Similar artifacts: {similar_artifacts}", flush=True)
        print(f"=== END DEBUG ===\n", flush=True)
        sys.stdout.flush()

        # Get detailed info for each result
        results = []
        for artifact_id, similarity_score in similar_artifacts:
            morph_features = mesh_processor._extract_features(
                mesh_processor.meshes[artifact_id],
                artifact_id
            )
            results.append({
                'artifact_id': artifact_id,
                'similarity_score': float(similarity_score),
                'features': morph_features
            })

        return jsonify({
            'status': 'success',
            'query_id': query_id,
            'n_results': len(results),
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/batch-compare', methods=['POST'])
def batch_compare_artifacts():
    """Compare one artifact to many targets."""
    try:
        from acs.core.similarity_search import get_similarity_engine
        from acs.core.stylistic_analyzer import get_stylistic_analyzer

        data = request.json
        query_id = data.get('query_id')
        target_ids = data.get('target_ids', [])

        if query_id not in mesh_processor.meshes:
            return jsonify({'error': 'Query artifact not found'}), 404

        if not target_ids:
            return jsonify({'error': 'No target artifacts specified'}), 400

        # Build search index
        search_engine = get_similarity_engine()
        stylistic = get_stylistic_analyzer()

        for artifact_id, mesh in mesh_processor.meshes.items():
            if artifact_id == query_id or artifact_id in target_ids:
                morph_features = mesh_processor._extract_features(mesh, artifact_id)
                style_features = stylistic.analyze_style(mesh, artifact_id, morph_features)
                search_engine.add_artifact_features(artifact_id, morph_features, style_features)

        search_engine.build_index()

        # Batch compare
        results = search_engine.batch_compare(query_id, target_ids)

        # Enrich results
        enriched_results = []
        for artifact_id, similarity_score in results:
            enriched_results.append({
                'artifact_id': artifact_id,
                'similarity_score': float(similarity_score)
            })

        return jsonify({
            'status': 'success',
            'query_id': query_id,
            'results': enriched_results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/generate-report', methods=['POST'])
def generate_report():
    """Generate PDF report comparing two artifacts with stylistic analysis."""
    try:
        from acs.core.stylistic_analyzer import get_stylistic_analyzer

        data = request.json
        artifact1 = data.get('artifact1')
        artifact2 = data.get('artifact2')

        if artifact1 not in mesh_processor.meshes or artifact2 not in mesh_processor.meshes:
            return jsonify({'error': 'One or both artifacts not found'}), 404

        # Get morphometric features
        features1 = mesh_processor._extract_features(mesh_processor.meshes[artifact1], artifact1)
        features2 = mesh_processor._extract_features(mesh_processor.meshes[artifact2], artifact2)

        # Get stylistic features
        stylistic = get_stylistic_analyzer()
        style1 = stylistic.analyze_style(mesh_processor.meshes[artifact1], artifact1, features1)
        style2 = stylistic.analyze_style(mesh_processor.meshes[artifact2], artifact2, features2)

        # Generate PDF report
        from acs.core.report_generator import ReportGenerator

        report_gen = ReportGenerator()
        pdf_path = report_gen.generate_comparison_report(
            artifact1=artifact1,
            artifact2=artifact2,
            mesh1=mesh_processor.meshes[artifact1],
            mesh2=mesh_processor.meshes[artifact2],
            features1=features1,
            features2=features2,
            style1=style1,
            style2=style2
        )

        from flask import send_file
        return send_file(pdf_path, mimetype='application/pdf', as_attachment=True,
                        download_name=f'comparison_{artifact1}_{artifact2}.pdf')
    except Exception as e:
        import traceback
        error_details = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"\n❌ Error in generate-report endpoint:")
        print(traceback.format_exc())
        return jsonify(error_details), 500


@web_bp.route('/ai-classify', methods=['POST'])
def ai_classify_artifact():
    """Use AI to analyze and suggest classification."""
    try:
        from acs.core.ai_assistant import get_ai_assistant
        from acs.core.database import get_database

        data = request.json
        artifact_id = data.get('artifact_id')

        if artifact_id not in mesh_processor.meshes:
            return jsonify({'error': 'Artifact not found'}), 404

        # Get features
        features = mesh_processor._extract_features(
            mesh_processor.meshes[artifact_id],
            artifact_id
        )

        # Get existing classes
        classes = [
            {
                'name': tc.name,
                'description': tc.description,
                'n_samples': len(tc.validated_samples)
            }
            for tc in taxonomy_system.classes.values()
        ]

        # AI analysis
        ai = get_ai_assistant()
        if ai is None:
            return jsonify({
                'error': 'AI Assistant not available. Set ANTHROPIC_API_KEY environment variable.'
            }), 503

        context = data.get('context', '')
        result = ai.analyze_artifact(artifact_id, features, classes, context)

        # Save to database with mesh path if available
        db = get_database()
        mesh = mesh_processor.meshes[artifact_id]
        mesh_path = mesh_processor.mesh_paths.get(artifact_id, '')
        db.add_artifact(
            artifact_id=artifact_id,
            mesh_path=mesh_path,
            n_vertices=len(mesh.vertices),
            n_faces=len(mesh.faces),
            is_watertight=mesh.is_watertight
        )
        db.add_features(artifact_id, features)

        return jsonify({
            'status': 'success',
            'artifact_id': artifact_id,
            'ai_analysis': result
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/ai-classify-stream', methods=['POST'])
def ai_classify_artifact_stream():
    """Use AI to analyze with streaming response (SSE)."""
    try:
        from acs.core.ai_assistant import get_ai_assistant
        from acs.core.database import get_database
        from flask import Response, stream_with_context

        data = request.json
        artifact_id = data.get('artifact_id')
        context = data.get('context', '')

        if artifact_id not in mesh_processor.meshes:
            return jsonify({'error': 'Artifact not found'}), 404

        # Get features
        features = mesh_processor._extract_features(
            mesh_processor.meshes[artifact_id],
            artifact_id
        )

        # Get existing classes
        classes = [
            {
                'name': tc.name,
                'description': tc.description,
                'n_samples': len(tc.validated_samples)
            }
            for tc in taxonomy_system.classes.values()
        ]

        # AI analysis
        ai = get_ai_assistant()
        if ai is None:
            return jsonify({
                'error': 'AI Assistant not available. Set ANTHROPIC_API_KEY environment variable.'
            }), 503

        # Save to database
        db = get_database()
        mesh = mesh_processor.meshes[artifact_id]
        mesh_path = mesh_processor.mesh_paths.get(artifact_id, '')
        db.add_artifact(
            artifact_id=artifact_id,
            mesh_path=mesh_path,
            n_vertices=len(mesh.vertices),
            n_faces=len(mesh.faces),
            is_watertight=mesh.is_watertight
        )
        db.add_features(artifact_id, features)

        def generate():
            """Generator for SSE streaming."""
            try:
                # Send initial event with artifact info
                yield f"data: {json.dumps({'type': 'start', 'artifact_id': artifact_id})}\n\n"

                # Stream AI analysis
                for text_chunk in ai.analyze_artifact_stream(artifact_id, features, classes, context):
                    yield f"data: {json.dumps({'type': 'text', 'content': text_chunk})}\n\n"

                # Send completion event
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/ai-multi-analyze', methods=['POST'])
def ai_multi_analyze():
    """Analyze multiple artifacts together with AI."""
    try:
        from acs.core.ai_assistant import get_ai_assistant
        from acs.core.stylistic_analyzer import StylisticAnalyzer

        data = request.json
        artifact_ids = data.get('artifact_ids', [])
        context = data.get('context', '')

        if not artifact_ids:
            return jsonify({'error': 'No artifacts specified'}), 400

        # Prepare artifacts data with morphometric and stylistic features
        artifacts = []
        stylistic_analyzer = StylisticAnalyzer()

        for artifact_id in artifact_ids:
            if artifact_id not in mesh_processor.meshes:
                continue

            # Extract morphometric features
            mesh = mesh_processor.meshes[artifact_id]
            features = mesh_processor._extract_features(mesh, artifact_id)

            # Extract stylistic features using analyze_style (which does everything)
            stylistic_features = stylistic_analyzer.analyze_style(mesh, artifact_id, features)

            artifacts.append({
                'id': artifact_id,
                'features': features,
                'stylistic_features': stylistic_features
            })

        if not artifacts:
            return jsonify({'error': 'No valid artifacts found'}), 404

        # Get existing classes
        classes = [
            {
                'name': tc.name,
                'description': tc.description,
                'n_samples': len(tc.validated_samples)
            }
            for tc in taxonomy_system.classes.values()
        ]

        # AI multi-analysis
        ai = get_ai_assistant()
        if ai is None:
            return jsonify({
                'error': 'AI Assistant not available. Set ANTHROPIC_API_KEY.'
            }), 503

        result = ai.analyze_multi_artifacts(artifacts, classes, context)

        return jsonify({
            'success': True,
            'artifacts_analyzed': len(artifacts),
            'analysis': result.get('analysis'),
            'raw_text': result.get('raw_text'),
            'model': result.get('model'),
            'usage': result.get('usage')
        })

    except Exception as e:
        import traceback
        print(f"\n❌ Error in ai-multi-analyze:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@web_bp.route('/ai-suggest-parameters', methods=['POST'])
def ai_suggest_parameters():
    """Get AI suggestions for analysis parameters."""
    try:
        from acs.core.ai_assistant import get_ai_assistant
        from acs.core.stylistic_analyzer import StylisticAnalyzer

        data = request.json
        artifact_id = data.get('artifact_id')

        if not artifact_id or artifact_id not in mesh_processor.meshes:
            return jsonify({'error': 'Artifact not found'}), 404

        # Extract features
        mesh = mesh_processor.meshes[artifact_id]
        features = mesh_processor._extract_features(mesh, artifact_id)

        # Extract stylistic features using analyze_style
        stylistic_analyzer = StylisticAnalyzer()
        stylistic_features = stylistic_analyzer.analyze_style(mesh, artifact_id, features)

        # AI parameter suggestion
        ai = get_ai_assistant()
        if ai is None:
            return jsonify({
                'error': 'AI Assistant not available. Set ANTHROPIC_API_KEY.'
            }), 503

        result = ai.suggest_analysis_parameters(artifact_id, features, stylistic_features)

        return jsonify({
            'success': True,
            'artifact_id': artifact_id,
            'parameters': result.get('parameters'),
            'raw_text': result.get('raw_text'),
            'model': result.get('model')
        })

    except Exception as e:
        import traceback
        print(f"\n❌ Error in ai-suggest-parameters:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@web_bp.route('/ai-apply-batch-analysis', methods=['POST'])
def ai_apply_batch_analysis():
    """Apply analysis parameters to multiple artifacts (after user confirmation)."""
    try:
        from acs.core.database import get_database

        data = request.json
        artifacts_params = data.get('artifacts_params', [])  # List of {artifact_id, parameters}
        confirmed = data.get('confirmed', False)

        if not confirmed:
            return jsonify({'error': 'User confirmation required'}), 400

        if not artifacts_params:
            return jsonify({'error': 'No artifacts specified'}), 400

        # Apply analysis to each artifact
        results = []
        db = get_database()

        for item in artifacts_params:
            artifact_id = item.get('artifact_id')
            parameters = item.get('parameters', {})

            if artifact_id not in mesh_processor.meshes:
                results.append({
                    'artifact_id': artifact_id,
                    'status': 'error',
                    'message': 'Artifact not found'
                })
                continue

            try:
                # Extract features with suggested parameters
                mesh = mesh_processor.meshes[artifact_id]
                features = mesh_processor._extract_features(mesh, artifact_id)

                # Apply morphometric parameters
                morph_params = parameters.get('morphometric_params', {})
                feature_weights = morph_params.get('feature_weights', {})

                # Apply weighted features if provided
                weighted_features = features.copy()
                for feature_name, weight in feature_weights.items():
                    if feature_name in weighted_features:
                        weighted_features[feature_name] *= weight

                # Run similarity search with suggested parameters
                tax_params = parameters.get('taxonomic_params', {})
                min_similarity = tax_params.get('min_similarity', 0.7)
                n_results = tax_params.get('n_results', 10)

                similar = search_engine.find_similar(
                    artifact_id,
                    n_results=n_results,
                    min_similarity=min_similarity
                )

                # Save results to database
                db.add_artifact(
                    artifact_id=artifact_id,
                    mesh_path=mesh_processor.mesh_paths.get(artifact_id, ''),
                    n_vertices=len(mesh.vertices),
                    n_faces=len(mesh.faces)
                )
                db.add_features(artifact_id, weighted_features)

                # Save analysis parameters
                with db.get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO analysis_parameters
                        (artifact_id, parameters_json, applied_at)
                        VALUES (?, ?, datetime('now'))
                    """, (artifact_id, json.dumps(parameters)))

                results.append({
                    'artifact_id': artifact_id,
                    'status': 'success',
                    'similar_count': len(similar),
                    'parameters_applied': parameters
                })

            except Exception as e:
                results.append({
                    'artifact_id': artifact_id,
                    'status': 'error',
                    'message': str(e)
                })

        # Create analysis_parameters table if it doesn't exist
        with db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_parameters (
                    artifact_id TEXT PRIMARY KEY,
                    parameters_json TEXT,
                    applied_at TEXT
                )
            """)

        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results),
            'successful': sum(1 for r in results if r['status'] == 'success')
        })

    except Exception as e:
        import traceback
        print(f"\n❌ Error in ai-apply-batch-analysis:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@web_bp.route('/ml-predict', methods=['POST'])
def ml_predict_artifact():
    """Use ML model to predict artifact class."""
    try:
        from acs.core.ml_classifier import get_ml_classifier
        from acs.core.database import get_database

        data = request.json
        artifact_id = data.get('artifact_id')

        if artifact_id not in mesh_processor.meshes:
            return jsonify({'error': 'Artifact not found'}), 404

        # Get features
        db = get_database()
        features = db.get_features(artifact_id)

        if not features:
            # Extract and save features
            features = mesh_processor._extract_features(
                mesh_processor.meshes[artifact_id],
                artifact_id
            )
            db.add_features(artifact_id, features)

        # ML prediction
        ml = get_ml_classifier()
        prediction = ml.predict(features)

        if prediction.get('error'):
            return jsonify({
                'status': 'error',
                'message': 'ML model not trained yet. Need at least 20 validated samples.',
                'error': prediction['error']
            }), 400

        # Get explanation
        explanation = ml.explain_prediction(features, prediction)

        return jsonify({
            'status': 'success',
            'artifact_id': artifact_id,
            'prediction': prediction,
            'explanation': explanation
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/hybrid-classify', methods=['POST'])
def hybrid_classify_artifact():
    """Hybrid classification using both rule-based and ML."""
    try:
        from acs.core.ml_classifier import get_ml_classifier
        from acs.core.database import get_database

        data = request.json
        artifact_id = data.get('artifact_id')

        if artifact_id not in mesh_processor.meshes:
            return jsonify({'error': 'Artifact not found'}), 404

        # Get features
        db = get_database()
        features = db.get_features(artifact_id)

        if not features:
            features = mesh_processor._extract_features(
                mesh_processor.meshes[artifact_id],
                artifact_id
            )
            db.add_features(artifact_id, features)

        # Rule-based classification
        rule_result = taxonomy_system.classify_object(features, return_all_scores=True)

        # ML classification
        ml = get_ml_classifier()
        ml_result = ml.predict(features)

        # Combine results
        recommendation = _combine_classifications(rule_result, ml_result)

        return jsonify({
            'status': 'success',
            'artifact_id': artifact_id,
            'rule_based': rule_result,
            'ml_based': ml_result,
            'recommendation': recommendation
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/ml-train', methods=['POST'])
def ml_train_model():
    """Train ML model with data from database."""
    try:
        from acs.core.ml_classifier import get_ml_classifier
        from acs.core.database import get_database

        db = get_database()
        training_data = db.get_training_data()

        if len(training_data) < 10:
            return jsonify({
                'error': f'Need at least 10 training samples. Current: {len(training_data)}',
                'n_samples': len(training_data)
            }), 400

        data = request.json
        algorithm = data.get('algorithm', 'random_forest')
        val_split = data.get('validation_split', 0.2)

        ml = get_ml_classifier()
        result = ml.train(training_data, val_split, algorithm)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/auto-classify-stylistic', methods=['POST'])
def auto_classify_stylistic():
    """
    Automatically classify all unclassified artifacts using stylistic analysis.

    Combines:
    - Morphometric features
    - Stylistic analysis (symmetry, proportions, surface quality)
    - AI classification (if available)
    - ML prediction (if trained)
    """
    try:
        from acs.core.stylistic_analyzer import get_stylistic_analyzer
        from acs.core.ai_assistant import get_ai_assistant
        from acs.core.ml_classifier import get_ml_classifier
        from acs.core.database import get_database

        db = get_database()
        stylistic = get_stylistic_analyzer()

        # Get all artifacts
        all_artifacts = list(mesh_processor.meshes.keys())

        # Filter unclassified (those not in taxonomy or database without class)
        unclassified = []
        for artifact_id in all_artifacts:
            # Check if already classified in database
            artifact_info = db.get_artifact(artifact_id)
            if not artifact_info or not artifact_info.get('class_name'):
                unclassified.append(artifact_id)

        if not unclassified:
            return jsonify({
                'status': 'success',
                'message': 'All artifacts are already classified',
                'total': len(all_artifacts),
                'classified': len(all_artifacts),
                'results': []
            })

        # Classify each unclassified artifact
        results = []
        ai = None
        try:
            ai = get_ai_assistant()
        except:
            pass  # AI optional

        ml = None
        try:
            ml = get_ml_classifier()
            if not ml.is_trained():
                ml = None
        except:
            pass  # ML optional

        for artifact_id in unclassified:
            try:
                mesh = mesh_processor.meshes[artifact_id]

                # Extract morphometric features
                morph_features = mesh_processor._extract_features(mesh, artifact_id)

                # Stylistic analysis
                style_features = stylistic.analyze_style(mesh, artifact_id, morph_features)

                # Get existing classes for context
                classes = [
                    {
                        'name': tc.name,
                        'description': tc.description,
                        'n_samples': len(tc.validated_samples)
                    }
                    for tc in taxonomy_system.classes.values()
                ]

                # Try AI classification
                ai_suggestion = None
                if ai:
                    ai_result = ai.analyze_artifact(artifact_id, morph_features, classes,
                                                   f"Stylistic Analysis: {style_features}")
                    ai_suggestion = ai_result.get('analysis')

                # Try ML prediction
                ml_prediction = None
                ml_confidence = 0
                if ml:
                    ml_result = ml.predict(morph_features)
                    ml_prediction = ml_result.get('predicted_class')
                    ml_confidence = ml_result.get('confidence', 0)

                # Rule-based classification (returns list when return_all_scores=True)
                rule_results = taxonomy_system.classify_object(morph_features, return_all_scores=True)

                # Get best rule-based result
                best_rule = rule_results[0] if rule_results else None
                rule_class = best_rule['class_name'] if best_rule else None
                rule_confidence = best_rule['confidence'] if best_rule else 0

                # Get overall stylistic quality (use surface_quality as proxy)
                stylistic_score = style_features.get('surface_quality', {}).get('score', 0) if isinstance(style_features.get('surface_quality'), dict) else 0

                # Combine all information
                classification = {
                    'artifact_id': artifact_id,
                    'stylistic_score': stylistic_score,
                    'rule_based': best_rule,
                    'ml_prediction': ml_prediction,
                    'ml_confidence': ml_confidence,
                    'ai_suggestion': ai_suggestion[:200] + '...' if ai_suggestion and len(ai_suggestion) > 200 else ai_suggestion,
                    'recommended_class': ml_prediction if ml_confidence > 0.7 else rule_class,
                    'confidence': ml_confidence if ml_confidence > 0.7 else rule_confidence
                }

                results.append(classification)

                # Auto-save classification if confidence is high
                if classification['confidence'] > 0.8 and classification['recommended_class']:
                    db.add_classification(
                        artifact_id=artifact_id,
                        class_id=classification['recommended_class'],
                        class_name=classification['recommended_class'],
                        confidence=classification['confidence'],
                        validated=False,
                        notes=f"Automatic stylistic classification. ML: {ml_confidence:.2f}, Style: {stylistic_score:.2f}"
                    )

            except Exception as e:
                results.append({
                    'artifact_id': artifact_id,
                    'error': str(e)
                })

        return jsonify({
            'status': 'success',
            'total': len(all_artifacts),
            'unclassified': len(unclassified),
            'processed': len(results),
            'auto_classified': sum(1 for r in results if r.get('confidence', 0) > 0.8),
            'results': results
        })

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@web_bp.route('/config/api-key', methods=['GET'])
def get_api_key_status():
    """Check if API key is configured."""
    try:
        from acs.core.config import get_config

        config = get_config()
        has_key = config.has_api_key()

        if has_key:
            # Return masked key
            key = config.get_api_key()
            masked = key[:8] + '...' + key[-4:] if len(key) > 12 else '***'
            return jsonify({
                'configured': True,
                'masked_key': masked
            })
        else:
            return jsonify({'configured': False})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/config/api-key', methods=['POST'])
def save_api_key():
    """Save Anthropic API key."""
    try:
        from acs.core.config import get_config

        data = request.json
        api_key = data.get('api_key', '').strip()

        if not api_key:
            return jsonify({'error': 'API key cannot be empty'}), 400

        # Basic validation
        if not api_key.startswith('sk-ant-'):
            return jsonify({'error': 'Invalid API key format. Should start with sk-ant-'}), 400

        config = get_config()
        config.set_api_key(api_key)

        # Note: AI assistant will be reinitialized on next use with new key

        return jsonify({
            'status': 'success',
            'message': 'API key saved successfully',
            'masked_key': api_key[:8] + '...' + api_key[-4:]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/config/api-key', methods=['DELETE'])
def delete_api_key():
    """Delete stored API key."""
    try:
        from acs.core.config import get_config

        config = get_config()
        config.delete('anthropic_api_key')

        return jsonify({
            'status': 'success',
            'message': 'API key deleted'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/reload-meshes', methods=['POST'])
def reload_meshes():
    """Manually reload all meshes from database."""
    try:
        from acs.core.database import get_database

        db = get_database()
        stats = mesh_processor.reload_from_database(db)

        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== PROJECT MANAGEMENT ROUTES ==========

@web_bp.route('/projects', methods=['GET'])
def list_projects():
    """List all projects."""
    try:
        from acs.core.database import get_database

        db = get_database()
        status = request.args.get('status')  # Optional filter
        # If status is "all", pass None to get all projects
        if status == 'all':
            status = None
        projects = db.list_projects(status=status)

        # Get statistics for each project
        for project in projects:
            stats = db.get_project_statistics(project['project_id'])
            project['stats'] = stats

        return jsonify({
            'status': 'success',
            'projects': projects
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    try:
        from acs.core.database import get_database

        data = request.json
        project_id = data.get('project_id')
        name = data.get('name')
        description = data.get('description', '')

        if not project_id or not name:
            return jsonify({'error': 'project_id and name are required'}), 400

        db = get_database()
        db.create_project(project_id, name, description)

        return jsonify({
            'status': 'success',
            'project_id': project_id,
            'message': f'Project "{name}" created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get project details with artifacts."""
    try:
        from acs.core.database import get_database

        db = get_database()
        project = db.get_project(project_id)

        if not project:
            return jsonify({'error': 'Project not found'}), 404

        # Get artifacts for this project
        artifacts = db.get_project_artifacts(project_id)

        # Get statistics
        stats = db.get_project_statistics(project_id)

        return jsonify({
            'status': 'success',
            'project': project,
            'artifacts': artifacts,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project (archives it)."""
    try:
        from acs.core.database import get_database

        db = get_database()
        project = db.get_project(project_id)

        if not project:
            return jsonify({'error': 'Project not found'}), 404

        # Archive instead of delete
        db.update_project_status(project_id, 'archived')

        return jsonify({
            'status': 'success',
            'message': f'Project "{project_id}" archived successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/projects/<project_id>/artifacts/<artifact_id>', methods=['POST'])
def assign_artifact_to_project(project_id, artifact_id):
    """Assign an artifact to a project."""
    try:
        from acs.core.database import get_database

        db = get_database()
        db.assign_artifact_to_project(artifact_id, project_id)

        return jsonify({
            'status': 'success',
            'message': f'Artifact {artifact_id} assigned to project {project_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/projects/merge', methods=['POST'])
def merge_projects():
    """Merge multiple projects into one."""
    try:
        from acs.core.database import get_database

        data = request.json
        source_ids = data.get('source_project_ids', [])
        target_id = data.get('target_project_id')
        target_name = data.get('target_name')
        target_description = data.get('target_description', '')

        if not source_ids or not target_id or not target_name:
            return jsonify({'error': 'source_project_ids, target_project_id, and target_name are required'}), 400

        db = get_database()
        db.merge_projects(source_ids, target_id, target_name, target_description)

        return jsonify({
            'status': 'success',
            'message': f'{len(source_ids)} projects merged into {target_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== TECHNICAL DRAWING ROUTES ==========

@web_bp.route('/technical-drawing/<artifact_id>', methods=['GET'])
def get_technical_drawing(artifact_id):
    """Generate complete technical drawing sheet for an artifact."""
    try:
        from acs.core.drawing_worker import generate_drawing_safe

        if artifact_id not in mesh_processor.meshes:
            return jsonify({'error': 'Artifact not found'}), 404

        mesh = mesh_processor.meshes[artifact_id]
        features = mesh_processor._extract_features(mesh, artifact_id)

        # Generate drawing in separate process (safe on macOS)
        image_data = generate_drawing_safe(mesh, artifact_id, features, 'complete_sheet', timeout=60)

        # Return image
        from flask import send_file
        return send_file(
            io.BytesIO(image_data),
            mimetype='image/png',
            as_attachment=True,
            download_name=f'{artifact_id}_technical_drawing.png'
        )

    except Exception as e:
        import traceback
        print(f"Error generating technical drawing: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@web_bp.route('/technical-drawing/<artifact_id>/<view_type>', methods=['GET'])
def get_technical_drawing_view(artifact_id, view_type):
    """
    Get specific technical drawing view.

    view_type: 'longitudinal_profile', 'cross_section_max', 'cross_section_min',
               'front_view', 'back_view', 'complete_sheet'
    """
    try:
        from acs.core.drawing_worker import generate_drawing_safe

        if artifact_id not in mesh_processor.meshes:
            return jsonify({'error': 'Artifact not found'}), 404

        mesh = mesh_processor.meshes[artifact_id]
        features = mesh_processor._extract_features(mesh, artifact_id)

        # Generate drawing in separate process (safe on macOS)
        image_data = generate_drawing_safe(mesh, artifact_id, features, view_type, timeout=60)

        # Return image
        from flask import send_file
        return send_file(
            io.BytesIO(image_data),
            mimetype='image/png',
            as_attachment=True,
            download_name=f'{artifact_id}_{view_type}.png'
        )

    except Exception as e:
        import traceback
        print(f"Error generating technical drawing view: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@web_bp.route('/projects-page')
def projects_page():
    """Projects management page."""
    return render_template('projects_list.html')


@web_bp.route('/drawings')
def drawings_page():
    """Technical drawings page."""
    return render_template('technical_drawings.html')


@web_bp.route('/ai-assistant')
def ai_assistant_page():
    """AI Assistant page."""
    artifacts = list(mesh_processor.meshes.keys())
    return render_template('ai_assistant.html', artifacts=artifacts)


def _combine_classifications(rule_result: dict, ml_result: dict) -> str:
    """Combine rule-based and ML classifications."""
    if ml_result.get('error'):
        return f"Rule-based only: {rule_result.get('assigned_class', 'None')}"

    rule_class = rule_result.get('assigned_class')
    ml_class = ml_result.get('prediction')
    ml_conf = ml_result.get('confidence', 0)

    if rule_class == ml_class:
        return f"Both methods agree: {rule_class} (ML confidence: {ml_conf:.2%})"
    elif ml_conf > 0.8:
        return f"ML suggests {ml_class} (high confidence: {ml_conf:.2%}), but rule-based suggests {rule_class}"
    else:
        return f"Rule-based: {rule_class}, ML: {ml_class} (confidence: {ml_conf:.2%})"


# ========== TAXONOMY MANAGEMENT ROUTES ==========

@web_bp.route('/taxonomy/classes', methods=['GET'])
def get_taxonomy_classes():
    """Get all taxonomy classes."""
    try:
        classes_data = []
        for class_id, tax_class in taxonomy_system.classes.items():
            classes_data.append({
                'class_id': class_id,
                'name': tax_class.name,
                'description': tax_class.description,
                'n_samples': len(tax_class.validated_samples),
                'n_morphometric_params': len(tax_class.morphometric_params),
                'n_technological_params': len(tax_class.technological_params),
                'confidence_threshold': tax_class.confidence_threshold,
                'created_date': tax_class.created_date.isoformat() if hasattr(tax_class.created_date, 'isoformat') else str(tax_class.created_date),
                'created_by': tax_class.created_by,
                'parameter_hash': tax_class.parameter_hash
            })

        return jsonify({
            'status': 'success',
            'classes': classes_data,
            'total': len(classes_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/taxonomy/classes/<class_id>', methods=['GET'])
def get_taxonomy_class_details(class_id):
    """Get detailed information about a taxonomy class."""
    try:
        if class_id not in taxonomy_system.classes:
            return jsonify({'error': 'Class not found'}), 404

        tax_class = taxonomy_system.classes[class_id]

        # Serialize morphometric parameters
        morphometric = {}
        for param_name, param in tax_class.morphometric_params.items():
            morphometric[param_name] = param.to_dict()

        # Serialize technological parameters
        technological = {}
        for param_name, param in tax_class.technological_params.items():
            technological[param_name] = param.to_dict()

        class_data = {
            'class_id': class_id,
            'name': tax_class.name,
            'description': tax_class.description,
            'morphometric_params': morphometric,
            'technological_params': technological,
            'optional_features': tax_class.optional_features,
            'confidence_threshold': tax_class.confidence_threshold,
            'created_date': tax_class.created_date.isoformat() if hasattr(tax_class.created_date, 'isoformat') else str(tax_class.created_date),
            'created_by': tax_class.created_by,
            'validated_samples': tax_class.validated_samples,
            'parameter_hash': tax_class.parameter_hash
        }

        return jsonify({
            'status': 'success',
            'class': class_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/taxonomy/classes/<class_id>', methods=['PUT'])
def modify_taxonomy_class(class_id):
    """Modify parameters of an existing taxonomy class."""
    try:
        data = request.json
        parameter_changes = data.get('parameter_changes', {})
        justification = data.get('justification', '')
        operator = data.get('operator', 'user')

        if not justification:
            return jsonify({'error': 'Justification is required'}), 400

        # Modify class
        new_class = taxonomy_system.modify_class_parameters(
            class_id=class_id,
            parameter_changes=parameter_changes,
            justification=justification,
            operator=operator
        )

        return jsonify({
            'status': 'success',
            'message': 'Class parameters updated',
            'new_class_id': new_class.class_id,
            'old_hash': taxonomy_system.classes.get(class_id, {}).parameter_hash if class_id in taxonomy_system.classes else None,
            'new_hash': new_class.parameter_hash
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/taxonomy/classes', methods=['POST'])
def create_taxonomy_class_from_group():
    """Create a new taxonomy class from a reference group."""
    try:
        data = request.json
        class_name = data.get('class_name')
        artifact_ids = data.get('artifact_ids', [])
        tolerance_factor = data.get('tolerance_factor', 0.15)

        if not class_name or len(artifact_ids) < 2:
            return jsonify({'error': 'Need class_name and at least 2 artifact_ids'}), 400

        # Extract features from selected artifacts
        reference_objects = []
        for artifact_id in artifact_ids:
            if artifact_id not in mesh_processor.meshes:
                continue

            mesh = mesh_processor.meshes[artifact_id]
            features = mesh_processor._extract_features(mesh, artifact_id)
            reference_objects.append(features)

        if len(reference_objects) < 2:
            return jsonify({'error': 'Not enough valid artifacts found'}), 400

        # Create class
        new_class = taxonomy_system.define_class_from_reference_group(
            class_name=class_name,
            reference_objects=reference_objects,
            tolerance_factor=tolerance_factor
        )

        return jsonify({
            'status': 'success',
            'message': f'Class "{class_name}" created from {len(reference_objects)} reference objects',
            'class_id': new_class.class_id,
            'class_name': new_class.name,
            'n_samples': len(new_class.validated_samples)
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


# ========== ML TRAINING ROUTES ==========

@web_bp.route('/ml/status', methods=['GET'])
def get_ml_status():
    """Get ML classifier status."""
    try:
        from acs.core.ml_classifier import get_ml_classifier
        from acs.core.database import get_database

        ml = get_ml_classifier()
        db = get_database()

        # Get training data statistics
        training_stats = db.get_training_statistics()

        # Check if model is trained (is_trained is a property, not a method)
        is_trained = ml.is_trained

        status = {
            'is_trained': is_trained,
            'model_path': ml.model_path if hasattr(ml, 'model_path') else None,
            'training_data': training_stats,
            'available_for_training': training_stats.get('total_samples', 0) >= 5,
            'min_samples_per_class': 2,
            'recommended_samples_per_class': 5
        }

        return jsonify({
            'status': 'success',
            'ml_status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/ml/train', methods=['POST'])
def train_ml_model():
    """Train the ML classifier."""
    try:
        from acs.core.ml_classifier import get_ml_classifier
        from acs.core.database import get_database

        data = request.json
        algorithm = data.get('algorithm', 'random_forest')  # random_forest, svm, gradient_boosting
        validation_split = data.get('validation_split', 0.2)

        ml = get_ml_classifier()
        db = get_database()

        # Get training data
        training_data = db.get_training_data()

        if len(training_data) < 5:
            return jsonify({
                'error': f'Not enough training data. Need at least 5 samples, have {len(training_data)}'
            }), 400

        # Train model
        results = ml.train(
            training_data=training_data,
            validation_split=validation_split,
            algorithm=algorithm
        )

        return jsonify({
            'status': 'success',
            'message': 'Model trained successfully',
            'results': results
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@web_bp.route('/ml/training-data', methods=['GET'])
def get_training_data():
    """Get available training data."""
    try:
        from acs.core.database import get_database

        db = get_database()
        training_data = db.get_training_data()
        stats = db.get_training_statistics()

        return jsonify({
            'status': 'success',
            'training_data': training_data,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/classifications/<artifact_id>/validate', methods=['POST'])
def validate_classification(artifact_id):
    """Validate a classification and add to training data."""
    try:
        from acs.core.database import get_database

        data = request.json
        class_name = data.get('class_name')
        confidence = data.get('confidence', 1.0)

        if not class_name:
            return jsonify({'error': 'class_name is required'}), 400

        if artifact_id not in mesh_processor.meshes:
            return jsonify({'error': 'Artifact not found'}), 404

        db = get_database()

        # Get features for this artifact
        mesh = mesh_processor.meshes[artifact_id]
        features = mesh_processor._extract_features(mesh, artifact_id)

        # Save classification
        db.add_classification(
            artifact_id=artifact_id,
            class_id=class_name,
            class_name=class_name,
            confidence=confidence,
            validated=True,
            notes='Manually validated classification'
        )

        # Add to training data
        db.add_training_sample(
            artifact_id=artifact_id,
            class_label=class_name,
            features=features,
            validation_score=confidence
        )

        # Also add to taxonomy class validated samples
        for class_id, tax_class in taxonomy_system.classes.items():
            if tax_class.name == class_name and artifact_id not in tax_class.validated_samples:
                tax_class.validated_samples.append(artifact_id)
                break

        return jsonify({
            'status': 'success',
            'message': f'Classification validated and added to training set',
            'artifact_id': artifact_id,
            'class_name': class_name
        })

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@web_bp.route('/technological-analysis/<artifact_id>', methods=['GET'])
def technological_analysis(artifact_id):
    """Perform technological analysis on an artifact."""
    try:
        from acs.core.technological_analyzer import get_technological_analyzer
        from acs.core.ai_assistant import get_ai_assistant

        if artifact_id not in mesh_processor.meshes:
            return jsonify({'error': 'Artifact not found'}), 404

        mesh = mesh_processor.meshes[artifact_id]

        # Perform technological analysis
        tech_analyzer = get_technological_analyzer()
        tech_features = tech_analyzer.analyze_technology(mesh, artifact_id)

        # Generate technical report
        tech_report = tech_analyzer.generate_technical_report(tech_features, artifact_id)

        # Get structured AI interpretation (temp=0.1, JSON output)
        ai_interpretation = None
        try:
            ai = get_ai_assistant()
            if ai:
                ai_result = ai.interpret_technological_analysis(
                    artifact_id,
                    tech_features,
                    tech_report
                )

                if ai_result.get('interpretation'):
                    ai_interpretation = ai_result
                else:
                    # Fallback to raw response if JSON parsing failed
                    ai_interpretation = ai_result.get('raw_response')
        except Exception as e:
            print(f"AI interpretation failed: {e}")
            ai_interpretation = None

        return jsonify({
            'status': 'success',
            'artifact_id': artifact_id,
            'technological_features': tech_features,
            'technical_report': tech_report,
            'ai_interpretation': ai_interpretation
        })

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@web_bp.route('/technological-analysis-page')
def technological_analysis_page():
    """Technological analysis visualization page."""
    return render_template('technological_analysis.html')


@web_bp.route('/technological-analysis-batch', methods=['POST'])
def technological_analysis_batch():
    """
    Perform batch technological analysis on multiple artifacts.

    Body (JSON):
    {
        "artifact_ids": ["axe001", "axe002", ...],  // Optional: if not provided, analyze ALL
        "format": "json"  // Optional: "json", "csv", "report"
    }
    """
    try:
        from acs.core.technological_analyzer import get_technological_analyzer

        data = request.json or {}
        artifact_ids = data.get('artifact_ids')
        output_format = data.get('format', 'json')

        # If no IDs specified, use all loaded artifacts
        if not artifact_ids:
            artifact_ids = list(mesh_processor.meshes.keys())

        if not artifact_ids:
            return jsonify({'error': 'No artifacts available for analysis'}), 400

        # Perform batch analysis
        tech_analyzer = get_technological_analyzer()
        batch_results = tech_analyzer.analyze_batch(mesh_processor.meshes, artifact_ids)

        # Return based on format
        if output_format == 'csv':
            csv_data = tech_analyzer.export_batch_csv(batch_results)
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=technological_analysis_batch.csv'
            return response

        elif output_format == 'report':
            report = tech_analyzer.generate_batch_report(batch_results)
            response = make_response(report)
            response.headers['Content-Type'] = 'text/plain'
            response.headers['Content-Disposition'] = 'attachment; filename=technological_analysis_batch.txt'
            return response

        else:  # json
            return jsonify({
                'status': 'success',
                'batch_results': batch_results
            })

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@web_bp.route('/generate-tech-report/<artifact_id>', methods=['POST'])
def generate_tech_report(artifact_id):
    """
    Generate comprehensive PDF report for single artifact with 3D renders.

    Body (JSON - optional):
    {
        "include_morphometric": true  // Include morphometric features
    }

    Returns:
        PDF file download
    """
    import time
    start_time = time.time()

    def log_timing(phase, elapsed):
        print(f"[PDF GEN] {artifact_id} - {phase}: {elapsed:.2f}s (total: {time.time() - start_time:.2f}s)")

    try:
        from acs.core.technological_analyzer import get_technological_analyzer
        from acs.core.report_generator import ReportGenerator
        from acs.core.ai_assistant import get_ai_assistant
        import os

        print(f"[PDF GEN] Starting PDF generation for {artifact_id}")

        # Check if artifact exists
        phase_start = time.time()
        if artifact_id not in mesh_processor.meshes:
            return jsonify({'error': f'Artifact {artifact_id} not found'}), 404

        mesh = mesh_processor.meshes[artifact_id]
        log_timing("Mesh loading", time.time() - phase_start)

        # Get technological analysis
        phase_start = time.time()
        tech_analyzer = get_technological_analyzer()
        tech_features = tech_analyzer.analyze_technology(mesh, artifact_id)
        tech_report = tech_analyzer.generate_technical_report(tech_features, artifact_id)
        log_timing("Technological analysis", time.time() - phase_start)

        # Get morphometric features if requested (do this before AI for optimization)
        data = request.json or {}
        morphometric_features = None
        if data.get('include_morphometric', True):
            phase_start = time.time()
            # Check if features are already cached
            if hasattr(mesh_processor, 'feature_cache') and artifact_id in mesh_processor.feature_cache:
                morphometric_features = mesh_processor.feature_cache[artifact_id]
                log_timing("Morphometric features (cached)", time.time() - phase_start)
            else:
                morphometric_features = mesh_processor._extract_features(mesh, artifact_id)
                # Cache for future use
                if not hasattr(mesh_processor, 'feature_cache'):
                    mesh_processor.feature_cache = {}
                mesh_processor.feature_cache[artifact_id] = morphometric_features
                log_timing("Morphometric features (computed)", time.time() - phase_start)

        # Get AI interpretation (structured JSON) - often the slowest part
        ai_interpretation = None
        try:
            phase_start = time.time()
            ai = get_ai_assistant()
            if ai:
                print(f"[PDF GEN] {artifact_id} - Calling AI API (this may take 5-30s)...")
                ai_interpretation = ai.interpret_technological_analysis(
                    artifact_id,
                    tech_features,
                    tech_report
                )
                log_timing("AI interpretation (API call)", time.time() - phase_start)
        except Exception as e:
            print(f"[PDF GEN] {artifact_id} - AI interpretation failed: {e}")

        # Generate PDF report with 3D renders
        phase_start = time.time()
        print(f"[PDF GEN] {artifact_id} - Generating PDF with 3D renders...")
        gen = ReportGenerator()
        pdf_path = gen.generate_technological_report(
            artifact_id,
            mesh,
            tech_features,
            tech_report,
            ai_interpretation,
            morphometric_features
        )
        log_timing("PDF generation (incl. 3D rendering)", time.time() - phase_start)

        total_time = time.time() - start_time
        print(f"[PDF GEN] {artifact_id} - ✅ Complete! Total time: {total_time:.2f}s")

        # Send file
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'tech_report_{artifact_id}.pdf'
        )

    except Exception as e:
        import traceback
        total_time = time.time() - start_time
        print(f"[PDF GEN] {artifact_id} - ❌ Failed after {total_time:.2f}s: {e}")
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@web_bp.route('/generate-batch-tech-report', methods=['POST'])
def generate_batch_tech_report():
    """
    Generate comprehensive PDF report for batch technological analysis.

    Body (JSON):
    {
        "artifact_ids": ["axe001", "axe002", ...],  // Optional: if not provided, use ALL
    }

    Returns:
        PDF file download
    """
    try:
        from acs.core.technological_analyzer import get_technological_analyzer
        from acs.core.report_generator import ReportGenerator
        from acs.core.ai_assistant import get_ai_assistant

        data = request.json or {}
        artifact_ids = data.get('artifact_ids')

        # If no IDs specified, use all loaded artifacts
        if not artifact_ids:
            artifact_ids = list(mesh_processor.meshes.keys())

        if not artifact_ids:
            return jsonify({'error': 'No artifacts available for analysis'}), 400

        # Perform batch analysis
        tech_analyzer = get_technological_analyzer()
        batch_results = tech_analyzer.analyze_batch(mesh_processor.meshes, artifact_ids)

        # Get AI batch interpretation
        ai_batch_interpretation = None
        try:
            ai = get_ai_assistant()
            if ai:
                # Get summary from batch_results
                summary_text = tech_analyzer.generate_batch_report(batch_results)
                ai_batch_interpretation = ai.interpret_batch_technological_analysis(
                    batch_results,
                    summary_text
                )
        except Exception as e:
            print(f"AI batch interpretation failed: {e}")

        # Prepare meshes dictionary for rendering
        artifact_meshes = {}
        for artifact_id in artifact_ids:
            if artifact_id in mesh_processor.meshes:
                artifact_meshes[artifact_id] = mesh_processor.meshes[artifact_id]

        # Generate PDF report
        gen = ReportGenerator()
        pdf_path = gen.generate_batch_technological_report(
            batch_results,
            artifact_meshes,
            ai_batch_interpretation
        )

        # Send file
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='batch_tech_report.pdf'
        )

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@web_bp.route('/technological-analysis-batch-page')
def technological_analysis_batch_page():
    """Batch technological analysis interface."""
    return render_template('technological_analysis_batch.html')


@web_bp.route('/artifacts-list', methods=['GET'])
def artifacts_list():
    """Get list of all loaded artifacts."""
    try:
        artifacts = []
        for artifact_id in mesh_processor.meshes.keys():
            artifacts.append({'id': artifact_id})

        return jsonify({
            'status': 'success',
            'artifacts': artifacts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@web_bp.route('/classify-management')
def classify_management_page():
    """Classification management page."""
    return render_template('classify_management.html')


@web_bp.route("/savignano-analysis")
def savignano_analysis_page():
    """Savignano Archaeological Analysis page."""
    return render_template("savignano_analysis.html")


@web_bp.route("/savignano-compare")
def savignano_compare_page():
    """Savignano Axes Comparison page."""
    return render_template("savignano_compare.html")


@web_bp.route("/savignano-drawings-test")
def savignano_drawings_test_page():
    """Savignano Technical Drawings Test page - Multilingual PDF Export."""
    return render_template("savignano_drawings_test.html")


@web_bp.route("/savignano-comprehensive-report")
def savignano_comprehensive_report_page():
    """Savignano Comprehensive Archaeological Report - Full Analysis with AI, PCA, Hammering, Casting."""
    return render_template("savignano_comprehensive_report.html")


@web_bp.route('/savignano-axes-list', methods=['GET'])
def get_savignano_axes_list():
    """Get list of all artifacts with Savignano features."""
    try:
        from acs.core.database import get_database

        db = get_database()
        all_artifacts = db.get_all_artifacts()

        # Include all artifacts, prioritize those with Savignano features
        savignano_axes = []
        for artifact in all_artifacts:
            artifact_id = artifact['artifact_id']

            # Get features from database
            features = db.get_features(artifact_id)

            # Include artifact even if no Savignano features (for UX)
            if features and 'savignano' in features:
                savignano_axes.append({
                    'artifact_id': artifact_id,
                    'peso': features['savignano'].get('peso', 0),
                    'incavo_presente': features['savignano'].get('incavo_presente', False),
                    'tagliente_forma': features['savignano'].get('tagliente_forma', 'unknown'),
                    'inventory_number': features['savignano'].get('inventory_number', artifact_id),
                    'has_savignano_features': True
                })
            else:
                # Include all artifacts from "Asce di Savignano" project or similar
                # Allow comparison even without full features
                category = artifact.get('category', '')
                description = artifact.get('description', '')

                # Include if likely a Savignano axe (category/description match)
                if 'axe' in category.lower() or 'ascia' in description.lower() or 'savignano' in description.lower():
                    savignano_axes.append({
                        'artifact_id': artifact_id,
                        'peso': 0,
                        'incavo_presente': None,
                        'tagliente_forma': 'unknown',
                        'inventory_number': artifact.get('inventory_number', artifact_id),
                        'has_savignano_features': False
                    })

        return jsonify({
            'status': 'success',
            'axes': savignano_axes,
            'count': len(savignano_axes)
        })

    except Exception as e:
        import logging
        logging.error(f"Error getting Savignano axes list: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@web_bp.route('/compare-savignano', methods=['POST'])
def compare_savignano_axes():
    """Compare two Savignano axes morphometric features."""
    try:
        from acs.core.database import get_database
        import numpy as np

        data = request.json
        axe1_id = data.get('axe1_id')
        axe2_id = data.get('axe2_id')

        if not axe1_id or not axe2_id:
            return jsonify({'error': 'Both axe IDs required'}), 400

        db = get_database()

        # Get features
        features1 = db.get_features(axe1_id)
        features2 = db.get_features(axe2_id)

        if not features1 or 'savignano' not in features1:
            return jsonify({
                'error': f'Axe "{axe1_id}" has no Savignano features',
                'message': f'Please analyze {axe1_id} using Savignano Analysis first.',
                'redirect_url': '/web/savignano-analysis'
            }), 404

        if not features2 or 'savignano' not in features2:
            return jsonify({
                'error': f'Axe "{axe2_id}" has no Savignano features',
                'message': f'Please analyze {axe2_id} using Savignano Analysis first.',
                'redirect_url': '/web/savignano-analysis'
            }), 404

        sav1 = features1['savignano']
        sav2 = features2['savignano']

        # Compare features
        feature_comparison = {}
        similarities = []

        # Numeric features to compare
        numeric_features = [
            'length', 'width', 'thickness', 'peso',
            'tallone_larghezza', 'tallone_spessore',
            'incavo_larghezza', 'incavo_profondita',
            'tagliente_larghezza', 'margini_rialzati_lunghezza',
            'margini_rialzati_spessore_max', 'larghezza_minima'
        ]

        for feature in numeric_features:
            val1 = sav1.get(feature, 0) or 0
            val2 = sav2.get(feature, 0) or 0

            if val1 == 0 and val2 == 0:
                continue

            max_val = max(abs(val1), abs(val2), 1e-10)
            diff = abs(val1 - val2) / max_val
            similarity = max(0, min(1, 1 - diff))

            feature_comparison[f'sav_{feature}'] = {
                'axe1': float(val1),
                'axe2': float(val2),
                'difference': float(diff),
                'similarity': float(similarity)
            }

            similarities.append(similarity)

        # Boolean features
        boolean_features = [
            'incavo_presente', 'margini_rialzati_presenti', 'tagliente_espanso'
        ]

        for feature in boolean_features:
            val1 = sav1.get(feature, False)
            val2 = sav2.get(feature, False)

            similarity = 1.0 if val1 == val2 else 0.0

            feature_comparison[f'sav_{feature}'] = {
                'axe1': val1,
                'axe2': val2,
                'similarity': similarity
            }

            similarities.append(similarity)

        # Overall similarity
        overall_similarity = float(np.mean(similarities)) if similarities else 0.0

        # AI interpretation (if enabled)
        ai_interpretation = None
        try:
            from acs.core.ai_assistant import AIClassificationAssistant

            ai = AIClassificationAssistant()
            ai_interpretation = _generate_comparison_interpretation(
                ai, axe1_id, axe2_id, sav1, sav2, overall_similarity
            )
        except Exception as e:
            import logging
            logging.warning(f"AI interpretation failed: {e}")

        return jsonify({
            'status': 'success',
            'axe1_id': axe1_id,
            'axe2_id': axe2_id,
            'overall_similarity': overall_similarity,
            'feature_comparison': feature_comparison,
            'ai_interpretation': ai_interpretation
        })

    except Exception as e:
        import logging
        logging.error(f"Error comparing Savignano axes: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def _generate_comparison_interpretation(ai, axe1_id, axe2_id, sav1, sav2, similarity):
    """Generate AI interpretation of Savignano axes comparison."""
    try:
        prompt = f"""You are an expert in Bronze Age archaeology specializing in axe typology.

Compare these two Bronze Age axes from Savignano:

**Axe {axe1_id}:**
- Weight: {sav1.get('peso', 'unknown')}g
- Tallone: {sav1.get('tallone_larghezza', 0):.1f}mm x {sav1.get('tallone_spessore', 0):.1f}mm
- Socket: {'Present' if sav1.get('incavo_presente') else 'Absent'} ({sav1.get('incavo_profilo', 'N/A')} profile)
- Raised edges: {'Present' if sav1.get('margini_rialzati_presenti') else 'Absent'}
- Blade: {sav1.get('tagliente_forma', 'unknown')} shape, {sav1.get('tagliente_larghezza', 0):.1f}mm

**Axe {axe2_id}:**
- Weight: {sav2.get('peso', 'unknown')}g
- Tallone: {sav2.get('tallone_larghezza', 0):.1f}mm x {sav2.get('tallone_spessore', 0):.1f}mm
- Socket: {'Present' if sav2.get('incavo_presente') else 'Absent'} ({sav2.get('incavo_profilo', 'N/A')} profile)
- Raised edges: {'Present' if sav2.get('margini_rialzati_presenti') else 'Absent'}
- Blade: {sav2.get('tagliente_forma', 'unknown')} shape, {sav2.get('tagliente_larghezza', 0):.1f}mm

**Morphometric Similarity:** {similarity * 100:.1f}%

Provide a concise archaeological interpretation (2-3 sentences):
1. Are these axes likely from the same casting matrix? Why or why not?
2. What do the similarities/differences tell us about production methods?
3. Any notable typological observations?

Be specific and cite the measurements."""

        response = ai.client.messages.create(
            model=ai.model,
            max_tokens=500,
            temperature=0.1,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return response.content[0].text

    except Exception as e:
        return None


@web_bp.route('/savignano-ai-interpretation/<artifact_id>', methods=['GET'])
def get_savignano_ai_interpretation(artifact_id):
    """Generate AI archaeological interpretation for a Savignano axe."""
    try:
        from acs.core.database import get_database
        from acs.core.ai_assistant import AIClassificationAssistant

        db = get_database()
        features = db.get_features(artifact_id)

        if not features or 'savignano' not in features:
            return jsonify({'error': 'No Savignano features found'}), 404

        sav = features['savignano']

        # Generate interpretation
        ai = AIClassificationAssistant()

        prompt = f"""You are an expert in Bronze Age archaeology specializing in Italian axe typology and the Savignano hoard.

Analyze this Bronze Age axe from Savignano (artifact {artifact_id}):

**Morphometric Features:**
- Weight: {sav.get('peso', 'unknown')}g
- Dimensions: L={sav.get('length', 0):.1f}mm, W={sav.get('width', 0):.1f}mm, T={sav.get('thickness', 0):.1f}mm
- Tallone (butt): {sav.get('tallone_larghezza', 0):.1f}mm x {sav.get('tallone_spessore', 0):.1f}mm
- Incavo (socket): {'Present' if sav.get('incavo_presente') else 'Absent'}
  {'  - Width: ' + str(sav.get('incavo_larghezza', 0)) + 'mm, Depth: ' + str(sav.get('incavo_profondita', 0)) + 'mm' if sav.get('incavo_presente') else ''}
  {'  - Profile: ' + sav.get('incavo_profilo', 'N/A') if sav.get('incavo_presente') else ''}
- Margini rialzati (raised edges): {'Present (' + str(sav.get('margini_rialzati_lunghezza', 0)) + 'mm)' if sav.get('margini_rialzati_presenti') else 'Absent'}
- Tagliente (blade): {sav.get('tagliente_forma', 'unknown')} shape, {sav.get('tagliente_larghezza', 0):.1f}mm wide
  {'  - Expanded: Yes' if sav.get('tagliente_espanso') else '  - Expanded: No'}
- Minimum body width: {sav.get('larghezza_minima', 0):.1f}mm

Provide a concise archaeological analysis (3-4 sentences):
1. What type of axe is this (socketed axe, flanged axe, palstave)?
2. Based on the morphometric features, what can you infer about the casting matrix and production method?
3. How does this axe compare to typical Bronze Age axes from Northern Italy?
4. Any notable features that indicate function, wear, or manufacturing technique?

Be specific and reference the actual measurements. Use proper archaeological terminology."""

        response = ai.client.messages.create(
            model=ai.model,
            max_tokens=600,
            temperature=0.1,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        interpretation = response.content[0].text

        return jsonify({
            'status': 'success',
            'artifact_id': artifact_id,
            'interpretation': interpretation,
            'model': ai.model
        })

    except Exception as e:
        import logging
        logging.error(f"Error generating Savignano AI interpretation: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

