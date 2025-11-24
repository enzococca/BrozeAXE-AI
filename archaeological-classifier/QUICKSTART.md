# Quick Start Guide

Get up and running with Archaeological Classifier System in 5 minutes.

## Installation

```bash
pip install archaeological-classifier
```

## Basic Workflow

### 1. Process a 3D Mesh

```python
from acs import MeshProcessor

# Create processor
processor = MeshProcessor()

# Load and analyze mesh
features = processor.load_mesh("bronze_axe.obj", artifact_id="AXE_001")

# View extracted features
print(f"Volume: {features['volume']:.2f} mm³")
print(f"Length: {features['length']:.2f} mm")
print(f"Width: {features['width']:.2f} mm")
```

### 2. Batch Process Multiple Meshes

```python
# Process all OBJ files in a directory
from pathlib import Path

obj_files = list(Path("./meshes").glob("*.obj"))
results = processor.batch_process([str(f) for f in obj_files])

# Extract features for analysis
all_features = [r['features'] for r in results if r['status'] == 'success']
print(f"Processed {len(all_features)} artifacts")
```

### 3. Morphometric Analysis

```python
from acs import MorphometricAnalyzer

# Create analyzer
analyzer = MorphometricAnalyzer()

# Add features
for features in all_features:
    analyzer.add_features(features['id'], features)

# Perform PCA
pca_results = analyzer.fit_pca(explained_variance=0.95)
print(f"Components: {pca_results['n_components']}")
print(f"Variance explained: {pca_results['cumulative_variance'][-1]:.2%}")

# Hierarchical clustering
clustering = analyzer.hierarchical_clustering(n_clusters=5)
print(f"Clusters: {clustering['clusters']}")
```

### 4. Define Taxonomic Classes

```python
from acs import FormalTaxonomySystem

# Create taxonomy system
taxonomy = FormalTaxonomySystem()

# Get artifacts from first cluster as reference
cluster_0 = clustering['clusters'][0]
reference_features = [f for f in all_features if f['id'] in cluster_0]

# Define formal class
savignano_class = taxonomy.define_class_from_reference_group(
    class_name="Savignano_Type_A",
    reference_objects=reference_features,
    parameter_weights={
        'length': 1.5,      # More important
        'volume': 1.0,
        'width': 1.2,
    },
    tolerance_factor=0.15  # 15% tolerance
)

print(f"Class created: {savignano_class.name}")
print(f"Class ID: {savignano_class.class_id}")
print(f"Parameter hash: {savignano_class.parameter_hash}")
```

### 5. Classify New Artifacts

```python
# Classify a new artifact
new_axe = {
    'id': 'AXE_NEW',
    'volume': 146.5,
    'length': 121.0,
    'width': 65.3,
    'thickness': 12.1
}

is_member, confidence, diagnostic = savignano_class.classify_object(new_axe)

print(f"Belongs to {savignano_class.name}: {is_member}")
print(f"Confidence: {confidence:.2%}")

# View detailed diagnostic
for param, details in diagnostic.items():
    if details['status'] == 'PASS':
        print(f"  {param}: ✓ (measured: {details['measured']:.2f})")
```

### 6. Export and Share

```python
# Export taxonomy for reproducibility
taxonomy.export_taxonomy("my_taxonomy.json")

# Get statistics
stats = taxonomy.get_statistics()
print(f"Total classes: {stats['n_classes']}")
print(f"Total classifications: {stats['total_classifications']}")
```

## Using the CLI

### Process Meshes

```bash
# Single file
acs-cli process axe.obj --output features.json

# Batch process directory
acs-cli batch ./meshes --pattern "*.obj" --output results.json
```

### Classification

```bash
# Define class from references
acs-cli define-class "Savignano" references.json --output class.json

# Classify artifact
acs-cli classify artifact.json taxonomy.json
```

### API Server

```bash
# Start server
acs-cli server --port 5000

# Test endpoint
curl http://localhost:5000/api/docs
```

