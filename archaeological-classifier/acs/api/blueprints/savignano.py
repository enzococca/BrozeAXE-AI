"""
Savignano Blueprint
===================

Flask Blueprint per analisi archeologica asce Savignano.

Routes:
-------
- GET /api/savignano/status - Stato analisi
- POST /api/savignano/upload-batch - Upload batch meshes
- POST /api/savignano/configure - Configurazione parametri
- POST /api/savignano/run-analysis - Esegui workflow completo
- GET /api/savignano/results/<analysis_id> - Ottieni risultati
- GET /api/savignano/download/<analysis_id>/<file_type> - Download file

Autore: Archaeological Classifier System
Data: Novembre 2025
"""

from flask import Blueprint, request, jsonify, send_file, current_app
import os
import json
import logging
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
from werkzeug.utils import secure_filename
import numpy as np

# Import moduli Savignano
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from acs.savignano.morphometric_extractor import batch_extract_savignano_features
from acs.savignano.matrix_analyzer import MatrixAnalyzer
from acs.savignano.archaeological_qa import SavignanoArchaeologicalQA
from acs.core.config import get_config
from acs.core.database import get_database
import pandas as pd
import trimesh

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_to_json_serializable(obj):
    """
    Converte tipi NumPy/Pandas in tipi Python nativi per JSON serialization.

    Args:
        obj: Oggetto da convertire (dict, list, np.ndarray, np.bool_, etc.)

    Returns:
        Oggetto convertito in tipi JSON-serializable
    """
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_to_json_serializable(obj.tolist())
    elif pd.isna(obj):
        return None
    else:
        return obj

savignano_bp = Blueprint('savignano', __name__)

# Storage per sessioni analisi
ANALYSES = {}  # {analysis_id: {status, progress, results, paths}}


@savignano_bp.route('/status', methods=['GET'])
def get_status():
    """
    Ottiene stato sistema Savignano.

    Returns:
        JSON con:
        - analyses_count: Numero analisi attive
        - analyses: Lista analisi con stato
    """
    analyses_list = []

    for analysis_id, analysis_data in ANALYSES.items():
        analyses_list.append({
            'analysis_id': analysis_id,
            'status': analysis_data.get('status', 'unknown'),
            'progress': analysis_data.get('progress', 0),
            'created_at': analysis_data.get('created_at'),
            'n_axes': analysis_data.get('n_axes', 0)
        })

    return jsonify({
        'status': 'ok',
        'analyses_count': len(ANALYSES),
        'analyses': analyses_list
    })


