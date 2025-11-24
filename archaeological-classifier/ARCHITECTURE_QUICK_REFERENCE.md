# Archaeological Classifier System - Quick Reference

**Location:** `/Users/enzo/Documents/BrozeAXE-AI/archaeological-classifier/`
**Full Documentation:** See `ACS_ARCHITECTURAL_ANALYSIS.md` (1376 lines, comprehensive)

---

## System Overview

**Archaeological Classifier System (ACS)** is a production-ready Flask web application for artifact classification that integrates:
- Formal parametric taxonomy (rule-based)
- Machine learning (Random Forest/Gradient Boosting)
- AI analysis (Claude 4.5 Sonnet)
- Morphometric analysis (PCA, clustering)
- 3D visualization (Three.js)
- Savignano specialization (36-parameter extraction for Bronze Age axes)

---

## Quick Navigation

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Web Routes** | `/acs/web/routes.py` | Flask routes for web UI (2000+ lines) |
| **API Routes** | `/acs/api/blueprints/*.py` | REST API endpoints |
| **Database** | `/acs/core/database.py` | SQLite schema & operations |
| **Taxonomy** | `/acs/core/taxonomy.py` | Formal parametric classification |
| **ML Classifier** | `/acs/core/ml_classifier.py` | Random Forest/Gradient Boosting |
| **AI Assistant** | `/acs/core/ai_assistant.py` | Claude 4.5 integration |
| **Morphometric** | `/acs/core/morphometric.py` | PCA, clustering, similarity |
| **Stylistic Analyzer** | `/acs/core/stylistic_analyzer.py` | Symmetry, surface quality, etc. |
| **Mesh Processor** | `/acs/core/mesh_processor.py` | 3D mesh loading & feature extraction |
| **Savignano** | `/acs/savignano/*.py` | Bronze Age axis specialization |

### Web Templates

| Template | Purpose |
|----------|---------|
| `ai_assistant.html` | AI classification interface |
| `viewer3d.html` | Interactive 3D mesh viewer |
| `taxonomy.html` | Taxonomy management UI |
| `morphometric.html` | PCA/clustering analysis |
| `savignano_analysis.html` | Savignano-specific analysis |
| `artifact_detail.html` | Single artifact details |
| `artifacts.html` | Artifact list & browser |

---

## 4 Classification Pathways

### 1. AI Classification (Claude 4.5)
```
Route: /web/ai-classify (POST) or /web/ai-classify-stream
Output: Morphometric assessment + suggested class + confidence + archaeological notes
Requires: ANTHROPIC_API_KEY
Model: claude-sonnet-4-20250514
```

### 2. ML Prediction (Trained Model)
```
Route: /web/ml-predict (POST)
Output: Predicted class + confidence + feature importance
Requires: acs_ml_model.pkl (trained model on disk)
Minimum: 20 validated training samples
```

### 3. Hybrid Classification (Rule-Based + ML)
```
Route: /web/hybrid-classify (POST)
Output: Rule result + ML result + combined recommendation
Combines: Formal taxonomy (parametric) + ML model (learned)
Confidence: Comparison of both approaches
```

### 4. Stylistic Auto-Classification
```
Route: /web/auto-classify-stylistic (POST)
Output: Full classification profile with multiple perspectives
Features: Symmetry, surface quality, shape regularity, curvature
Optional: Can include AI or ML results
```

---

## Database Schema (SQLite)

### Core Tables

**artifacts** - 3D mesh registry
- artifact_id (PK), project_id, mesh_path, upload_date, n_vertices, n_faces, is_watertight

**features** - Morphometric measurements
- id (PK), artifact_id (FK), feature_name, feature_value, extraction_date
- Key names: 'volume', 'length', 'width', 'socket_depth', 'sav_butt_width', etc.

**stylistic_features** - Non-morphometric analysis
- id (PK), artifact_id (FK), feature_category, features_json, extraction_date

**classifications** - Classification results
- id (PK), artifact_id (FK), class_id, class_name, confidence, validated, validator_notes

**training_data** - Curated ML training set
- id (PK), artifact_id (FK), class_label, features_json, is_validated
- Only is_validated=1 rows used for ML training

**analysis_results** - Cached results (PCA, clustering, QA)
- id (PK), analysis_type, artifact_ids, results_json, analysis_date

**comparisons** - Cached comparison results
- id (PK), artifact1_id, artifact2_id, similarity_score, comparison_data

**projects** - Multi-project support
- project_id (PK), project_name, description, status ('active', 'archived', 'merged')

---

## 3D Viewer & Comparisons

### 3D Viewer
- **Route:** `/web/viewer` (GET)
- **Technology:** Three.js (WebGL)
- **Formats:** OBJ, PLY, STL
- **Features:** Rotate, zoom, preset views, wireframe, axes/grid, fullscreen, screenshot

