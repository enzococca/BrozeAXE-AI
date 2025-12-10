# BrozeAXE-AI: Complete Workflow TODO List

**Data Analisi:** 2025-11-24
**Branch:** claude/fix-pdf-data-display-01KpmDJmg8a947EZXRYN1xPV

---

## 📋 EXECUTIVE SUMMARY

### ✅ Cosa Funziona Bene
- ✅ Estrazione features completa (36+ parametri Savignano)
- ✅ Database SQLite ben strutturato con relazioni
- ✅ Batch processing di file 3D (singolo e multiplo)
- ✅ Sistema di tassonomia formale con versioning
- ✅ Doppio pipeline AI/ML (Claude 4.5 + sklearn)
- ✅ Generazione report PDF professionali
- ✅ Project management a livello database

### ❌ Problemi Critici Identificati
- ❌ **Nessuna autenticazione** - sistema completamente aperto
- ❌ **Mesh in memoria** - persi al restart del server
- ❌ **Due Flask app separate** - duplicazione e confusione
- ❌ **Processing sincrono** - blocca le richieste HTTP
- ❌ **Vulnerabilità sicurezza** - CORS aperto, file upload non validati
- ❌ **UI incompleta** - project management solo nel DB
- ❌ **No versioning ML models** - solo un modello alla volta

---

## 🎯 PRIORITÀ 1: SICUREZZA E STABILITÀ (SETTIMANA 1-2)

### 1.1 Autenticazione e Autorizzazione ⚠️ CRITICO
**Perché:** Sistema completamente aperto, chiunque può caricare/cancellare dati

**Task:**
- [ ] Implementare JWT authentication per API
- [ ] Aggiungere session-based auth per web interface
- [ ] Creare tabella `users` nel database con ruoli (admin, archaeologist, viewer)
- [ ] Proteggere tutti gli endpoint con decorators `@login_required`
- [ ] Aggiungere endpoint `/api/auth/login`, `/api/auth/logout`, `/api/auth/register`
- [ ] Implementare password hashing con bcrypt
- [ ] Aggiungere ruoli e permessi:
  - Admin: tutto
  - Archaeologist: upload, classify, validate
  - Viewer: solo visualizzazione

**Files da modificare:**
- `acs/api/app.py` - setup auth middleware
- `acs/api/blueprints/auth.py` - nuovo blueprint
- `acs/core/database.py` - aggiungere tabella users
- `acs/web/routes.py` - aggiungere session management

**Testing:**
```bash
# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "archaeologist1", "password": "secure123"}'

# Test protected endpoint
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/mesh/upload
```

---

### 1.2 Sicurezza File Upload ⚠️ CRITICO
**Perché:** Vulnerabile a file maliciosi, DoS, file bomb

**Task:**
- [ ] Aggiungere validazione content-type (non solo estensione)
- [ ] Implementare limite dimensione file per endpoint:
  - Web upload: 100 MB per file
  - API upload: 500 MB per file
  - Batch: 2 GB totale
- [ ] Aggiungere scanning basic (magic bytes check)
- [ ] Validare mesh integrity con trimesh prima di salvare
- [ ] Sanitize filename (rimuovere path traversal: `../`, `./`)
- [ ] Aggiungere rate limiting (max 10 upload/minuto per utente)
- [ ] Implementare virus scanning con ClamAV (opzionale)

**Files da modificare:**
- `acs/api/blueprints/mesh.py` - upload endpoints (linee 27-125)
- `acs/api/blueprints/savignano.py` - upload-batch (linee 108-216)
- Nuovo file: `acs/core/file_validator.py`

**Codice esempio:**
```python
# acs/core/file_validator.py
import magic
from werkzeug.utils import secure_filename

class FileValidator:
    MAX_SIZE = 100 * 1024 * 1024  # 100 MB
    ALLOWED_MIME = ['model/obj', 'model/stl', 'model/ply']

    @staticmethod
    def validate_upload(file):
        # Check size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset
        if size > FileValidator.MAX_SIZE:
            raise ValueError(f"File too large: {size} bytes")

        # Check magic bytes
        mime = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)
        if mime not in FileValidator.ALLOWED_MIME:
            raise ValueError(f"Invalid file type: {mime}")

        # Sanitize filename
        filename = secure_filename(file.filename)
        return filename
```

---

### 1.3 Fix Configurazione Sicurezza ⚠️ CRITICO
**Perché:** CORS aperto a tutti, API keys in plaintext, path prevedibili

**Task:**
- [ ] **CORS:** Configurare allowed origins specifici (non `*`)
- [ ] **API Keys:** Migrare da JSON plaintext a system keychain:
  - macOS: Keychain Access
  - Linux: Secret Service API (libsecret)
  - Windows: Credential Manager
- [ ] **Config Management:** Unificare in un solo file `config.py`
- [ ] **Environment Variables:** Usare `.env` file per development
- [ ] **Secrets:** Usare variabili d'ambiente per production
- [ ] **Debug Mode:** Disabilitare in production (`app.debug = False`)

**Files da modificare:**
- `acs/api/app.py` linea 46 - CORS config
- `acs/core/config_manager.py` - aggiungere keychain support
- Nuovo file: `.env.example` - template per configurazione