@savignano_bp.route('/upload-batch', methods=['POST'])
def upload_batch():
    """
    Upload batch meshes per analisi Savignano.

    Expected:
        - files: List di file mesh (.obj, .stl, .ply)
        - Optional: weights_file (JSON con pesi)
        - Optional: weights_docx (DOCX note scansioni)

    Returns:
        JSON con:
        - analysis_id: ID univoco analisi
        - n_files_uploaded: Numero file caricati
        - files: Lista file caricati
    """
    try:
        # Verifica files
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')

        if len(files) == 0:
            return jsonify({'error': 'Empty file list'}), 400

        # Crea ID analisi e directory temporanea
        analysis_id = f"savignano_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir = Path(tempfile.mkdtemp(prefix=f'savignano_{analysis_id}_'))

        meshes_dir = temp_dir / 'meshes'
        meshes_dir.mkdir(exist_ok=True)

        # Salva meshes
        uploaded_files = []
        for file in files:
            if file.filename == '':
                continue

            # Verifica estensione
            filename = secure_filename(file.filename)
            if not filename.lower().endswith(('.obj', '.stl', '.ply')):
                continue

            file_path = meshes_dir / filename
            file.save(str(file_path))
            uploaded_files.append(filename)

        if len(uploaded_files) == 0:
            shutil.rmtree(temp_dir)
            return jsonify({'error': 'No valid mesh files uploaded'}), 400

        # Gestisci pesi opzionali
        weights_data = {}

        # Opzione 1: JSON pesi
        if 'weights_file' in request.files:
            weights_file = request.files['weights_file']
            if weights_file.filename != '':
                weights_path = temp_dir / 'weights.json'
                weights_file.save(str(weights_path))
                with open(weights_path, 'r') as f:
                    weights_data = json.load(f)
                logger.info(f"Loaded weights from JSON: {len(weights_data)} entries")

        # Opzione 2: DOCX note scansioni
        elif 'weights_docx' in request.files:
            weights_docx = request.files['weights_docx']
            if weights_docx.filename != '':
                docx_path = temp_dir / 'scan_notes.docx'
                weights_docx.save(str(docx_path))

                # Estrai pesi da DOCX
                try:
                    from savignano_complete_workflow import load_weights_from_docx
                    weights_data = load_weights_from_docx(str(docx_path))
                    logger.info(f"Extracted weights from DOCX: {len(weights_data)} entries")
                except Exception as e:
                    logger.warning(f"Could not extract weights from DOCX: {e}")

        # Inizializza analisi
        ANALYSES[analysis_id] = {
            'status': 'uploaded',
            'progress': 10,
            'created_at': datetime.now().isoformat(),
            'n_axes': len(uploaded_files),
            'files': uploaded_files,
            'paths': {
                'temp_dir': str(temp_dir),
                'meshes_dir': str(meshes_dir)
            },
            'weights_data': weights_data,
            'config': {}
        }

        logger.info(f"Created analysis {analysis_id} with {len(uploaded_files)} meshes")

        return jsonify({
            'status': 'success',
            'analysis_id': analysis_id,
            'n_files_uploaded': len(uploaded_files),
            'files': uploaded_files,
            'weights_loaded': len(weights_data) > 0
        })

    except Exception as e:
        logger.error(f"Error in upload_batch: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@savignano_bp.route('/configure', methods=['POST'])
def configure_analysis():
    """
    Configura parametri analisi Savignano.

    Expected JSON:
        {
            "analysis_id": "savignano_xxx",
            "config": {
                "clustering_method": "hierarchical" | "kmeans",
                "max_clusters": 15,
                "use_ai": true | false,
                "anthropic_api_key": "..." (optional)
            }
        }

    Returns:
        JSON con conferma configurazione
    """
    try:
        data = request.get_json()

        analysis_id = data.get('analysis_id')
        config = data.get('config', {})

        if not analysis_id or analysis_id not in ANALYSES:
            return jsonify({'error': 'Invalid analysis_id'}), 400

        # Aggiorna configurazione
        ANALYSES[analysis_id]['config'] = config
        ANALYSES[analysis_id]['status'] = 'configured'
        ANALYSES[analysis_id]['progress'] = 20

        logger.info(f"Configured analysis {analysis_id}: {config}")

        return jsonify({
            'status': 'success',
            'analysis_id': analysis_id,
            'config': config
        })

    except Exception as e:
        logger.error(f"Error in configure_analysis: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@savignano_bp.route('/run-analysis', methods=['POST'])
def run_analysis():
    """
    Esegue workflow completo Savignano.

    Expected JSON:
        {
            "analysis_id": "savignano_xxx"
        }

    Returns:
        JSON con conferma esecuzione
    """
    try:
        data = request.get_json()
        analysis_id = data.get('analysis_id')

        if not analysis_id or analysis_id not in ANALYSES:
            return jsonify({'error': 'Invalid analysis_id'}), 400

        analysis = ANALYSES[analysis_id]

        if analysis['status'] not in ['uploaded', 'configured']:
            return jsonify({'error': f"Cannot run analysis in status: {analysis['status']}"}), 400

        # Esegui analisi in background (per ora sincrono, poi async con Celery)
        analysis['status'] = 'running'
        analysis['progress'] = 30

        try:
            results = _execute_savignano_workflow(analysis_id)

            analysis['status'] = 'completed'
            analysis['progress'] = 100
            analysis['results'] = results
            analysis['completed_at'] = datetime.now().isoformat()

            logger.info(f"Analysis {analysis_id} completed successfully")

            # Save artifacts to main database for comparison
            try:
                _save_artifacts_to_database(analysis_id, analysis, results)
            except Exception as e:
                logger.warning(f"Failed to save artifacts to database: {e}")

            return jsonify({
                'status': 'success',
                'analysis_id': analysis_id,
                'results_summary': {
                    'n_matrices': results.get('n_matrices', 0),
                    'total_fusions': results.get('total_fusions', 0)
                }
            })

        except Exception as e:
            analysis['status'] = 'failed'
            analysis['error'] = str(e)
            analysis['failed_at'] = datetime.now().isoformat()
            logger.error(f"Analysis {analysis_id} failed: {e}", exc_info=True)
            raise

    except Exception as e:
        logger.error(f"Error in run_analysis: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@savignano_bp.route('/results/<analysis_id>', methods=['GET'])
def get_results(analysis_id):
    """
    Ottiene risultati analisi completata.

    Returns:
        JSON con tutti i risultati
    """
    try:
        if analysis_id not in ANALYSES:
            return jsonify({'error': 'Analysis not found'}), 404

        analysis = ANALYSES[analysis_id]

        if analysis['status'] != 'completed':
            return jsonify({
                'status': analysis['status'],
                'progress': analysis.get('progress', 0),
                'error': analysis.get('error')
            })

        # Ritorna risultati completi
        return jsonify({
            'status': 'success',
            'analysis_id': analysis_id,
            'created_at': analysis['created_at'],
            'completed_at': analysis.get('completed_at'),
            'results': analysis.get('results', {})
        })

    except Exception as e:
        logger.error(f"Error in get_results: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@savignano_bp.route('/download/<analysis_id>/<file_type>', methods=['GET'])
def download_file(analysis_id, file_type):
    """
    Download file risultati.

    Params:
        analysis_id: ID analisi
        file_type: 'features_csv', 'matrices_json', 'report_md', 'dendrogram_png', etc.

    Returns:
        File download
    """
    try:
        if analysis_id not in ANALYSES:
            return jsonify({'error': 'Analysis not found'}), 404

        analysis = ANALYSES[analysis_id]

        if analysis['status'] != 'completed':
            return jsonify({'error': 'Analysis not completed yet'}), 400

        # Mappa file types a paths
        output_dir = Path(analysis['paths']['output_dir'])

        file_map = {
            'features_csv': output_dir / 'features' / 'savignano_morphometric_features.csv',
            'features_json': output_dir / 'features' / 'savignano_morphometric_features.json',
            'matrices_json': output_dir / 'matrices' / 'matrices_summary.json',
            'matrix_assignments_csv': output_dir / 'matrices' / 'matrix_assignments.csv',
            'fusions_json': output_dir / 'matrices' / 'fusions_per_matrix.json',
            'report_md': output_dir / 'archaeological_qa' / 'SAVIGNANO_ARCHAEOLOGICAL_REPORT.md',
            'answers_json': output_dir / 'archaeological_qa' / 'archaeological_questions_answers.json',
            'dendrogram_png': output_dir / 'visualizations' / 'matrices_dendrogram.png',
            'pca_png': output_dir / 'visualizations' / 'matrices_pca_clusters.png',
            'summary_json': output_dir / 'ANALYSIS_SUMMARY.json',
            'readme_md': output_dir / 'README.md'
        }

        if file_type not in file_map:
            return jsonify({'error': f'Unknown file type: {file_type}'}), 400

        file_path = file_map[file_type]

        if not file_path.exists():
            return jsonify({'error': f'File not found: {file_path.name}'}), 404

        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=file_path.name
        )

    except Exception as e:
        logger.error(f"Error in download_file: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Helper Functions
# =============================================================================

def _execute_savignano_workflow(analysis_id):
    """
    Esegue workflow Savignano completo.

    Args:
        analysis_id: ID analisi

    Returns:
        Dict con risultati
    """
    analysis = ANALYSES[analysis_id]

    meshes_dir = analysis['paths']['meshes_dir']
    weights_data = analysis.get('weights_data', {})
    config = analysis.get('config', {})

    # Crea output directory
    temp_dir = Path(analysis['paths']['temp_dir'])
    output_dir = temp_dir / 'results'
    output_dir.mkdir(exist_ok=True)

    analysis['paths']['output_dir'] = str(output_dir)

    # Sottodirectory
    features_dir = output_dir / 'features'
    matrices_dir = output_dir / 'matrices'
    qa_dir = output_dir / 'archaeological_qa'
    viz_dir = output_dir / 'visualizations'

    for dir in [features_dir, matrices_dir, qa_dir, viz_dir]:
        dir.mkdir(exist_ok=True)

    logger.info(f"Executing workflow for analysis {analysis_id}")

    # STEP 1: Estrazione features
    logger.info("Step 1/4: Extracting morphometric features...")
    analysis['progress'] = 40

    features_list = batch_extract_savignano_features(
        meshes_dir,
        weights_dict=weights_data
    )

    features_df = pd.DataFrame(features_list)

    # Salva features
    features_csv = features_dir / 'savignano_morphometric_features.csv'
    features_df.to_csv(features_csv, index=False)

    features_json = features_dir / 'savignano_morphometric_features.json'
    with open(features_json, 'w') as f:
        # Converti tipi NumPy in tipi Python nativi per JSON
        json_serializable_features = convert_to_json_serializable(features_list)
        json.dump(json_serializable_features, f, indent=2)

    logger.info(f"Extracted features for {len(features_df)} axes")

    # STEP 2: Analisi matrici
    logger.info("Step 2/4: Identifying matrices...")
    analysis['progress'] = 60

    matrix_analyzer = MatrixAnalyzer(features_df)

    matrices_result = matrix_analyzer.identify_matrices(
        method=config.get('clustering_method', 'hierarchical'),
        max_clusters=config.get('max_clusters', 15)
    )

    # Salva matrici
    matrices_json = matrices_dir / 'matrices_summary.json'
    with open(matrices_json, 'w') as f:
        json.dump(convert_to_json_serializable(matrix_analyzer.matrices), f, indent=2)

    assignments_df = matrix_analyzer.get_matrix_assignments()
    assignments_csv = matrices_dir / 'matrix_assignments.csv'
    assignments_df.to_csv(assignments_csv, index=False)

    # STEP 3: Fusioni
    logger.info("Step 3/4: Estimating fusions...")
    analysis['progress'] = 70

    fusions_result = matrix_analyzer.estimate_fusions_per_matrix()

    fusions_json = matrices_dir / 'fusions_per_matrix.json'
    with open(fusions_json, 'w') as f:
        json.dump(convert_to_json_serializable(fusions_result), f, indent=2)

    # STEP 4: Domande archeologiche
    logger.info("Step 4/4: Generating archaeological analysis...")
    analysis['progress'] = 85

    use_ai = config.get('use_ai', False)
    # Usa API key globale se configurata
    config_manager = get_config()
    api_key = config_manager.get_api_key() or os.getenv('ANTHROPIC_API_KEY')

    qa_analyzer = SavignanoArchaeologicalQA(
        matrices_info=matrix_analyzer.matrices,
        features_df=features_df,
        tech_analysis_df=None,
        anthropic_api_key=api_key if use_ai else None
    )

    qa_results = qa_analyzer.answer_all_questions()

    # Salva risposte
    qa_json = qa_dir / 'archaeological_questions_answers.json'
    with open(qa_json, 'w', encoding='utf-8') as f:
        json.dump(convert_to_json_serializable(qa_results), f, indent=2, ensure_ascii=False)

    # Genera report
    report_md = qa_dir / 'SAVIGNANO_ARCHAEOLOGICAL_REPORT.md'
    qa_analyzer.generate_report(str(report_md), format='markdown')

    # STEP 5: Visualizzazioni
    logger.info("Generating visualizations...")
    analysis['progress'] = 95

    try:
        dendrogram_path = viz_dir / 'matrices_dendrogram.png'
        matrix_analyzer.plot_dendrogram(str(dendrogram_path))

        pca_path = viz_dir / 'matrices_pca_clusters.png'
        matrix_analyzer.plot_pca_clusters(str(pca_path))
    except Exception as e:
        logger.warning(f"Could not generate visualizations: {e}")

    # Summary
    summary = {
        'analysis_id': analysis_id,
        'analysis_date': datetime.now().isoformat(),
        'n_axes_analyzed': len(features_df),
        'n_matrices_identified': matrices_result['n_matrices'],
        'total_fusions_estimated': fusions_result['total_fusions'],
        'silhouette_score': matrices_result['silhouette_score'],
        'davies_bouldin_score': matrices_result['davies_bouldin_score'],
        'ai_analysis_used': use_ai
    }

    summary_json = output_dir / 'ANALYSIS_SUMMARY.json'
    with open(summary_json, 'w') as f:
        json.dump(convert_to_json_serializable(summary), f, indent=2)

    logger.info(f"Workflow completed for analysis {analysis_id}")

    return {
        'n_matrices': matrices_result['n_matrices'],
        'total_fusions': fusions_result['total_fusions'],
        'silhouette_score': matrices_result['silhouette_score'],
        'summary': summary
    }


def _save_artifacts_to_database(analysis_id: str, analysis: dict, results: dict):
    """
    Salva gli artifacts Savignano nel database principale per renderli disponibili
    nella comparazione e nel 3D viewer.

    Args:
        analysis_id: ID dell'analisi
        analysis: Dict con info analisi (paths, files, etc.)
        results: Risultati dell'analisi
    """
    logger.info(f"Saving {len(analysis['files'])} artifacts to main database...")

    db = get_database()
    output_dir = Path(analysis['paths']['output_dir'])
    meshes_dir = Path(analysis['paths']['meshes_dir'])

    # Load features DataFrame
    features_csv = output_dir / 'features' / 'savignano_features.csv'
    if not features_csv.exists():
        logger.warning(f"Features file not found: {features_csv}")
        return

    features_df = pd.read_csv(features_csv)

    # Permanent mesh storage directory
    permanent_mesh_dir = Path(os.path.expanduser('~/.acs/savignano_meshes'))
    permanent_mesh_dir.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    for _, row in features_df.iterrows():
        artifact_id = row['artifact_id']

        # Find mesh file in temp directory
        mesh_file = None
        for ext in ['.obj', '.stl', '.ply']:
            temp_mesh = meshes_dir / f"{artifact_id}{ext}"
            if temp_mesh.exists():
                mesh_file = temp_mesh
                break

        if not mesh_file:
            logger.warning(f"Mesh file not found for {artifact_id}")
            continue

        # Copy mesh to permanent location
        permanent_mesh = permanent_mesh_dir / mesh_file.name
        shutil.copy2(mesh_file, permanent_mesh)

        # Load mesh for metadata
        try:
            mesh = trimesh.load(str(permanent_mesh))
            n_vertices = len(mesh.vertices)
            n_faces = len(mesh.faces)
        except Exception as e:
            logger.warning(f"Failed to load mesh {artifact_id}: {e}")
            n_vertices = 0
            n_faces = 0

        # Create artifact in database
        artifact_data = {
            'artifact_id': artifact_id,
            'inventory_number': row.get('inventory_number', artifact_id),
            'description': f"Savignano axe - {analysis_id}",
            'category': 'Bronze Age Axe',
            'material': 'Bronze',
            'dimensions': {
                'lunghezza_totale': float(row.get('lunghezza_totale', 0)),
                'larghezza_tagliente': float(row.get('larghezza_tagliente', 0)),
                'larghezza_tallone': float(row.get('larghezza_tallone', 0))
            },
            'mesh_path': str(permanent_mesh),
            'mesh_stats': {
                'vertices': n_vertices,
                'faces': n_faces
            }
        }

        # Add artifact to database (will update if exists)
        db.add_artifact(artifact_data)

        # Save Savignano features
        savignano_features = row.to_dict()
        db.save_features(artifact_id, {'savignano': savignano_features})

        saved_count += 1
        logger.info(f"Saved artifact {artifact_id} to database")

    logger.info(f"Successfully saved {saved_count}/{len(features_df)} artifacts to main database")
    logger.info(f"Successfully saved {saved_count}/{len(features_df)} artifacts to main database")


@savignano_bp.route('/generate-drawings/<artifact_id>', methods=['POST'])
def generate_drawings(artifact_id: str):
    """
    Generate technical drawings for a Savignano artifact.

    URL Parameters:
        artifact_id: Artifact identifier

    Body Parameters (JSON):
        language: Language for labels ('it', 'en') - default 'it'
        export_pdf: Export to PDF (default True)
        include_png: Include individual PNG files (default True)

    Returns:
        JSON with:
        - status: 'success' or 'error'
        - drawings: Dict with paths to generated files
        - message: Status message
    """
    try:
        from acs.savignano.technical_drawings import generate_technical_drawings

        # Get parameters
        data = request.get_json() or {}
        language = data.get('language', 'it')
        export_pdf = data.get('export_pdf', True)
        include_png = data.get('include_png', True)

        # Validate language
        if language not in ['it', 'en']:
            return jsonify({
                'status': 'error',
                'error': f'Unsupported language: {language}. Use "it" or "en".'
            }), 400

        # Get artifact from database
        db = get_database()
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({
                'status': 'error',
                'error': f'Artifact {artifact_id} not found'
            }), 404

        # Get mesh path
        mesh_path = artifact.get('mesh_path')
        if not mesh_path or not Path(mesh_path).exists():
            return jsonify({
                'status': 'error',
                'error': f'Mesh file not found for artifact {artifact_id}'
            }), 404

        # Get Savignano features
        features = db.get_features(artifact_id)
        savignano_features = features.get('savignano', {}) if features else {}

        if not savignano_features:
            return jsonify({
                'status': 'error',
                'error': f'No Savignano features available for artifact {artifact_id}. Run Savignano analysis first.'
            }), 400

        # Create output directory
        output_dir = Path.home() / '.acs' / 'drawings' / artifact_id
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating technical drawings for {artifact_id} in {language}")

        # Generate drawings
        results = generate_technical_drawings(
            mesh_path=mesh_path,
            features=savignano_features,
            output_dir=str(output_dir),
            artifact_id=artifact_id,
            language=language,
            export_pdf=export_pdf
        )

        # Remove PNG files if not requested
        if not include_png and 'pdf' in results:
            for key in ['front', 'profile', 'sections']:
                if key in results:
                    try:
                        Path(results[key]).unlink()
                        del results[key]
                    except Exception as e:
                        logger.warning(f"Failed to delete {key} PNG: {e}")

        # Update artifact metadata with drawing paths
        artifact_metadata = artifact.get('metadata', '{}')
        # Parse JSON string if needed
        if isinstance(artifact_metadata, str):
            try:
                artifact_metadata = json.loads(artifact_metadata) if artifact_metadata else {}
            except json.JSONDecodeError:
                artifact_metadata = {}

        artifact_metadata['technical_drawings'] = results
        artifact_metadata['drawings_language'] = language
        artifact_metadata['drawings_generated'] = datetime.now().isoformat()

        # Update metadata in database using direct SQL
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE artifacts SET metadata = ? WHERE artifact_id = ?',
                (json.dumps(artifact_metadata), artifact_id)
            )

        logger.info(f"Technical drawings generated successfully for {artifact_id}")

        return jsonify({
            'status': 'success',
            'drawings': results,
            'language': language,
            'message': f'Technical drawings generated in {language.upper()}'
        })

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return jsonify({
            'status': 'error',
            'error': f'Technical drawings module not available: {str(e)}'
        }), 500

    except Exception as e:
        logger.error(f"Error generating technical drawings: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'artifact_id': artifact_id
        }), 500


@savignano_bp.route('/download-drawing/<artifact_id>/<file_type>', methods=['GET'])
def download_drawing(artifact_id: str, file_type: str):
    """
    Download a technical drawing file.

    URL Parameters:
        artifact_id: Artifact identifier
        file_type: Type of file ('pdf', 'front', 'profile', 'sections')

    Query Parameters:
        language: Language version ('it', 'en') - default uses last generated

    Returns:
        File download
    """
    try:
        language = request.args.get('language', 'it')

        # Get artifact
        db = get_database()
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({'error': f'Artifact {artifact_id} not found'}), 404

        # Get drawing paths from metadata
        metadata = artifact.get('metadata', '{}')
        # Parse JSON string if needed
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata) if metadata else {}
            except json.JSONDecodeError:
                metadata = {}
        drawings = metadata.get('technical_drawings', {})

        if not drawings:
            return jsonify({
                'error': f'No technical drawings available for {artifact_id}. Generate them first.'
            }), 404

        # Get requested file
        file_path = drawings.get(file_type)
        if not file_path or not Path(file_path).exists():
            return jsonify({
                'error': f'Drawing type "{file_type}" not found for {artifact_id}'
            }), 404

        # Determine MIME type
        mime_types = {
            'pdf': 'application/pdf',
            'front': 'image/png',
            'profile': 'image/png',
            'sections': 'image/png'
        }

        mime_type = mime_types.get(file_type, 'application/octet-stream')

        # Send file
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=f"{artifact_id}_{file_type}_{language}.{'pdf' if file_type == 'pdf' else 'png'}"
        )

    except Exception as e:
        logger.error(f"Error downloading drawing: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@savignano_bp.route('/supported-languages', methods=['GET'])
def get_supported_languages():
    """
    Get list of supported languages for technical drawings.

    Returns:
        JSON with supported language codes and names
    """
    return jsonify({
        'status': 'success',
        'languages': {
            'it': 'Italiano',
            'en': 'English'
        },
        'default': 'it'
    })


@savignano_bp.route('/generate-comprehensive-report/<artifact_id>', methods=['POST'])
def generate_comprehensive_report(artifact_id: str):
    """
    Generate comprehensive archaeological report with:
    - Realistic 3D mesh renderings
    - Complete measurements table
    - AI interpretation
    - Hammering analysis
    - Casting analysis
    - PCA and clustering
    - Comparative analysis

    Request body:
        {
            "language": "it" or "en" (default: "it")
        }

    Returns:
        JSON with report generation status and file paths
    """
    try:
        data = request.get_json() or {}
        language = data.get('language', 'it')

        # Validate language
        if language not in ['it', 'en']:
            return jsonify({
                'status': 'error',
                'error': f'Unsupported language: {language}. Use "it" or "en"'
            }), 400

        # Get artifact from database
        db = get_database()
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({
                'status': 'error',
                'error': f'Artifact {artifact_id} not found'
            }), 404

        # Get mesh path
        mesh_path = artifact.get('mesh_path')
        if not mesh_path or not Path(mesh_path).exists():
            return jsonify({
                'status': 'error',
                'error': f'Mesh file not found for artifact {artifact_id}'
            }), 404

        # ALWAYS re-extract features to ensure latest measurements with corrected code
        from acs.savignano.morphometric_extractor import extract_savignano_features
        logger.info(f"Re-extracting Savignano features for {artifact_id} with latest code")
        savignano_features = extract_savignano_features(Path(mesh_path), artifact_id)

        # Create output directory
        output_dir = Path.home() / '.acs' / 'reports' / artifact_id
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating comprehensive report for {artifact_id} in {language}")

        # Import comprehensive report generator
        from acs.savignano.comprehensive_report import generate_comprehensive_report as gen_report

        # Generate report
        results = gen_report(
            mesh_path=mesh_path,
            features=savignano_features,
            output_dir=str(output_dir),
            artifact_id=artifact_id,
            language=language
        )

        # Update artifact metadata with report path
        metadata = artifact.get('metadata', '{}')
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata) if metadata else {}
            except json.JSONDecodeError:
                metadata = {}

        metadata['comprehensive_report'] = results
        metadata['report_language'] = language
        metadata['report_generated'] = datetime.now().isoformat()

        # Update metadata in database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE artifacts SET metadata = ? WHERE artifact_id = ?',
                (json.dumps(metadata), artifact_id)
            )

        logger.info(f"Comprehensive report generated successfully for {artifact_id}")

        return jsonify({
            'status': 'success',
            'report': results,
            'language': language,
            'message': f'Comprehensive archaeological report generated in {language.upper()}'
        })

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return jsonify({
            'status': 'error',
            'error': f'Comprehensive report module not available: {str(e)}'
        }), 500

    except Exception as e:
        logger.error(f"Error generating comprehensive report: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'artifact_id': artifact_id
        }), 500


