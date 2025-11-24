# Project Structure

Complete structure of the Archaeological Classifier System project.

```
archaeological-classifier/
│
├── acs/                              # Main package
│   ├── __init__.py                  # Package initialization
│   │
│   ├── core/                        # Core analysis modules
│   │   ├── __init__.py
│   │   ├── mesh_processor.py       # 3D mesh loading & feature extraction
│   │   ├── morphometric.py         # PCA, clustering, similarity analysis
│   │   └── taxonomy.py             # Formal parametric taxonomy system
│   │
│   ├── api/                         # Flask REST API
│   │   ├── __init__.py
│   │   ├── app.py                  # Flask application factory
│   │   └── blueprints/             # API endpoints
│   │       ├── __init__.py
│   │       ├── mesh.py             # Mesh upload & processing endpoints
│   │       ├── morphometric.py     # Morphometric analysis endpoints
│   │       ├── classification.py   # Classification endpoints
│   │       └── agents.py           # AI agents endpoints (placeholder)
│   │
│   ├── mcp/                         # Model Context Protocol
│   │   ├── __init__.py
│   │   └── server.py               # MCP server for Claude Desktop
│   │
│   ├── models/                      # Data models (Pydantic)
│   │   ├── __init__.py
│   │   ├── artifact.py             # Artifact data models
│   │   └── classification.py       # Classification models
│   │
│   └── cli.py                       # Command-line interface
│
├── tests/                           # Test suite
│   ├── __init__.py
│   └── test_taxonomy.py            # Taxonomy system tests
│
├── examples/                        # Usage examples
│   └── savignano_analysis.py       # Complete workflow example
│
├── docs/                            # Documentation (empty, for future)
│
├── setup.py                         # Package setup (setuptools)
├── pyproject.toml                  # Modern build configuration
├── requirements.txt                # Dependencies
├── MANIFEST.in                     # Package data inclusion
│
├── README.md                       # Main documentation
├── INSTALL.md                      # Installation guide
├── QUICKSTART.md                   # Quick start guide
├── LICENSE                         # MIT License
│
├── .gitignore                      # Git ignore rules
├── Makefile                        # Task automation
├── claude_desktop_config.json     # Example MCP configuration
│
└── PROJECT_STRUCTURE.md           # This file
```

## Module Descriptions

### Core Modules

**`acs.core.mesh_processor.MeshProcessor`**
- Load 3D mesh files (OBJ, PLY, STL)
- Extract geometric features (volume, dimensions, curvature)
- Batch processing
- Distance computation between meshes

**`acs.core.morphometric.MorphometricAnalyzer`**
- Principal Component Analysis (PCA)
- Hierarchical clustering
- DBSCAN clustering
- Similarity matrix computation
- Procrustes superimposition
- Elliptic Fourier Analysis support

**`acs.core.taxonomy.FormalTaxonomySystem`**
- Parametric class definition
- Object classification with confidence scoring
- Parameter modification with versioning
- Automatic class discovery
- Import/export functionality
- Complete audit trail

### API Blueprints

**`/api/mesh`** - Mesh Processing
- `POST /upload` - Upload and process mesh
- `POST /batch` - Batch processing
- `GET /<id>` - Get artifact features
- `GET /<id1>/distance/<id2>` - Compute distance

**`/api/morphometric`** - Morphometric Analysis
- `POST /add-features` - Add features for analysis
- `POST /pca` - Fit PCA model
- `POST /cluster` - Hierarchical clustering
- `POST /dbscan` - DBSCAN clustering
- `POST /similarity` - Similarity matrix
- `POST /find-similar` - Find similar artifacts

**`/api/classification`** - Taxonomy Management
- `POST /define-class` - Define new class
- `POST /classify` - Classify artifact
- `POST /modify-class` - Modify class (versioned)
- `POST /discover` - Discover new classes
- `GET /classes` - List all classes
- `GET /classes/<id>` - Get class details
- `GET /export` - Export taxonomy
- `POST /import` - Import taxonomy
- `GET /statistics` - Get statistics

**`/api/agents`** - AI Agents (Placeholder)
- `POST /analyze` - Multi-agent analysis
- `POST /ask` - Ask archaeological question

### MCP Tools (12 total)

1. `process_mesh` - Process 3D mesh file
2. `batch_process_meshes` - Batch process multiple meshes
3. `morphometric_analysis` - PCA, clustering, similarity
4. `find_similar_artifacts` - Find similar artifacts
5. `define_taxonomic_class` - Define formal class
6. `classify_artifact` - Classify artifact
7. `modify_class_parameters` - Modify class (tracked)
8. `discover_new_classes` - Auto-discover classes
9. `list_classes` - List all classes
10. `get_class_details` - Get class information
11. `export_taxonomy` - Export to JSON
12. `get_taxonomy_statistics` - Get statistics

### CLI Commands

```bash
acs-cli process <file>              # Process single mesh
acs-cli batch <directory>           # Batch process
acs-cli define-class <name> <refs>  # Define class
acs-cli classify <features> <tax>   # Classify artifact
acs-cli list-classes <taxonomy>     # List classes
acs-cli server                       # Start API server
```

## File Count Summary

- **Python files**: 22
- **Documentation**: 3 (README, INSTALL, QUICKSTART)
- **Configuration**: 7 (setup.py, pyproject.toml, requirements.txt, etc.)
- **Examples**: 1 (savignano_analysis.py)
- **Tests**: 1 (test_taxonomy.py)

## Key Features

### 1. Formal Taxonomy System
- Explicit quantitative parameters
- MD5 hash-based versioning
- Complete modification history
- Mandatory justifications
- Statistical validation

### 2. Integration Options
- **REST API**: Flask server for HTTP access
- **MCP**: Claude Desktop integration
- **CLI**: Command-line tools
- **Python API**: Direct import and use

### 3. Scalability
- Modular architecture
- Extensible blueprints
- Plugin-ready agents system
- Async MCP server

## Dependencies

**Core Scientific**
- numpy, scipy, scikit-learn
- trimesh, networkx

**Web & API**
- flask, flask-cors, werkzeug
- pydantic

**Integration**
- mcp (Model Context Protocol)
- click (CLI)

**Optional**
- pandas (data export)
- pyefd (Elliptic Fourier Analysis)
- pytest (testing)

## Next Steps

1. **Installation**: Follow INSTALL.md
2. **Quick Start**: Follow QUICKSTART.md
3. **Examples**: Run examples/savignano_analysis.py
4. **API**: Start server with `acs-cli server`
5. **Claude Integration**: Configure claude_desktop_config.json

## Publishing

Ready for PyPI publication:

```bash
make build          # Build distribution
make publish-test   # Test on TestPyPI
make publish        # Publish to PyPI
```

---

**Archaeological Classifier System v0.1.0**
