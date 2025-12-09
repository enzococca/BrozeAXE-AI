# BrozeAXE-AI

**Archaeological Classifier System (ACS) - Advanced 3D Mesh Analysis for Bronze Age Artifacts**

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

BrozeAXE-AI is a sophisticated web-based archaeological analysis system designed for the morphometric study and classification of Bronze Age artifacts. Originally developed for analyzing the **Savignano bronze axes hoard**, this system combines 3D mesh processing, advanced statistical analysis, machine learning, and AI-powered reasoning (Claude 4.5 Sonnet) to provide comprehensive archaeological insights.

### What It Does

- **Analyzes 3D scanned artifacts** - Process OBJ, PLY, and STL mesh files
- **Extracts morphometric parameters** - 36+ measurements specific to Bronze Age axes
- **Identifies casting matrices** - Groups artifacts that came from the same mold
- **Classifies artifacts** - Using AI, ML, or hybrid approaches
- **Generates comprehensive reports** - Multi-page PDFs with visualizations and analysis
- **Enables comparative studies** - Compare artifacts 1:1 or across entire collections

## Key Features

### 3D Mesh Processing
- Load and process OBJ, PLY, STL files
- Automatic feature extraction (volume, dimensions, surface area)
- Mesh normalization and scale factor handling
- Interactive 3D visualization with Three.js

### Savignano Morphometric Analysis
- **36+ specialized parameters** for Bronze Age axes:
  - Socket (incavo) depth, width, and profile
  - Butt (tallone) measurements
  - Blade dimensions and edge angles
  - Raised edges analysis
- Detection of post-casting modifications (hammering, filing marks)
- Archaeological Quality Assurance (QA) system

### Advanced Statistical Analysis
- **Principal Component Analysis (PCA)** with explained variance tracking
- **Hierarchical Clustering** for artifact grouping
- **DBSCAN Clustering** for identifying casting matrices
- **Procrustes Superimposition** for shape comparison
- **Elliptic Fourier Analysis** for outline analysis

### Classification Systems (4 Approaches)
| Method | Description | Speed |
|--------|-------------|-------|
| **AI Classification** | Claude 4.5 Sonnet intelligent analysis | 3-8s |
| **ML Prediction** | Random Forest/Gradient Boosting | <100ms |
| **Hybrid** | Combined rule-based + ML | ~2s |
| **Stylistic Auto** | Multi-feature comprehensive profiling | ~1s |

### Formal Taxonomy System
- Parametric class definitions with explicit morphometric parameters
- Full version control with SHA256 hashing
- Complete audit trail with mandatory justifications
- Automatic class discovery from clustering results

### Report Generation
- Multi-page PDF reports with professional layouts
- 3D mesh renderings (front, profile, cross-sections)
- Measurement tables with scientific formatting
- AI interpretations and technical analysis
- Bilingual support (Italian/English)

## Architecture

```
BrozeAXE-AI/
├── app.py                          # Simple Savignano report application
├── requirements.txt                # Python dependencies
├── archaeological-classifier/      # Main ACS system
│   ├── acs/
│   │   ├── core/                  # Analysis modules
│   │   │   ├── database.py        # SQLite ORM
│   │   │   ├── mesh_processor.py  # 3D mesh processing
│   │   │   ├── morphometric.py    # PCA, clustering
│   │   │   ├── taxonomy.py        # Formal taxonomy
│   │   │   ├── ml_classifier.py   # ML models
│   │   │   └── ai_assistant.py    # Claude integration
│   │   │
│   │   ├── savignano/             # Savignano-specific modules
│   │   │   ├── morphometric_extractor.py
│   │   │   ├── comprehensive_report.py
│   │   │   ├── matrix_analyzer.py
│   │   │   └── archaeological_qa.py
│   │   │
│   │   ├── api/                   # REST API (Flask blueprints)
│   │   ├── web/                   # Web interface
│   │   │   ├── routes.py          # Web routes
│   │   │   ├── templates/         # 24 HTML templates
│   │   │   └── static/            # CSS, JS, images
│   │   │
│   │   └── mcp/                   # Model Context Protocol
│   │       └── server.py          # Claude Desktop integration
│   │
│   └── docs/                      # Documentation
│
├── templates/                      # Simple app templates
├── static/                         # Static assets
└── data/                          # Database and uploads
```

## Installation

### Prerequisites
- Python 3.9+
- pip package manager
- Virtual environment (recommended)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/enzococca/BrozeAXE-AI.git
cd BrozeAXE-AI

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings (especially ANTHROPIC_API_KEY for AI features)

# Run the application
python app.py
```

The application will start on http://127.0.0.1:5000/

### Full ACS System

```bash
cd archaeological-classifier
pip install -e .

# Run the full web interface
python -m acs.web.routes
# Or use the CLI
acs-cli --help
```

## Configuration

Create a `.env` file with the following variables:

```env
# Required for AI features
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Application settings
FLASK_ENV=production
PORT=5001
DATABASE_PATH=/data/acs_artifacts.db

# Optional: Cloud storage
DROPBOX_ACCESS_TOKEN=your-token
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json