@savignano_bp.route('/generate-comprehensive-report-stream/<artifact_id>', methods=['GET'])
def generate_comprehensive_report_stream(artifact_id: str):
    """
    Generate comprehensive report with real-time streaming logs via Server-Sent Events.

    Query parameters:
        language: Report language ('it' or 'en', default: 'it')

    Returns:
        Server-Sent Events stream with progress updates
    """
    language = request.args.get('language', 'it')

    def generate():
        import sys
        from io import StringIO

        try:
            # Send initial log
            yield f"data: {json.dumps({'type': 'log', 'message': 'Inizio generazione report...', 'level': 'info'})}\n\n"

            # Validate language
            if language not in ['it', 'en']:
                yield f"data: {json.dumps({'type': 'error', 'message': f'Lingua non supportata: {language}'})}\n\n"
                return

            # Get artifact from database
            yield f"data: {json.dumps({'type': 'log', 'message': f'Caricamento artefatto {artifact_id}...', 'level': 'info'})}\n\n"

            db = get_database()
            artifact = db.get_artifact(artifact_id)

            if not artifact:
                yield f"data: {json.dumps({'type': 'error', 'message': f'Artefatto {artifact_id} non trovato'})}\n\n"
                return

            # Get mesh path
            mesh_path = artifact.get('mesh_path')
            if not mesh_path or not Path(mesh_path).exists():
                yield f"data: {json.dumps({'type': 'error', 'message': f'File mesh non trovato per {artifact_id}'})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'log', 'message': f'Mesh trovato: {Path(mesh_path).name}', 'level': 'success'})}\n\n"

            # Extract features
            yield f"data: {json.dumps({'type': 'log', 'message': 'Estrazione features morfometriche...', 'level': 'info'})}\n\n"

            from acs.savignano.morphometric_extractor import extract_savignano_features
            savignano_features = extract_savignano_features(Path(mesh_path), artifact_id)

            yield f"data: {json.dumps({'type': 'log', 'message': '✓ Features estratte con successo', 'level': 'success'})}\n\n"

            # Create output directory
            output_dir = Path.home() / '.acs' / 'reports' / artifact_id
            output_dir.mkdir(parents=True, exist_ok=True)

            yield f"data: {json.dumps({'type': 'log', 'message': 'Directory output creata', 'level': 'info'})}\n\n"

            # Generate report with logging
            yield f"data: {json.dumps({'type': 'log', 'message': 'Generazione PDF in corso...', 'level': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '  Pagina 1: Copertina e morfometria', 'level': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '  Pagina 2: Disegni tecnici', 'level': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '  Pagina 3: Interpretazione AI', 'level': 'info'})}\n\n"

            # Create generator instance to access analysis methods
            from acs.savignano.comprehensive_report import SavignanoComprehensiveReport
            generator = SavignanoComprehensiveReport(mesh_path, savignano_features, artifact_id, language)

            # Stream REAL hammering analysis data
            yield f"data: {json.dumps({'type': 'log', 'message': '  Pagina 4+: Analisi martellatura', 'level': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '    → Calcolo rugosità superficiale...', 'level': 'info'})}\n\n"

            hammer_analysis = generator._analyze_hammering()
            # Stream the actual hammering analysis line by line
            for line in hammer_analysis.split('\n')[:10]:  # First 10 lines
                if line.strip():
                    yield f"data: {json.dumps({'type': 'log', 'message': f'      {line[:80]}', 'level': 'success'})}\n\n"

            yield f"data: {json.dumps({'type': 'log', 'message': f'    → Totale: {len(hammer_analysis.split(chr(10)))} righe generate', 'level': 'info'})}\n\n"

            # Stream REAL casting analysis data
            yield f"data: {json.dumps({'type': 'log', 'message': '  Analisi fusione', 'level': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '    → Calcolo simmetria e qualità...', 'level': 'info'})}\n\n"

            casting_analysis = generator._analyze_casting()
            # Stream the actual casting analysis line by line
            for line in casting_analysis.split('\n')[:10]:  # First 10 lines
                if line.strip():
                    yield f"data: {json.dumps({'type': 'log', 'message': f'      {line[:80]}', 'level': 'success'})}\n\n"

            yield f"data: {json.dumps({'type': 'log', 'message': f'    → Totale: {len(casting_analysis.split(chr(10)))} righe generate', 'level': 'info'})}\n\n"

            yield f"data: {json.dumps({'type': 'log', 'message': '  Analisi PCA e clustering', 'level': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '  Analisi comparativa', 'level': 'info'})}\n\n"

            # Now generate the complete PDF
            pdf_path = output_dir / f"{artifact_id}_comprehensive_report_{language}.pdf"
            results = generator.generate_complete_report(str(pdf_path))

            # Update artifact metadata
            metadata = artifact.get('metadata', '{}')
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata) if metadata else {}
                except json.JSONDecodeError:
                    metadata = {}

            metadata['comprehensive_report'] = results
            metadata['report_language'] = language
            metadata['report_generated'] = datetime.now().isoformat()

            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE artifacts SET metadata = ? WHERE artifact_id = ?',
                    (json.dumps(metadata), artifact_id)
                )

            yield f"data: {json.dumps({'type': 'log', 'message': '✅ Report completato!', 'level': 'success'})}\n\n"

            # Send completion message
            yield f"data: {json.dumps({'type': 'complete', 'pdf_path': results.get('pdf', '')})}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming report generation: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return current_app.response_class(generate(), mimetype='text/event-stream')
