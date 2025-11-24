# 🚀 Get Started with Archaeological Classifier System

Your complete Archaeological Classifier System is ready! Here's how to start using it.

## ✅ What's Been Created

A production-ready Python package with:

- **22 Python modules** implementing complete functionality
- **Complete REST API** with Flask (16 endpoints)
- **MCP Server** for Claude Desktop integration (12 tools)
- **CLI tools** for command-line usage
- **Comprehensive documentation** (README, INSTALL, QUICKSTART)
- **Working example** (Savignano analysis)
- **Test suite** with pytest
- **PyPI-ready** setup and configuration

## 📦 Installation

### Option 1: Install for Development

```bash
cd archaeological-classifier
pip install -e .
```

This installs the package in "editable" mode so you can modify the code.

### Option 2: Install All Dependencies

```bash
cd archaeological-classifier
pip install -e ".[dev]"
```

This includes development tools (pytest, black, mypy).

## 🧪 Quick Test

Verify everything works:

```bash
# Test imports
python -c "from acs import MeshProcessor, MorphometricAnalyzer, FormalTaxonomySystem; print('✅ All imports successful!')"

# Check CLI
acs-cli --version

# Run example (uses simulated data)
python examples/savignano_analysis.py
```

## 🔧 Usage Examples

### 1. Using Python API

```python
from acs import MeshProcessor, FormalTaxonomySystem

# Process a 3D mesh
processor = MeshProcessor()
features = processor.load_mesh("path/to/axe.obj")

# Create taxonomy
taxonomy = FormalTaxonomySystem()
references = [features1, features2, features3]  # Your reference artifacts

new_class = taxonomy.define_class_from_reference_group(
    class_name="Savignano",
    reference_objects=references
)

# Classify new artifact
is_member, confidence, diagnostic = new_class.classify_object(new_features)
print(f"Classification: {is_member}, Confidence: {confidence:.2%}")
```

### 2. Using CLI

```bash
# Process mesh
acs-cli process axe.obj --output features.json

# Batch process directory
acs-cli batch ./meshes --pattern "*.obj"

# Start API server
acs-cli server --port 5000
```

### 3. Using REST API

```bash
# Start server
acs-server --port 5000

# In another terminal, test endpoints
curl http://localhost:5000/api/docs
```

### 4. Using with Claude Desktop

1. **Find your Claude Desktop config file:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add this configuration:**
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

3. **Restart Claude Desktop**

4. **Test in Claude:**
   ```
   List the available archaeological analysis tools
   ```

## 📚 Documentation

- **[README.md](README.md)** - Complete overview and features
- **[INSTALL.md](INSTALL.md)** - Detailed installation guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start tutorial
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Project architecture

## 🎯 Next Steps

### For Your Savignano Axes Analysis

1. **Prepare your data:**
   - Place all OBJ files in a directory
   - Ensure files are named consistently (e.g., `AXE_001.obj`, `AXE_002.obj`)

2. **Modify the example:**
   ```bash
   # Edit examples/savignano_analysis.py
   # Replace simulated data with:
   mesh_directory = Path("/path/to/your/obj/files")
   mesh_files = list(mesh_directory.glob("*.obj"))
   ```

3. **Run the analysis:**
   ```bash
   python examples/savignano_analysis.py
   ```

4. **Review results:**
   - `savignano_taxonomy.json` - Formal taxonomy
   - `savignano_features.json` - Extracted features
   - `savignano_statistics.json` - Analysis statistics

### Extend the System

**Add AI Agents:**
Edit `acs/api/blueprints/agents.py` to integrate LangGraph or CrewAI for archaeological reasoning.

**Add More Features:**
Extend `acs/core/mesh_processor.py` to extract additional features (wear patterns, surface texture, etc.).

**Custom Classifications:**
Create domain-specific classifiers in new modules under `acs/core/`.

## 🛠️ Development Commands

Use the Makefile for common tasks:

```bash
make help          # Show all commands
make install       # Install package
make dev           # Install with dev dependencies
make test          # Run tests
make format        # Format code with black
make run-api       # Start Flask server
make run-mcp       # Start MCP server
make build         # Build for PyPI
make publish-test  # Publish to Test PyPI
make publish       # Publish to PyPI
```

## 📦 Publishing to PyPI

When ready to share your package:

```bash
# 1. Build distribution
make build

# 2. Test on TestPyPI first
make publish-test

# 3. Install from TestPyPI to verify
pip install --index-url https://test.pypi.org/simple/ archaeological-classifier

# 4. If all works, publish to PyPI
make publish
```

## 🐛 Troubleshooting

### Import Errors

```bash
# Reinstall in editable mode
pip install -e .
```

### Missing Dependencies

```bash
# Install all requirements
pip install -r requirements.txt
```

### Claude Desktop Not Showing Tools

1. Check config file location
2. Verify JSON syntax
3. Completely restart Claude Desktop
4. Check logs in `~/Library/Logs/Claude/`

### API Server Won't Start

```bash
# Check if port is in use
lsof -i :5000

# Use different port
acs-server --port 8000
```

## 💡 Tips

1. **Start Small**: Test with 5-10 meshes first
2. **Version Control**: Use git to track taxonomy changes
3. **Document Changes**: Use the modification justification system
4. **Export Regularly**: Save taxonomy snapshots
5. **Validate**: Always check confidence scores

## 📖 Recommended Workflow

```
1. Load & Process Meshes → MeshProcessor
2. Exploratory Analysis → MorphometricAnalyzer (PCA, clustering)
3. Define Classes → FormalTaxonomySystem
4. Classify Artifacts → Classification with diagnostics
5. Refine & Iterate → Modify classes with justification
6. Export & Publish → Share reproducible taxonomy
```

## 🤝 Getting Help

- **Check docs**: Start with QUICKSTART.md
- **Run examples**: Learn from savignano_analysis.py
- **Test installation**: Run the test suite
- **GitHub Issues**: Report bugs or request features

## 🎉 You're Ready!

Everything is set up and ready to use. Start with:

```bash
cd archaeological-classifier
python examples/savignano_analysis.py
```

Then adapt it to your real data!

---

**Archaeological Classifier System** - Built for serious archaeological research with reproducibility and rigor.

Good luck with your Savignano axes analysis! 🏛️