## Using the REST API

### Start Server

```bash
acs-server --port 5000
```

### Upload Mesh

```bash
curl -X POST http://localhost:5000/api/mesh/upload \
  -F "file=@axe.obj" \
  -F "artifact_id=AXE_001"
```

### Define Class

```bash
curl -X POST http://localhost:5000/api/classification/define-class \
  -H "Content-Type: application/json" \
  -d '{
    "class_name": "Savignano",
    "reference_objects": [...]
  }'
```

## Claude Desktop Integration

### 1. Configure

Edit Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

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

### 2. Use in Claude

After restarting Claude Desktop:

```
Process the mesh file at /path/to/axe.obj and extract features
```

```
Define a new taxonomic class called "Savignano" using these reference artifacts: [...]
```

```
Classify this artifact: {"volume": 145, "length": 120, "width": 65}
```

## Example: Complete Analysis Workflow

```python
from acs import MeshProcessor, MorphometricAnalyzer, FormalTaxonomySystem
from pathlib import Path

# 1. Load all meshes
processor = MeshProcessor()
mesh_files = list(Path("./savignano_axes").glob("*.obj"))
results = processor.batch_process([str(f) for f in mesh_files])
features_list = [r['features'] for r in results if r['status'] == 'success']

print(f"Loaded {len(features_list)} artifacts")

# 2. Clustering to identify groups
analyzer = MorphometricAnalyzer()
for features in features_list:
    analyzer.add_features(features['id'], features)

clustering = analyzer.hierarchical_clustering(n_clusters=4)
print(f"Identified {clustering['n_clusters']} groups")

# 3. Define formal classes for each group
taxonomy = FormalTaxonomySystem()

for cluster_id, artifact_ids in clustering['clusters'].items():
    cluster_features = [f for f in features_list if f['id'] in artifact_ids]

    if len(cluster_features) >= 3:  # Minimum for reliable class
        tax_class = taxonomy.define_class_from_reference_group(
            class_name=f"Group_{cluster_id}",
            reference_objects=cluster_features
        )
        print(f"Defined class: {tax_class.name} ({len(cluster_features)} specimens)")

# 4. Export results
taxonomy.export_taxonomy("savignano_taxonomy.json")
analyzer.export_features("savignano_features.json")

print("Analysis complete!")
```

## Common Patterns

### Finding Similar Artifacts

```python
# Find 5 most similar to a query
similar = analyzer.find_most_similar(
    query_id="AXE_001",
    n=5,
    metric='euclidean'
)

for artifact_id, similarity in similar:
    print(f"{artifact_id}: {similarity:.2%} similar")
```

### Modifying Classes (with Tracking)

```python
# All modifications are logged and versioned
new_version = taxonomy.modify_class_parameters(
    class_id="TYPE_SAVIGNANO_20250104_120000",
    parameter_changes={
        "morphometric": {
            "length": {"max_threshold": 135.0}  # Expand range
        }
    },
    justification="New specimens found with greater length",
    operator="Enzo Ferroni"
)

print(f"New version: {new_version.class_id}")
# Original preserved in version_history
```

### Automatic Class Discovery

```python
# Find unclassified artifacts
unclassified = [f for f in all_features if not_yet_classified(f)]

# Discover new classes automatically
new_classes = taxonomy.discover_new_classes(
    unclassified_objects=unclassified,
    min_cluster_size=5,
    eps=0.3
)

print(f"Discovered {len(new_classes)} new types")
```

## Next Steps

- Review the [full documentation](README.md)
- Explore [examples/](examples/) for real-world use cases
- Check out the [API reference](README.md#rest-api)
- Try the Claude Desktop integration

## Getting Help

- **Documentation**: [README.md](README.md)
- **Installation Issues**: [INSTALL.md](INSTALL.md)
- **GitHub Issues**: [Report bugs](https://github.com/yourusername/archaeological-classifier/issues)

---

**Ready to start analyzing?** 🏛️