### 1:1 Comparison
- **Route:** `/web/compare-artifacts` (POST)
- **Output:** morphometric_similarity + stylistic_similarities + overall_similarity (60% morph + 40% style)
- **Visualization:** Split-screen in 3D viewer

### 1:Many Search
- **Route:** `/web/find-similar` (POST)
- **Parameters:** query_id, n_results (default 10), metric ('cosine'/'euclidean'), min_similarity
- **Output:** Ranked list of similar artifacts with similarity scores

---

## Morphometric Features

### Standard Features (Extracted by MeshProcessor)
- volume, surface_area, length, width, thickness, convexity, aspect_ratio
- compactness, vertex_count, face_count

### Technological Features (Optional)
- socket_depth, socket_diameter, edge_angle, hammering_index
- has_socket (bool), has_midrib (bool), hammered (bool)

### Savignano Features (36+ parameters)
- **Butt:** butt_width, butt_thickness, socket_width, socket_depth, socket_profile, socket_volume
- **Edges:** raised_edge_length, raised_edge_max_thickness, raised_edge_regularity
- **Body:** body_min_width, body_max_width, body_thickness_without_edges, body_thickness_with_edges
- **Blade:** blade_width, blade_shape, blade_arc, blade_chord, blade_sharpness
- **Proportions:** length_width_ratio, length_thickness_ratio, socket_to_body_ratio, edge_angle

---

## AI Analysis with Claude

### Configuration
```
Priority Order:
1. Web UI: Set via /web/ai-assistant → stored in config
2. Environment Variable: ANTHROPIC_API_KEY
3. Config file: ~/.acs/config.json

API Version: claude-sonnet-4-20250514
Temperature: 0.3 (focused, deterministic)
Max tokens: 2000
```

### AI Prompt Includes
1. System context (expert archaeological AI)
2. Artifact morphometric features
3. Existing taxonomic classes (name + description)
4. User-provided archaeological context
5. Task definition (analysis + classification recommendation)

### Expected Output
```json
{
    "morphometric_assessment": "Interpretation of features",
    "suggested_class": "Class name",
    "confidence": "High|Medium|Low",
    "reasoning": "Why this class",
    "recommendation": "classify_existing|create_new",
    "archaeological_notes": "Period, technique, function"
}
```

---

## ML Model Training

### Workflow
```
1. Database has validated classifications (validated=1)
2. POST /web/ml-train (algorithm='random_forest'|'gradient_boosting')
3. Load training_data (only is_validated=1 rows)
4. Split: 80/20 train/validation (stratified)
5. Standardize features (StandardScaler)
6. Train model
7. Validate (accuracy, cross-val, confusion matrix)
8. Save to: acs_ml_model.pkl (joblib)
```

### Requirements
- Minimum 10 training samples
- At least 2 different classes
- Recommended: 20+ samples for good accuracy

### Output Metrics
```json
{
    "algorithm": "random_forest",
    "n_samples": 25,
    "n_classes": 3,
    "validation_accuracy": 0.92,
    "cross_val_score": 0.89,
    "class_distribution": {"Class1": 10, "Class2": 8, "Class3": 7},
    "feature_names": ["volume", "length", "width", ...]
}
```

---

## Savignano Analysis

### Complete Workflow
```bash
python savignano_complete_workflow.py \
    --meshes /path/to/96/axes/ \
    --output /results/ \
    --weights /path/to/weights.json \
    --anthropic-api-key YOUR_KEY
```

### Features Extracted
1. Morphometric: 36+ Savignano-specific parameters
2. Matrix clustering: Identifies distinct casting molds (typically 6-10 matrices)
3. Archaeological QA: Answers 6 key questions
4. AI Interpretation: Claude analysis of findings

### Output Structure
```
output/
├─ features/savignano_features_all.csv
├─ matrices/matrix_analysis.json
├─ archaeological_qa/answers.json
└─ visualizations/pca_plot.png, dendrogram.png
```

### 6 Archaeological Questions Answered
1. How many casting matrices were used?
2. What are matrix-specific characteristics?
3. How were individual axes modified?
4. Evidence of recycling/remelting?
5. Chronological sequence?
6. Production technique indicators?

---

## Important File Paths

```
/acs/
├── web/
│   ├── routes.py              # Main Flask routes (2000+ lines)
│   └── templates/
│       ├── ai_assistant.html
│       ├── viewer3d.html
│       ├── taxonomy.html
│       └── ...
├── api/
│   ├── app.py                 # Flask app factory
│   └── blueprints/
│       ├── classification.py
│       ├── morphometric.py
│       ├── mesh.py
│       ├── savignano.py
│       └── agents.py
├── core/
│   ├── database.py            # SQLite schema & operations
│   ├── taxonomy.py            # Parametric classification
│   ├── ml_classifier.py       # ML model training/prediction
│   ├── ai_assistant.py        # Claude integration
│   ├── morphometric.py        # PCA, clustering, similarity
│   ├── stylistic_analyzer.py
│   └── mesh_processor.py      # 3D mesh loading
├── savignano/
│   ├── morphometric_extractor.py
│   ├── matrix_analyzer.py
│   └── archaeological_qa.py
└── models/
    ├── artifact.py            # Pydantic models
    └── classification.py

Database: acs_artifacts.db (SQLite)
ML Model: acs_ml_model.pkl (joblib)
Config: ~/.acs/config.json
```

