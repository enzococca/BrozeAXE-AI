# Installation Guide

Complete installation instructions for Archaeological Classifier System.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Dependency Installation](#dependency-installation)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **Python**: 3.9 or higher
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk Space**: 500 MB for installation + space for mesh files
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 20.04+)

### Recommended Setup

- **Python**: 3.11+
- **RAM**: 16 GB (for large batch processing)
- **CPU**: Multi-core processor for parallel processing
- **GPU**: Optional, not currently utilized

## Installation Methods

### Method 1: PyPI (Recommended)

```bash
pip install archaeological-classifier
```

This installs the latest stable release from PyPI.

### Method 2: Development Install

For development or to use the latest features:

```bash
# Clone repository
git clone https://github.com/yourusername/archaeological-classifier.git
cd archaeological-classifier

# Install in editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Method 3: From Source

```bash
# Download and extract source
wget https://github.com/yourusername/archaeological-classifier/archive/main.zip
unzip main.zip
cd archaeological-classifier-main

# Install
pip install .
```

## Dependency Installation

### Core Dependencies

ACS requires several scientific computing libraries:

```bash
# Install core dependencies explicitly
pip install numpy scipy scikit-learn
pip install trimesh networkx
pip install flask flask-cors
pip install pydantic mcp click
```

### Optional Dependencies

#### For Elliptic Fourier Analysis

```bash
pip install pyefd
```

#### For Development

```bash
pip install pytest pytest-cov black mypy
```

#### For Data Export

```bash
pip install pandas openpyxl
```

## Claude Desktop Integration

Archaeological Classifier System integrates seamlessly with Claude Desktop via MCP.

### Step-by-Step Setup

#### 1. Install ACS

```bash
pip install archaeological-classifier
```

#### 2. Verify Installation

```bash
python -c "import acs; print(acs.__version__)"
# Should output: 0.1.0
```

#### 3. Locate Configuration File

Find your Claude Desktop configuration file:

**macOS:**
```bash
~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

#### 4. Configure MCP Server

Open the configuration file and add the MCP server:

```json
{
  "mcpServers": {
    "archaeological-classifier": {
      "command": "python",
      "args": ["-m", "acs.mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

**Important**: If you installed ACS in a virtual environment, use the full path to Python:

```json
{
  "mcpServers": {
    "archaeological-classifier": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "acs.mcp.server"]
    }
  }
}
```

To find your Python path:

```bash
# macOS/Linux
which python

# Windows
where python
```

#### 5. Restart Claude Desktop

Completely quit and restart Claude Desktop for changes to take effect.

#### 6. Verify MCP Integration

In Claude Desktop, you should see the archaeological-classifier tools available. Test with:

```
List the available archaeological analysis tools
```

Claude should respond with the available MCP tools.

## Verification

### Test Installation

Create a test script `test_install.py`:

```python
#!/usr/bin/env python3
"""Test ACS installation."""

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from acs import MeshProcessor, MorphometricAnalyzer, FormalTaxonomySystem
        print("✓ Core modules imported")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    try:
        from acs.api import create_app
        print("✓ API module imported")
    except ImportError as e:
        print(f"✗ API import failed: {e}")
        return False

    try:
        import trimesh
        import numpy
        import scipy
        import sklearn
        print("✓ Dependencies available")
    except ImportError as e:
        print(f"✗ Dependency missing: {e}")
        return False

    return True

def test_basic_functionality():
    """Test basic functionality."""
    print("\nTesting basic functionality...")

    from acs import FormalTaxonomySystem

    taxonomy = FormalTaxonomySystem()

    reference = [
        {"id": "test_1", "volume": 100, "length": 50},
        {"id": "test_2", "volume": 105, "length": 52},
    ]

    try:
        test_class = taxonomy.define_class_from_reference_group(
            class_name="TestClass",
            reference_objects=reference
        )
        print(f"✓ Created test class: {test_class.class_id}")
    except Exception as e:
        print(f"✗ Class creation failed: {e}")
        return False

    return True

if __name__ == "__main__":
    print("Archaeological Classifier System - Installation Test")
    print("=" * 60)

    if test_imports() and test_basic_functionality():
        print("\n✅ Installation successful!")
    else:
        print("\n❌ Installation incomplete or errors detected")
```

Run the test:

```bash
python test_install.py
```

### Test CLI

```bash
# Test CLI is available
acs-cli --version

# Test server startup
acs-cli server --help
```

### Test MCP Server

```bash
# Run MCP server directly
python -m acs.mcp.server
```

The server should start without errors.

## Troubleshooting

### Common Issues

#### Issue 1: `ModuleNotFoundError: No module named 'acs'`

**Solution**: Install ACS properly

```bash
pip install archaeological-classifier
# or
pip install -e .
```

#### Issue 2: `ImportError: No module named 'trimesh'`

**Solution**: Install missing dependencies

```bash
pip install trimesh networkx
```

#### Issue 3: Claude Desktop doesn't show MCP tools

**Solutions**:

1. Check configuration file location
2. Verify JSON syntax (use a JSON validator)
3. Ensure Python path is correct
4. Completely restart Claude Desktop (Quit, not just close window)
5. Check Claude Desktop logs:

**macOS:**
```bash
~/Library/Logs/Claude/mcp*.log
```

#### Issue 4: Permission denied errors

**Solution**: Install in user directory

```bash
pip install --user archaeological-classifier
```

#### Issue 5: Version conflicts

**Solution**: Use virtual environment

```bash
python -m venv acs_env
source acs_env/bin/activate  # macOS/Linux
# or
acs_env\Scripts\activate  # Windows

pip install archaeological-classifier
```

### Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/yourusername/archaeological-classifier/issues)
2. Verify all dependencies are installed: `pip list`
3. Check Python version: `python --version`
4. Review error logs

### Platform-Specific Notes

#### macOS

- May need to install Xcode Command Line Tools:
  ```bash
  xcode-select --install
  ```

#### Windows

- Install Microsoft C++ Build Tools if trimesh compilation fails
- Use Git Bash or PowerShell for better command-line experience

#### Linux

- May need to install system dependencies:
  ```bash
  sudo apt-get update
  sudo apt-get install python3-dev build-essential
  ```

## Next Steps

After successful installation:

1. Read the [Quick Start Guide](QUICKSTART.md)
2. Explore the [examples/](examples/) directory
3. Review the [API documentation](README.md#rest-api)
4. Try the Claude Desktop integration

---

**Need help?** Open an issue on [GitHub](https://github.com/yourusername/archaeological-classifier/issues)