# Security
JWT_SECRET_KEY=your-secret-key
MAX_UPLOAD_SIZE=100000000
```

## Usage

### Web Interface

1. **Upload Meshes**: Navigate to the upload page and select your 3D mesh files (OBJ, PLY, STL)
2. **Extract Features**: The system automatically extracts morphometric parameters
3. **Analyze**: Choose your analysis method:
   - Run PCA for dimensionality reduction
   - Perform clustering to identify groups
   - Use AI/ML for classification
4. **Compare**: Use the comparison tools to analyze similarities
5. **Generate Reports**: Create comprehensive PDF reports

### REST API

```bash
# Upload a mesh
curl -X POST -F "file=@axe.obj" http://localhost:5000/api/mesh/upload

# Run PCA analysis
curl -X POST http://localhost:5000/api/morphometric/pca \
  -H "Content-Type: application/json" \
  -d '{"artifact_ids": ["AXE_001", "AXE_002"]}'

# Classify an artifact
curl -X POST http://localhost:5000/api/classification/classify \
  -H "Content-Type: application/json" \
  -d '{"artifact_id": "AXE_097", "method": "ai"}'
```

### Python API

```python
from acs import MeshProcessor, MorphometricAnalyzer, FormalTaxonomySystem

# Process a mesh
processor = MeshProcessor()
features = processor.load_mesh("axe.obj", artifact_id="AXE_001")

# Run morphometric analysis
analyzer = MorphometricAnalyzer()
analyzer.add_features("AXE_001", features)
pca_results = analyzer.perform_pca(n_components=3)

# Define a taxonomic class
taxonomy = FormalTaxonomySystem()
new_class = taxonomy.define_class_from_reference_group(
    class_name="Savignano",
    reference_objects=[features]
)
```

### Claude Desktop Integration (MCP)

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "archaeological-classifier": {
      "command": "python",
      "args": ["-m", "acs.mcp.server"]
    }
  }
}
```

## Savignano Analysis Workflow

The system includes specialized tools for analyzing Bronze Age axes from the Savignano hoard:

```
1. UPLOAD MULTIPLE MESHES
   Upload 10-96 OBJ files of Bronze Age axes
   Optional: Upload weight data (Excel, CSV, JSON)
   ↓
2. FEATURE EXTRACTION
   Extract 36+ Savignano morphometric parameters:
   - Socket dimensions and profile
   - Butt measurements
   - Blade analysis
   - Raised edges
   ↓
3. MATRIX CLUSTERING
   DBSCAN clustering identifies potential casting dies
   Archaeological QA validates results
   ↓
4. CLASSIFICATION
   Formal taxonomy definition for each matrix group
   AI-powered archaeological interpretation
   ↓
5. REPORT GENERATION
   Comprehensive multi-page PDF with all analysis
```

## Database Schema

SQLite database with the following core tables:

| Table | Purpose |
|-------|---------|
| `artifacts` | 3D mesh registry and metadata |
| `features` | Morphometric measurements |
| `stylistic_features` | Non-morphometric analysis |
| `classifications` | Classification results |
| `training_data` | ML training dataset |
| `analysis_results` | Cached analysis outputs |
| `comparisons` | Similarity results |
| `projects` | Multi-project organization |

## Technologies

### Backend
- **Flask 3.0+** - Web framework
- **SQLite** - Database
- **Anthropic API** - Claude 4.5 Sonnet for AI analysis
- **Trimesh 4.0+** - 3D mesh processing
- **NumPy, SciPy** - Numerical computing
- **Scikit-learn 1.3+** - Machine Learning

### Frontend
- **Jinja2** - HTML templating
- **Three.js** - 3D visualization
- **Bootstrap** - UI framework

### Integration
- **Model Context Protocol (MCP)** - Claude Desktop
- **Dropbox API** - Cloud backup
- **Google Drive** - Cloud storage

## Deployment

### Railway.app (Recommended)

The project includes Railway.app configuration for easy deployment:

```bash
railway login
railway init
railway up
```

### Docker

```bash
docker build -t brozeaxe-ai .
docker run -p 5000:5000 brozeaxe-ai
```

### Manual Deployment

```bash
# Production mode
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Documentation

Comprehensive documentation is available:

- [QUICKSTART.md](archaeological-classifier/QUICKSTART.md) - 5-minute getting started
- [INSTALL.md](archaeological-classifier/INSTALL.md) - Detailed installation
- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Usage workflows
- [SAVIGNANO_QUICK_START.md](archaeological-classifier/SAVIGNANO_QUICK_START.md) - Savignano analysis guide
- [ACS_ARCHITECTURAL_ANALYSIS.md](archaeological-classifier/ACS_ARCHITECTURAL_ANALYSIS.md) - Technical architecture

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Code formatting
black acs/

# Type checking
mypy acs/
```

## Citation

If you use BrozeAXE-AI in your research, please cite:

```bibtex
@software{brozeaxe_ai_2025,
  author = {Cocca, Enzo},
  title = {BrozeAXE-AI: Archaeological Classifier System for Bronze Age Artifacts},
  year = {2025},
  url = {https://github.com/enzococca/BrozeAXE-AI}
}
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Developed for the morphometric analysis of the Savignano bronze axes hoard and similar archaeological assemblages. This project combines traditional archaeological methodology with modern computational techniques to bring rigor and reproducibility to archaeological typology.

---

**BrozeAXE-AI** - Bringing AI-powered precision to archaeological artifact analysis.
