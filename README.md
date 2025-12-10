# Archaeological Classifier System (ACS)

**Advanced 3D mesh analysis and formal taxonomy system for archaeological artifacts**

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Archaeological Classifier System (ACS) is a comprehensive Python framework for analyzing 3D scanned archaeological artifacts. It combines advanced morphometric analysis, formal parametric taxonomy, and AI-powered reasoning to answer complex archaeological questions.

### Key Features

✅ **3D Mesh Processing** - Load and analyze OBJ, PLY, STL files
✅ **Morphometric Analysis** - PCA, clustering, Procrustes, Elliptic Fourier Analysis
✅ **Formal Taxonomy** - Parametric classification with versioning and traceability
✅ **REST API** - Complete Flask API for all functionalities
✅ **MCP Integration** - Claude Desktop integration via Model Context Protocol
✅ **CLI Tools** - Command-line interface for all operations
✅ **Rigorous Validation** - Statistical validation and confidence scoring

## Installation

### Quick Install

```bash
pip install archaeological-classifier
```

### Development Install

```bash
git clone https://github.com/yourusername/archaeological-classifier.git
cd archaeological-classifier
pip install -e .
```

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## Quick Start

### 1. Process a 3D Mesh

```python
from acs import MeshProcessor

processor = MeshProcessor()
features = processor.load_mesh("path/to/axe.obj", artifact_id="AXE_001")

print(f"Volume: {features['volume']:.2f} mm³")
print(f"Length: {features['length']:.2f} mm")
```

### 2. Define a Taxonomic Class

```python
from acs import FormalTaxonomySystem

taxonomy = FormalTaxonomySystem()

# Reference artifacts from archaeological group
reference_axes = [
    {"id": "AXE_001", "volume": 145.3, "length": 120.5, "width": 65.2},
    {"id": "AXE_002", "volume": 148.1, "length": 122.0, "width": 64.8},
    # ... more reference objects
]

savignano_class = taxonomy.define_class_from_reference_group(
    class_name="Savignano",
    reference_objects=reference_axes
)

print(f"Class created: {savignano_class.class_id}")
print(f"Parameter hash: {savignano_class.parameter_hash}")
```

### 3. Classify New Artifacts

```python
new_axe = {
    "id": "AXE_097",
    "volume": 146.8,
    "length": 121.2,
    "width": 65.0
}

is_member, confidence, diagnostic = savignano_class.classify_object(new_axe)

print(f"Belongs to Savignano: {is_member}")
print(f"Confidence: {confidence:.2%}")
```

## Architecture

### Core Modules

- **`acs.core.mesh_processor`** - 3D mesh loading and feature extraction
- **`acs.core.morphometric`** - Advanced morphometric analysis
- **`acs.core.taxonomy`** - Formal parametric taxonomy system

### API & Integration

- **`acs.api`** - Flask REST API with complete endpoint coverage
- **`acs.mcp`** - Model Context Protocol server for Claude Desktop
- **`acs.cli`** - Command-line interface

## Use Cases

### Archaeological Questions Answered

This system was designed to answer questions like:

1. **How many casting matrices were used?**
   → Clustering identifies distinct groups from the same matrix

2. **How many castings per matrix?**
   → Count artifacts per cluster

3. **What post-casting treatments were applied?**
   → Technological parameter analysis (hammering, filing)

4. **How much were the artifacts used?**
   → Wear analysis on cutting edge

5. **Why the socket in the butt?**
   → Functional analysis and interpretation

### Example: Savignano Bronze Axes

```python
# See examples/savignano_analysis.py for complete workflow
from acs import MeshProcessor, MorphometricAnalyzer, FormalTaxonomySystem

# 1. Process 96 OBJ files
processor = MeshProcessor()
results = processor.batch_process(obj_files)

# 2. Morphometric analysis
analyzer = MorphometricAnalyzer()
for result in results:
    analyzer.add_features(result['artifact_id'], result['features'])

clustering = analyzer.hierarchical_clustering(n_clusters=None, distance_threshold=0.5)
print(f"Identified {clustering['n_clusters']} potential matrices")

# 3. Define classes from clusters
taxonomy = FormalTaxonomySystem()
for cluster_id, artifact_ids in clustering['clusters'].items():
    cluster_objects = [get_features(aid) for aid in artifact_ids]

    taxonomy.define_class_from_reference_group(
        class_name=f"Matrix_{cluster_id}",
        reference_objects=cluster_objects
    )

# 4. Export for publication
taxonomy.export_taxonomy("savignano_taxonomy.json")
```