---

## Starting the System

```bash
# From project root
python run_web.py

# Runs on: http://localhost:5001/web/
# API docs: http://localhost:5001/api/docs
```

---

## Key Integration Points for Savignano

### Current Status
- ✅ Savignano morphometric extraction working
- ✅ Matrix clustering implemented
- ✅ Archaeological QA system functional
- ✅ API blueprint registered
- ⚠️ Not fully integrated into main workflow

### Recommended Integration (5 Phases)

**Phase 1: Feature Integration** (Week 1-2)
- Auto-extract Savignano features for project artifacts
- Store with `sav_` prefix in features table

**Phase 2: Taxonomy Integration** (Week 2-3)
- Define Savignano matrix classes with Savignano parameters
- Auto-detect Savignano artifacts

**Phase 3: AI Integration** (Week 3-4)
- Include Savignano context in AI prompts
- AI-assisted matrix identification

**Phase 4: Web UI** (Week 4-5)
- Dedicated Savignano workspace
- Matrix visualization dashboard

**Phase 5: ML Training** (Week 5-6)
- Train ML model for matrix classification
- Integrate into hybrid classification

---

## Data Flow Summary

```
Upload Mesh (AXE_001.obj)
    ↓ [MeshProcessor]
Extract morphometric features (20+ standard + optional Savignano)
    ↓
Store in DB: artifacts, features tables
    ↓
User initiates classification
    ↓ ┌─────────────────────┬──────────────────┬──────────────┐
      │                     │                  │              │
      v                     v                  v              v
   AI Classify      ML Predict        Hybrid Classify   Stylistic Auto
   (Claude)         (Trained RF)      (Both methods)     (Multi-feature)
      │                 │                  │              │
      └─────────────────┴──────────────────┴──────────────┘
                        ↓
            Save to classifications table
                        ↓
            [Optional] User validates
                        ↓
        Add to training_data (is_validated=1)
                        ↓
        [Eventually] Retrain ML model
```

---

## Performance Targets

| Operation | Time |
|-----------|------|
| Mesh upload + feature extraction | 2-5 sec |
| AI analysis (Claude) | 3-8 sec |
| ML prediction | <100ms |
| 1:1 comparison | 1-2 sec |
| 1:Many search (1 vs 50) | 5-10 sec |
| PCA fit (50 artifacts) | 1-2 sec |
| ML model training | 1-2 sec |

---

## Storage Estimate

| Item | Size |
|------|------|
| Per artifact mesh | 0.5-5 MB |
| Per artifact features | ~1 KB |
| Database (100 artifacts) | ~2 MB |
| ML model | ~5 MB |
| **Total (100 artifacts)** | **50-500 MB** |

---

## Troubleshooting

### API Key Issues
```
Error: "API key not configured"
Solution: Set ANTHROPIC_API_KEY env var OR configure via /web/ai-assistant
```

### ML Model Not Found
```
Error: "ML model not trained yet"
Solution: Need >=20 validated samples, then POST /web/ml-train
```

### Mesh Loading Issues
```
Error: "Mesh format not supported"
Solution: Use OBJ, PLY, or STL formats. Check trimesh can load it.
```

### Database Locked
```
Error: SQLite database locked
Solution: Restart Flask app. Check no other processes using acs_artifacts.db
```

---

## Useful Commands

```bash
# Start web server
python run_web.py

# Run Savignano complete workflow
python savignano_complete_workflow.py --meshes /data/axes/ --output /results/

# Export database
curl -X POST http://localhost:5001/web/export-data > backup.json

# Check statistics
curl http://localhost:5001/web/statistics

# Train ML model
curl -X POST http://localhost:5001/web/ml-train \
  -H "Content-Type: application/json" \
  -d '{"algorithm":"random_forest","validation_split":0.2}'
```

---

## For Detailed Information

See **ACS_ARCHITECTURAL_ANALYSIS.md** (1376 lines) for:
- Complete database schema documentation
- Detailed classification algorithm explanation
- Full AI prompt structure
- ML training workflow details
- Savignano parameter definitions
- Data flow examples
- Architecture diagram
- Deployment considerations
- Integration recommendations

---

**Last Updated:** November 9, 2025
**Comprehensive Documentation:** `ACS_ARCHITECTURAL_ANALYSIS.md`
**Questions?** See project README.md or documentation files