@savignano_bp.route('/download-comprehensive-report/<artifact_id>', methods=['GET'])
def download_comprehensive_report(artifact_id: str):
    """
    Download comprehensive archaeological report PDF.

    Query parameters:
        language: Report language ('it' or 'en', default: 'it')

    Returns:
        PDF file download
    """
    try:
        language = request.args.get('language', 'it')

        # Get artifact
        db = get_database()
        artifact = db.get_artifact(artifact_id)

        if not artifact:
            return jsonify({'error': f'Artifact {artifact_id} not found'}), 404

        # Get report path from metadata
        metadata = artifact.get('metadata', '{}')
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata) if metadata else {}
            except json.JSONDecodeError:
                metadata = {}

        comprehensive_report = metadata.get('comprehensive_report', {})

        if not comprehensive_report:
            return jsonify({
                'error': f'No comprehensive report available for {artifact_id}. Generate it first.'
            }), 404

        # Get PDF file path
        pdf_path = comprehensive_report.get('pdf')
        if not pdf_path or not Path(pdf_path).exists():
            return jsonify({
                'error': f'Report PDF not found for {artifact_id}'
            }), 404

        # Send file
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{artifact_id}_comprehensive_report_{language}.pdf"
        )

    except Exception as e:
        logger.error(f"Error downloading comprehensive report: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