## REST API

Start the API server:

```bash
acs-server --port 5000
```

### Endpoints

**Mesh Processing**
- `POST /api/mesh/upload` - Upload and process mesh
- `POST /api/mesh/batch` - Batch processing
- `GET /api/mesh/<id>` - Get artifact features

**Morphometric Analysis**
- `POST /api/morphometric/pca` - PCA analysis
- `POST /api/morphometric/cluster` - Clustering
- `POST /api/morphometric/find-similar` - Similarity search

**Classification**
- `POST /api/classification/define-class` - Define taxonomic class
- `POST /api/classification/classify` - Classify artifact
- `POST /api/classification/modify-class` - Modify class (tracked)
- `GET /api/classification/classes` - List all classes

See full API documentation at `/api/docs`.

## Claude Desktop Integration

Archaeological Classifier System integrates with Claude Desktop via the Model Context Protocol (MCP).

### Setup

1. Install ACS:
   ```bash
   pip install archaeological-classifier
   ```

2. Configure Claude Desktop (see [INSTALL.md](INSTALL.md) for detailed instructions):
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

3. Restart Claude Desktop

### Available Tools

- `process_mesh` - Process 3D mesh files
- `morphometric_analysis` - PCA, clustering, similarity
- `define_taxonomic_class` - Create formal classes
- `classify_artifact` - Classify artifacts
- `modify_class_parameters` - Modify classes (with justification)
- `discover_new_classes` - Automatic class discovery
- And more...

## Formal Taxonomy System

### Key Principles

✅ **Explicit Parameters** - Every class defined by quantitative parameters
✅ **Versioning** - Complete version history with MD5 hashing
✅ **Traceability** - All modifications logged with justification
✅ **Reproducibility** - Same parameters = same classification
✅ **Statistical Validation** - Confidence scores and diagnostics

### Parameter Types

1. **Morphometric** - Geometric features (volume, length, width)
2. **Technological** - Manufacturing features (socket depth, edge angle)
3. **Optional** - Presence/absence features (socket, midrib)

### Modification Control

```python
# Modifications require justification and create new versions
new_class = taxonomy.modify_class_parameters(
    class_id="TYPE_SAVIGNANO_20250104_123456",
    parameter_changes={
        "morphometric": {
            "length": {"min_threshold": 115.0, "max_threshold": 130.0}
        }
    },
    justification="Range expansion after discovery of 3 new specimens",
    operator="Enzo Ferroni"
)

# New version created: TYPE_SAVIGNANO_20250104_123456_v2
# Original class preserved in version history
```

## CLI Usage

```bash
# Process single mesh
acs-cli process axe.obj --output features.json

# Batch process directory
acs-cli batch ./meshes --pattern "*.obj" --output batch_results.json

# Define taxonomic class
acs-cli define-class "Savignano" references.json --output class.json

# Classify artifact
acs-cli classify artifact.json taxonomy.json

# List classes
acs-cli list-classes taxonomy.json

# Start API server
acs-cli server --port 5000 --debug
```

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

### Code Formatting

```bash
black acs/
```

### Type Checking

```bash
mypy acs/
```

## Publishing to PyPI

```bash
# Build distribution
python -m build

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Citation

If you use Archaeological Classifier System in your research, please cite:

```bibtex
@software{archaeological_classifier_2025,
  author = {Ferroni, Enzo},
  title = {Archaeological Classifier System: Advanced 3D Analysis and Formal Taxonomy},
  year = {2025},
  url = {https://github.com/yourusername/archaeological-classifier}
}
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/archaeological-classifier/issues)
- **Documentation**: [Full Documentation](https://github.com/yourusername/archaeological-classifier#readme)
- **Examples**: See `examples/` directory

## Acknowledgments

Developed for the analysis of the Savignano bronze axes hoard and similar archaeological assemblages.

---

**Archaeological Classifier System** - Bringing rigor and reproducibility to archaeological typology.