**Esempio CORS:**
```python
# acs/api/app.py
from flask_cors import CORS

# PRIMA (insicuro):
CORS(app)

# DOPO (sicuro):
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",  # React dev server
            "https://brozeaxe.example.com"  # Production domain
        ],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

### 1.4 Error Handling Robusto
**Perché:** Molti failure modes non gestiti, server crash possibili

**Task:**
- [ ] Aggiungere try-except globale in app con logging
- [ ] Gestire specificamente:
  - `MeshLoadError` - file 3D corrotto
  - `DatabaseError` - connessione DB fallita
  - `AIError` - API Anthropic fallita
  - `ValidationError` - dati invalidi
- [ ] Implementare retry logic per operazioni transient (DB, API)
- [ ] Aggiungere circuit breaker per API esterne
- [ ] Logging strutturato (JSON) con livelli appropriati
- [ ] Error responses standardizzati:
```json
{
  "error": "MeshLoadError",
  "message": "Failed to load mesh: file corrupted",
  "details": "Invalid vertex count",
  "timestamp": "2025-11-24T10:30:00Z"
}
```

**Files da modificare:**
- `acs/core/mesh_processor.py` - aggiungere MeshLoadError
- `acs/api/app.py` - error handlers globali
- Nuovo file: `acs/core/exceptions.py` - custom exceptions

---

## 🚀 PRIORITÀ 2: ARCHITETTURA E PERFORMANCE (SETTIMANA 2-3)

### 2.1 Unificare Flask Apps ⚡ IMPORTANTE
**Perché:** Due app separate creano confusione, duplicazione codice

**Task:**
- [ ] Merge `app.py` (web simple) in `acs/api/app.py`
- [ ] Riorganizzare blueprints:
  - `/api/*` - REST API endpoints
  - `/web/*` - Web interface (HTML templates)
  - `/` - Landing page
- [ ] Unificare configurazione in un solo `config.py`
- [ ] Migrare routes da `app.py` a `acs/web/routes.py`
- [ ] Eliminare `app.py` dopo merge completo

**Struttura target:**
```
acs/
  api/
    app.py              # Main application (UNICA)
    blueprints/
      api/              # REST API
        mesh.py
        classification.py
        morphometric.py
        savignano.py
      web/              # Web interface
        artifacts.py    # Artifact viewing
        projects.py     # Project management
        statistics.py   # Statistics dashboard
        admin.py        # Admin panel
```

**Files da eliminare:**
- `/home/user/BrozeAXE-AI/app.py` ❌ DELETE

**Migration plan:**
1. Copiare routes da `app.py` in `acs/web/routes.py`
2. Testare che tutto funziona
3. Aggiornare README con nuovo comando start
4. Eliminare `app.py`

---

### 2.2 Async Task Processing ⚡ IMPORTANTE
**Perché:** Workflow Savignano blocca richieste HTTP per minuti

**Task:**
- [ ] Installare Celery + Redis (o RabbitMQ)
- [ ] Creare Celery app in `acs/core/celery_app.py`
- [ ] Convertire operazioni lunghe in tasks:
  - `@celery.task` per comprehensive report generation
  - `@celery.task` per batch processing
  - `@celery.task` per PCA/clustering computation
  - `@celery.task` per ML model training
- [ ] Aggiungere tabella `tasks` nel DB per tracking:
```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    task_type TEXT,  -- 'report', 'batch', 'training', etc.
    status TEXT,     -- 'pending', 'running', 'completed', 'failed'
    progress REAL,   -- 0.0 to 1.0
    result_json TEXT,
    error_message TEXT,
    created_at TEXT,
    completed_at TEXT
)
```
- [ ] Aggiungere endpoints per task monitoring:
  - `GET /api/tasks/<task_id>` - get status
  - `GET /api/tasks/<task_id>/cancel` - cancel task
  - `GET /api/tasks/list` - list user tasks
- [ ] Implementare progress tracking con Celery signals

**Example:**
```python
# acs/core/celery_app.py
from celery import Celery

celery = Celery('brozeaxe',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0')

# acs/savignano/tasks.py
from acs.core.celery_app import celery
from acs.savignano.comprehensive_report import SavignanoComprehensiveReport

@celery.task(bind=True)
def generate_comprehensive_report_task(self, artifact_id, ai_api_key=None):
    """Async task for report generation."""
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0.1})

        report = SavignanoComprehensiveReport(artifact_id, ai_api_key)

        self.update_state(state='PROGRESS', meta={'progress': 0.5})

        pdf_path = report.generate_complete_report()

        return {'status': 'completed', 'pdf_path': pdf_path}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}

# acs/api/blueprints/savignano.py
@savignano_bp.route('/generate-report-async/<artifact_id>', methods=['POST'])
def generate_report_async(artifact_id):
    task = generate_comprehensive_report_task.delay(artifact_id)
    return jsonify({'task_id': task.id, 'status': 'pending'})

@savignano_bp.route('/task-status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = generate_comprehensive_report_task.AsyncResult(task_id)
    if task.state == 'PROGRESS':
        return jsonify({'status': 'running', 'progress': task.info.get('progress')})
    elif task.state == 'SUCCESS':
        return jsonify({'status': 'completed', 'result': task.result})
    else:
        return jsonify({'status': task.state})
```

**Setup:**
```bash
# Install
pip install celery redis

# Start Redis
redis-server

# Start Celery worker
celery -A acs.core.celery_app worker --loglevel=info
```

---

### 2.3 Mesh Lazy Loading Strategy ⚡ IMPORTANTE
**Perché:** 214MB mesh in memoria rallentano startup, sprecano RAM

**Task:**
- [ ] Rimuovere `MeshProcessor.meshes` dict (in-memory storage)
- [ ] Implementare `@lru_cache` decorator per caching LRU:
```python
from functools import lru_cache

class MeshProcessor:
    @lru_cache(maxsize=10)  # Keep max 10 meshes in memory
    def get_mesh(self, artifact_id):
        """Load mesh on-demand with LRU caching."""
        # Get mesh path from database
        mesh_path = self.db.get_artifact(artifact_id)['mesh_path']

        # Load with trimesh
        mesh = trimesh.load(mesh_path)

        return mesh
```
- [ ] Aggiungere context manager per temp mesh loading:
```python
with mesh_processor.load_temp(artifact_id) as mesh:
    # Use mesh
    features = extract_features(mesh)
# Mesh automatically unloaded
```
- [ ] Implementare mesh compression per storage:
  - Salvare versione decimata (low-res) per preview
  - Caricare full-res solo quando necessario
- [ ] Aggiungere preload hint per operazioni batch

**Files da modificare:**
- `acs/core/mesh_processor.py` - rimuovere self.meshes dict
- Tutte le chiamate a `mesh_processor.meshes[id]` → `mesh_processor.get_mesh(id)`

---

### 2.4 Database Optimization
**Perché:** Queries lente, manca caching, N+1 problem

**Task:**
- [ ] **Pagination:** Aggiungere LIMIT/OFFSET a tutte le query list:
```python
def get_all_artifacts(self, page=1, per_page=50):
    offset = (page - 1) * per_page
    cursor.execute('''
        SELECT * FROM artifacts
        ORDER BY upload_date DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
```
- [ ] **JOIN Queries:** Eliminare N+1 con JOIN:
```python
# PRIMA (N+1):
artifacts = db.get_all_artifacts()
for artifact in artifacts:
    features = db.get_features(artifact['artifact_id'])  # N queries!

# DOPO (single query):
cursor.execute('''
    SELECT a.*, f.feature_name, f.feature_value
    FROM artifacts a
    LEFT JOIN features f ON a.artifact_id = f.artifact_id
''')
```
- [ ] **Caching:** Usare `analysis_results` table per cache:
```python
# Check cache before computing
cached = db.get_analysis_result('pca', artifact_ids)
if cached:
    return cached['results_json']

# Compute and save
pca_results = compute_pca(features)
db.save_analysis_result('pca', artifact_ids, pca_results)
```
- [ ] **Indexes:** Aggiungere missing indexes:
```sql
CREATE INDEX idx_artifact_project ON artifacts(project_id);
CREATE INDEX idx_feature_name ON features(feature_name);
CREATE INDEX idx_classification_date ON classifications(classification_date);
```
- [ ] **Connection Pool:** Implementare connection pooling per concurrency

**Files da modificare:**
- `acs/core/database.py` - tutte le query functions

---

## 📊 PRIORITÀ 3: FUNZIONALITÀ MANCANTI (SETTIMANA 3-4)

### 3.1 Project Management UI Completa
**Perché:** DB pronto ma nessuna interfaccia web

**Task:**
- [ ] **Dashboard Projects:** Pagina principale con lista progetti
  - Card per ogni progetto con statistiche
  - Filtri per status, data, n° artifacts
  - Pulsanti: View, Edit, Delete, Export

- [ ] **Create Project:** Form per nuovo progetto
  - Nome, descrizione, tags
  - Validazione lato client e server

- [ ] **Project Detail:** Pagina dettaglio progetto
  - Info progetto (edit inline)
  - Lista artifacts nel progetto
  - Statistiche: n° artifacts, classifications, avg features
  - Grafici: distribuzione classi, timeline upload
  - Azioni bulk: classify all, export all, generate reports

- [ ] **Assign Artifacts:** UI per assegnare artifacts a progetti
  - Drag & drop interface
  - Multi-select con checkbox
  - Bulk assign

- [ ] **Merge Projects:** UI per unire progetti
  - Select source projects
  - Confirm merge
  - Mostra artifacts che saranno uniti

**Files da creare:**
- `acs/web/templates/projects/`
  - `list.html` - dashboard progetti
  - `detail.html` - dettaglio progetto
  - `create.html` - form creazione
  - `assign.html` - assegna artifacts
- `acs/api/blueprints/web/projects.py` - routes per web UI

**API Endpoints da aggiungere:**
- `POST /api/projects` - create project
- `GET /api/projects` - list projects (con pagination)
- `GET /api/projects/<id>` - get project details
- `PUT /api/projects/<id>` - update project
- `DELETE /api/projects/<id>` - delete project (con artifacts)
- `POST /api/projects/<id>/assign` - assign artifacts
- `POST /api/projects/merge` - merge projects

---

### 3.2 ML Model Versioning System
**Perché:** Solo un modello, no A/B testing, no rollback

**Task:**
- [ ] **Database Schema:** Aggiungere tabella `ml_models`:
```sql
CREATE TABLE ml_models (
    model_id TEXT PRIMARY KEY,  -- UUID
    model_name TEXT,            -- "savignano_rf_v1"
    algorithm TEXT,             -- "random_forest", "gradient_boosting"
    version INTEGER,            -- 1, 2, 3...
    training_date TEXT,
    training_samples INTEGER,
    validation_accuracy REAL,
    hyperparameters_json TEXT,  -- JSON con parametri
    model_path TEXT,            -- Path to .pkl file
    feature_names_json TEXT,    -- Lista features usate
    class_labels_json TEXT,     -- Lista classi
    is_active INTEGER DEFAULT 0,-- 1 = active model
    notes TEXT
)
```

- [ ] **Model Training:** Salvare ogni training come nuova versione
```python
def train_new_version(training_data, algorithm='random_forest'):
    # Train model
    model = train_model(training_data, algorithm)

    # Generate version number
    latest = db.get_latest_model_version('savignano_rf')
    new_version = latest + 1

    # Save model file
    model_id = str(uuid.uuid4())
    model_path = f"~/.acs/models/savignano_rf_v{new_version}_{model_id}.pkl"
    joblib.dump(model, model_path)

    # Save metadata to database
    db.add_ml_model(
        model_id=model_id,
        model_name=f'savignano_rf_v{new_version}',
        algorithm=algorithm,
        version=new_version,
        training_samples=len(training_data),
        validation_accuracy=accuracy,
        model_path=model_path
    )

    return model_id
```

- [ ] **Model Selection:** Endpoint per switch active model
```python
@app.route('/api/ml/activate-model/<model_id>', methods=['POST'])
def activate_model(model_id):
    # Deactivate current active
    db.execute('UPDATE ml_models SET is_active = 0')

    # Activate selected
    db.execute('UPDATE ml_models SET is_active = 1 WHERE model_id = ?', (model_id,))

    # Reload model in memory
    ml_classifier.load_model(model_id)

    return jsonify({'status': 'success'})
```

- [ ] **Model Comparison:** UI per comparare versioni
  - Tabella con metriche (accuracy, precision, recall, F1)
  - Confusion matrix side-by-side
  - Feature importance comparison
  - Performance su test set

- [ ] **A/B Testing:** Endpoint per predict con modello specifico
```python
@app.route('/api/ml/predict/<model_id>', methods=['POST'])
def predict_with_model(model_id):
    features = request.json['features']
    model = load_model_from_db(model_id)
    prediction = model.predict(features)
    return jsonify(prediction)
```

**Files da modificare:**
- `acs/core/database.py` - aggiungere tabella e methods
- `acs/core/ml_classifier.py` - versioning support
- Nuovo file: `acs/api/blueprints/ml_models.py` - endpoints

---

### 3.3 Batch Classification Endpoint
**Perché:** Deve classificare uno alla volta, inefficiente

**Task:**
- [ ] **API Endpoint:** `POST /api/classification/batch-classify`
```python
@classification_bp.route('/batch-classify', methods=['POST'])
def batch_classify():
    """Classify multiple artifacts in one request."""
    data = request.json
    artifact_ids = data.get('artifact_ids', [])
    classifier_type = data.get('classifier', 'ml')  # 'ml' or 'formal'

    results = []
    for artifact_id in artifact_ids:
        features = db.get_features(artifact_id)

        if classifier_type == 'ml':
            prediction = ml_classifier.predict(features)
        else:
            prediction = formal_taxonomy.classify(features)

        # Save classification
        db.add_classification(
            artifact_id=artifact_id,
            class_id=prediction['class_id'],
            class_name=prediction['class_name'],
            confidence=prediction['confidence']
        )

        results.append({
            'artifact_id': artifact_id,
            'classification': prediction,
            'status': 'success'
        })

    return jsonify({'results': results})
```

- [ ] **Async Version:** Con Celery per batch grandi
```python
@celery.task
def batch_classify_task(artifact_ids):
    # Same logic but async
    pass
```

- [ ] **Web UI:** Pagina per batch classification
  - Select multiple artifacts (checkbox)
  - Choose classifier (ML, Formal Taxonomy, AI)
  - Show progress bar
  - Display results table

**Files da modificare:**
- `acs/api/blueprints/classification.py` - aggiungere endpoint

---

### 3.4 Statistics Dashboard
**Perché:** Dati nel DB ma nessuna visualizzazione

**Task:**
- [ ] **Dashboard Homepage:** Metrics overview
  - Total artifacts
  - Total projects
  - Total classifications (validated / total)
  - Recent uploads (last 7 days)
  - Top 5 artifact classes

- [ ] **Grafici Interattivi:** Usare Chart.js o Plotly
  - Timeline: Uploads over time (bar chart)
  - Distribution: Artifact classes (pie chart)
  - Heatmap: Feature correlations
  - Scatter: PCA visualization (interactive)
  - Box plots: Feature distributions per class

- [ ] **Filtri:** Filter by project, date range, class

- [ ] **Export:** Download stats as CSV/JSON

**Files da creare:**
- `acs/web/templates/statistics/`
  - `dashboard.html` - main dashboard
  - `charts.html` - detailed charts
- `acs/api/blueprints/web/statistics.py` - routes

**API Endpoints:**
- `GET /api/statistics/overview` - high-level metrics
- `GET /api/statistics/timeline` - uploads over time
- `GET /api/statistics/distribution` - class distribution
- `GET /api/statistics/features` - feature stats

---

### 3.5 Artifact Deletion Cascade
**Perché:** Non esiste endpoint per eliminare artifacts

**Task:**
- [ ] **Soft Delete:** Aggiungere flag `deleted` invece di cancellare
```sql
ALTER TABLE artifacts ADD COLUMN deleted INTEGER DEFAULT 0;
```

- [ ] **Cascade Logic:** Quando si elimina artifact, eliminare:
  - Features (tabella `features`)
  - Stylistic features (tabella `stylistic_features`)
  - Classifications (tabella `classifications`)
  - Training data (tabella `training_data`)
  - Comparisons (tabella `comparisons`)
  - File mesh da filesystem

- [ ] **API Endpoint:** `DELETE /api/artifacts/<artifact_id>`
```python
@artifacts_bp.route('/artifacts/<artifact_id>', methods=['DELETE'])
def delete_artifact(artifact_id):
    # Soft delete
    db.execute('UPDATE artifacts SET deleted = 1 WHERE artifact_id = ?', (artifact_id,))

    # Or hard delete with cascade
    db.delete_artifact_cascade(artifact_id)

    return jsonify({'status': 'deleted'})
```

- [ ] **Restore:** Endpoint per restore soft-deleted
```python
@artifacts_bp.route('/artifacts/<artifact_id>/restore', methods=['POST'])
def restore_artifact(artifact_id):
    db.execute('UPDATE artifacts SET deleted = 0 WHERE artifact_id = ?', (artifact_id,))
    return jsonify({'status': 'restored'})
```

- [ ] **Web UI:**
  - Pulsante "Delete" su artifact detail page
  - Conferma modal: "Are you sure?"
  - "Trash" page con soft-deleted artifacts
  - Pulsante "Restore" per recover

**Files da modificare:**
- `acs/core/database.py` - aggiungere `delete_artifact_cascade()`
- Nuovo file: `acs/api/blueprints/artifacts.py` - CRUD endpoints

---

## 🤖 PRIORITÀ 4: MACHINE LEARNING E AI (SETTIMANA 4-5)

### 4.1 Active Learning Pipeline
**Perché:** Labeling manuale lento, AI può suggerire cosa labellare

**Task:**
- [ ] **Uncertainty Sampling:** Identificare artifacts con low confidence
```python
def get_uncertain_artifacts(threshold=0.6):
    """Find artifacts with prediction confidence < threshold."""
    predictions = []
    for artifact_id in db.get_all_artifact_ids():
        features = db.get_features(artifact_id)
        pred = ml_classifier.predict(features)

        if pred['confidence'] < threshold:
            predictions.append({
                'artifact_id': artifact_id,
                'confidence': pred['confidence'],
                'prediction': pred['class_name']
            })

    # Sort by lowest confidence
    return sorted(predictions, key=lambda x: x['confidence'])
```

- [ ] **Annotation Queue:** Pagina web per labeling
  - Mostra artifact con low confidence
  - Show 3D viewer
  - Show features table
  - Show AI prediction
  - Form: Correct class, Notes
  - Buttons: Confirm, Reject, Skip

- [ ] **Labeling API:**
```python
@app.route('/api/labeling/queue', methods=['GET'])
def get_labeling_queue():
    """Get next N artifacts to label."""
    uncertain = get_uncertain_artifacts(threshold=0.7)
    return jsonify(uncertain[:10])  # Next 10

@app.route('/api/labeling/submit', methods=['POST'])
def submit_label():
    data = request.json
    artifact_id = data['artifact_id']
    correct_class = data['class_label']
    notes = data.get('notes', '')

    # Save as validated training sample
    features = db.get_features(artifact_id)
    db.add_training_sample(
        artifact_id=artifact_id,
        class_label=correct_class,
        features=features,
        validation_score=1.0,
        is_validated=True
    )

    return jsonify({'status': 'saved'})
```

- [ ] **Auto-retrain:** Trigger quando N nuovi samples validati
```python
def check_retrain_trigger():
    """Retrain model if 20+ new validated samples."""
    new_samples = db.get_training_samples(is_validated=True, since_last_train=True)

    if len(new_samples) >= 20:
        # Trigger async retraining
        retrain_model_task.delay(new_samples)

        # Notify admin
        send_notification("Model retraining started with {} new samples".format(len(new_samples)))
```

**Files da creare:**
- `acs/web/templates/labeling/queue.html` - annotation interface
- `acs/api/blueprints/labeling.py` - labeling endpoints
- `acs/ml/active_learning.py` - active learning logic

---

### 4.2 Feature Engineering Pipeline
**Perché:** Features estratte sono base, mancano derived features

**Task:**
- [ ] **Feature Derivation:** Creare features addizionali da quelle base
```python
class FeatureEngineer:
    def derive_features(self, base_features):
        derived = {}

        # Ratios
        derived['length_width_ratio'] = base_features['length'] / base_features['width']
        derived['blade_butt_ratio'] = base_features['blade_width'] / base_features['butt_width']

        # Normalized dimensions
        derived['relative_socket_depth'] = base_features['socket_depth'] / base_features['length']

        # Symmetry metrics
        derived['blade_symmetry_score'] = calculate_symmetry(base_features['blade_curvature'])

        # Complexity metrics
        derived['surface_complexity'] = base_features['surface_area'] / base_features['convex_hull_area']

        return derived
```

- [ ] **Feature Selection:** Identificare features più importanti
```python
from sklearn.feature_selection import SelectKBest, f_classif

def select_top_features(X, y, k=20):
    """Select top K most discriminative features."""
    selector = SelectKBest(f_classif, k=k)
    X_selected = selector.fit_transform(X, y)

    # Get selected feature names
    selected_indices = selector.get_support(indices=True)
    selected_features = [feature_names[i] for i in selected_indices]

    return selected_features
```

- [ ] **Feature Store:** Salvare derived features nel DB
```sql
-- Aggiungere a stylistic_features
INSERT INTO stylistic_features (artifact_id, feature_category, features_json)
VALUES (?, 'derived', ?)
```

- [ ] **Auto-derive:** Calcolare derived features automaticamente dopo extraction

**Files da modificare:**
- Nuovo file: `acs/ml/feature_engineering.py`
- `acs/core/mesh_processor.py` - integrare feature derivation

---

### 4.3 Model Explainability
**Perché:** ML è black box, archaeologists vogliono capire predictions

**Task:**
- [ ] **SHAP Values:** Implementare SHAP per spiegare predictions
```python
import shap

def explain_prediction_shap(model, features):
    """Generate SHAP explanation for prediction."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(features)

    # Generate plot
    shap.summary_plot(shap_values, features, show=False)
    plt.savefig('explanation.png')

    return shap_values
```

- [ ] **Feature Importance Visualization:** Grafici interattivi
  - Bar chart: Top 10 features
  - Waterfall plot: Single prediction explanation
  - Dependence plot: Feature vs prediction

- [ ] **Natural Language Explanation:** AI-generated text
```python
def generate_explanation(artifact_id, prediction):
    """Use Claude to generate human-readable explanation."""
    features = db.get_features(artifact_id)
    top_features = get_top_influential_features(features, n=5)

    prompt = f"""
    Explain why this artifact was classified as {prediction['class_name']}.

    Top influential features:
    {json.dumps(top_features, indent=2)}

    Generate a 2-3 sentence archaeological explanation.
    """

    explanation = ai_assistant.ask_question(prompt)
    return explanation
```

- [ ] **Confidence Intervals:** Mostrare incertezza
```python
def predict_with_confidence_intervals(features, n_bootstrap=100):
    """Predict with bootstrap confidence intervals."""
    predictions = []

    for _ in range(n_bootstrap):
        # Bootstrap sampling
        sample_features = bootstrap_sample(features)
        pred = model.predict_proba(sample_features)
        predictions.append(pred)

    # Calculate mean and std
    mean_pred = np.mean(predictions, axis=0)
    std_pred = np.std(predictions, axis=0)

    return {
        'prediction': mean_pred,
        'confidence_interval': (mean_pred - 1.96*std_pred, mean_pred + 1.96*std_pred)
    }
```

**Files da creare:**
- `acs/ml/explainability.py` - SHAP and explanations
- `acs/web/templates/artifacts/explanation.html` - visualization

---

### 4.4 Hyperparameter Tuning
**Perché:** Usa default params, non ottimizzati per questo dataset

**Task:**
- [ ] **Grid Search:** Implementare hyperparameter search
```python
from sklearn.model_selection import GridSearchCV

def tune_hyperparameters(X_train, y_train):
    """Find best hyperparameters via grid search."""
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, 15, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }

    rf = RandomForestClassifier()
    grid_search = GridSearchCV(rf, param_grid, cv=5,
                               scoring='accuracy', n_jobs=-1)
    grid_search.fit(X_train, y_train)

    return {
        'best_params': grid_search.best_params_,
        'best_score': grid_search.best_score_,
        'cv_results': grid_search.cv_results_
    }
```

- [ ] **Bayesian Optimization:** Per spazi di ricerca grandi
```python
from skopt import BayesSearchCV

def tune_bayesian(X_train, y_train):
    """Bayesian hyperparameter optimization."""
    search_spaces = {
        'n_estimators': (50, 500),
        'max_depth': (5, 50),
        'min_samples_split': (2, 20)
    }

    opt = BayesSearchCV(
        RandomForestClassifier(),
        search_spaces,
        n_iter=32,
        cv=5
    )
    opt.fit(X_train, y_train)

    return opt.best_params_
```

- [ ] **Auto-tune:** Endpoint per trigger tuning
```python
@app.route('/api/ml/tune', methods=['POST'])
def tune_model():
    """Trigger hyperparameter tuning."""
    # Get training data
    training_data = db.get_all_training_samples()

    # Start async tuning task
    task = tune_hyperparameters_task.delay(training_data)

    return jsonify({'task_id': task.id, 'status': 'tuning'})
```

- [ ] **Save Best Params:** Salvare in ml_models table

**Files da modificare:**
- `acs/core/ml_classifier.py` - aggiungere tuning methods
- Nuovo file: `acs/ml/hyperparameter_tuning.py`

---

## 🧹 PRIORITÀ 5: PULIZIA E REFACTORING (SETTIMANA 5-6)

### 5.1 Rimuovere Codice Duplicato

**Task:**
- [ ] **Feature Extraction Unificato:**
  - Merge `MeshProcessor._extract_features()` con `extract_savignano_features()`
  - Single pipeline: basic → savignano → derived

- [ ] **Taxonomy Inheritance:**
  - `SavignanoClassifier` dovrebbe estendere `FormalTaxonomySystem`
  - Non sistemi paralleli

- [ ] **Report Generation:**
  - Unificare rendering logic
  - Template system per report diversi
  - Rimuovere duplicazione plot generation code

**Files da modificare:**
- `acs/core/mesh_processor.py`
- `acs/savignano/morphometric_extractor.py`
- `acs/classification/savignano_classifier.py`
- `acs/savignano/comprehensive_report.py`

---

### 5.2 Configurazione Unificata

**Task:**
- [ ] **Single Config File:** `acs/core/config.py`
```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    # Database
    DB_PATH: str = os.getenv('ACS_DB_PATH', 'acs_artifacts.db')

    # Upload
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', '/tmp/acs_uploads')
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB

    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    JWT_EXPIRATION: int = 3600  # 1 hour

    # ML
    ML_MODEL_PATH: str = '~/.acs/models'

    # AI
    ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')

    # Celery
    CELERY_BROKER: str = os.getenv('CELERY_BROKER', 'redis://localhost:6379/0')

    # CORS
    CORS_ORIGINS: list = ['http://localhost:3000']

# Development config
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

# Production config
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Override with production values

# Select config based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

- [ ] **Environment Variables:** `.env` file per development
```bash
# .env
FLASK_ENV=development
ACS_DB_PATH=/home/user/data/acs.db
UPLOAD_FOLDER=/home/user/uploads
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=random-secret-key-123
```

- [ ] **Load Config:** In app initialization
```python
# acs/api/app.py
from acs.core.config import config

app = Flask(__name__)
app.config.from_object(config[os.getenv('FLASK_ENV', 'default')])
```

**Files da creare/modificare:**
- `acs/core/config.py` - unified config
- `.env.example` - template
- Rimuovere hardcoded values ovunque

---

### 5.3 Logging Strutturato

**Task:**
- [ ] **JSON Logging:** Per parsing e analisi
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Setup
handler = logging.FileHandler('acs.log')
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

- [ ] **Log Levels:** Appropriati
  - DEBUG: Detailed info for debugging
  - INFO: General informational messages
  - WARNING: Warning messages
  - ERROR: Error messages
  - CRITICAL: Critical errors

- [ ] **Structured Fields:**
```python
logger.info("Mesh loaded", extra={
    'artifact_id': 'axe123',
    'file_size': 1024000,
    'load_time_ms': 250,
    'n_vertices': 50000
})
```

- [ ] **Log Rotation:** Per evitare file troppo grandi
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'acs.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
```

**Files da modificare:**
- `acs/core/logging_config.py` - setup logging
- Tutti i file: usare logger invece di print

---

### 5.4 Testing Infrastructure

**Task:**
- [ ] **Unit Tests:** Pytest per core modules
```python
# tests/test_mesh_processor.py
import pytest
from acs.core.mesh_processor import MeshProcessor

def test_load_valid_obj():
    processor = MeshProcessor()
    mesh = processor.load_mesh('test_data/valid.obj', 'test_artifact')
    assert mesh is not None
    assert 'test_artifact' in processor.meshes

def test_load_invalid_file():
    processor = MeshProcessor()
    with pytest.raises(ValueError):
        processor.load_mesh('test_data/invalid.txt', 'test')
```

- [ ] **Integration Tests:** Test API endpoints
```python
# tests/test_api.py
def test_upload_mesh(client):
    with open('test_data/axe.obj', 'rb') as f:
        response = client.post('/api/mesh/upload', data={
            'file': f,
            'artifact_id': 'test_axe'
        })

    assert response.status_code == 200
    assert response.json['status'] == 'success'
```

- [ ] **Fixtures:** Test data e mocks
```python
# tests/conftest.py
import pytest
from acs.api.app import create_app

@pytest.fixture
def app():
    app = create_app('testing')
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db():
    # Setup test database
    db = ArtifactDatabase(':memory:')
    yield db
    # Teardown
```

- [ ] **Coverage:** Aim for 80%+ coverage
```bash
pytest --cov=acs --cov-report=html
```

**Files da creare:**
- `tests/` directory
- `tests/conftest.py` - fixtures
- `tests/test_*.py` - test files
- `pytest.ini` - pytest config

---

### 5.5 Documentation

**Task:**
- [ ] **API Documentation:** OpenAPI/Swagger
```python
from flask_swagger_ui import get_swaggerui_blueprint

# Swagger UI
SWAGGER_URL = '/api/docs'
API_URL = '/api/openapi.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "BrozeAXE-AI API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
```

- [ ] **Code Documentation:** Docstrings everywhere
```python
def extract_savignano_features(mesh: trimesh.Trimesh) -> dict:
    """Extract Savignano-specific morphometric features.

    Args:
        mesh: Trimesh object of the axe artifact

    Returns:
        Dictionary with 36+ Savignano feature parameters:
        - Basic dimensions (length, width, thickness)
        - Socket analysis (depth, width, shape, symmetry)
        - Blade analysis (angle, symmetry, curvature)
        - Technological features (hammering, casting quality)

    Raises:
        ValueError: If mesh is invalid or missing required geometry

    Example:
        >>> mesh = trimesh.load('axe.obj')
        >>> features = extract_savignano_features(mesh)
        >>> print(features['lunghezza_totale'])
        165.3
    """
```

- [ ] **README:** Comprehensive setup guide
  - Requirements
  - Installation steps
  - Configuration
  - Running the app
  - API usage examples
  - Troubleshooting

- [ ] **Architecture Docs:** System design documentation
  - Database schema diagram
  - Component architecture
  - Data flow diagrams
  - ML pipeline diagram

**Files da creare:**
- `docs/` directory
- `docs/api.md` - API documentation
- `docs/architecture.md` - system design
- `docs/setup.md` - setup guide
- Update `README.md`

---

## 📈 MONITORING E PRODUCTION (SETTIMANA 6+)

### 6.1 Monitoring and Alerting

**Task:**
- [ ] **Metrics Collection:** Prometheus metrics
- [ ] **Performance Monitoring:** APM (Application Performance Monitoring)
- [ ] **Error Tracking:** Sentry integration
- [ ] **Uptime Monitoring:** Health check endpoint
- [ ] **Usage Analytics:** Track API usage, popular endpoints

---

### 6.2 Deployment

**Task:**
- [ ] **Docker:** Containerize application
- [ ] **Docker Compose:** Multi-container setup (app + redis + postgres)
- [ ] **CI/CD:** GitHub Actions for automated testing/deployment
- [ ] **Production Server:** Gunicorn + Nginx
- [ ] **Database Migration:** Alembic for schema versioning

---

## 🎯 QUICK WINS (Fare subito, basso effort / alto impatto)

1. **✅ Add File Size Validation** (30 min)
   - Aggiungere check dimensione file in upload endpoint

2. **✅ Add Pagination to /artifacts** (1 ora)
   - Aggiungere LIMIT/OFFSET a query artifacts

3. **✅ Add /health Endpoint** (15 min)
   - Endpoint per health check: DB connection, disk space

4. **✅ Fix CORS Configuration** (15 min)
   - Specificare origins invece di allow all

5. **✅ Add Artifact Delete Endpoint** (1 ora)
   - Endpoint DELETE con cascade

6. **✅ Add Batch Classification** (2 ore)
   - Endpoint per classificare multipli artifacts

7. **✅ Add Project Statistics** (1 ora)
   - Endpoint per statistiche per progetto

8. **✅ Cache PCA Results** (1 ora)
   - Usare analysis_results table per caching

---

## 📊 RIEPILOGO PRIORITÀ

| Priorità | Area | Sforzo | Impatto | Settimane |
|----------|------|--------|---------|-----------|
| 🔥 P1 | Security & Stability | Alto | Critico | 1-2 |
| ⚡ P2 | Architecture & Performance | Alto | Alto | 2-3 |
| 📊 P3 | Missing Features | Medio | Alto | 3-4 |
| 🤖 P4 | ML & AI Improvements | Medio | Medio | 4-5 |
| 🧹 P5 | Cleanup & Refactoring | Medio | Medio | 5-6 |
| 📈 P6 | Monitoring & Production | Alto | Alto | 6+ |

---

## 🚀 ROADMAP TIMELINE

```
Week 1-2: SECURITY FIRST
├─ Authentication system
├─ File upload security
├─ CORS & API key security
└─ Error handling

Week 2-3: ARCHITECTURE
├─ Merge Flask apps
├─ Async tasks (Celery)
├─ Mesh lazy loading
└─ Database optimization

Week 3-4: FEATURES
├─ Project management UI
├─ ML model versioning
├─ Batch classification
└─ Statistics dashboard

Week 4-5: ML/AI
├─ Active learning
├─ Feature engineering
├─ Model explainability
└─ Hyperparameter tuning

Week 5-6: CLEANUP
├─ Code refactoring
├─ Unified config
├─ Logging & testing
└─ Documentation

Week 6+: PRODUCTION
├─ Monitoring & alerting
├─ Docker deployment
└─ CI/CD pipeline
```

---

## ✅ NEXT ACTIONS (da fare ORA)

1. **Review this TODO list** con team/client
2. **Prioritize** quale priorità affrontare per prima
3. **Create GitHub Issues** da questa lista
4. **Setup Project Board** (Kanban) con colonne: Todo, In Progress, Review, Done
5. **Start with P1 Security** - è CRITICO

---

**Fine TODO List**
