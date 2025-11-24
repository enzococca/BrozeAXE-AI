# 🚀 Launch Web Interface

## Quick Start

### Method 1: Run Script (Recommended)

```bash
cd archaeological-classifier
python run_web.py
```

Then open: **http://localhost:5000/web/**

### Method 2: CLI Command

```bash
acs-cli server --port 5000
```

Then open: **http://localhost:5000/web/**

### Method 3: Python Module

```bash
python -m flask --app acs.api.app run --debug
```

Then open: **http://localhost:5000/web/**

## What You'll See

### 🏠 Dashboard
- Statistics overview
- Quick actions
- System status

### 📤 Upload
- Drag & drop mesh files (OBJ, PLY, STL)
- Multi-file upload
- Real-time progress

### 📦 Artifacts
- Browse loaded meshes
- Search functionality
- View details

### 📊 Analysis
- PCA analysis with scree plots
- Clustering (Hierarchical & DBSCAN)
- Interactive visualizations

### 🏷️ Taxonomy
- Define formal classes
- Classify artifacts
- View confidence scores

## Features

✅ Modern, responsive UI
✅ Drag-and-drop file upload
✅ Real-time processing feedback
✅ Interactive visualizations (Plotly.js)
✅ Search and filter
✅ Export functionality
✅ Mobile-friendly design

## Screenshots

### Dashboard
```
┌────────────────────────────────────────┐
│   🏛️ Archaeological Classifier        │
├────────────────────────────────────────┤
│  Dashboard  Upload  Artifacts  ...     │
├────────────────────────────────────────┤
│                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  │
│  │ 📦  │  │ 📊  │  │ 🏷️  │  │ ✓  │  │
│  │  5  │  │  5  │  │  2  │  │ 10 │  │
│  │Mesh │  │Feat │  │Cls  │  │Clf │  │
│  └─────┘  └─────┘  └─────┘  └─────┘  │
│                                         │
│  Quick Actions:                         │
│  [📤 Upload] [📊 Analyze] [💾 Export] │
│                                         │
└────────────────────────────────────────┘
```

### Upload Interface
```
┌────────────────────────────────────────┐
│   Upload 3D Meshes                      │
├────────────────────────────────────────┤
│                                         │
│  ╔═══════════════════════════════════╗ │
│  ║        📦                         ║ │
│  ║  Drag and drop files here         ║ │
│  ║  or click to browse               ║ │
│  ║                                   ║ │
│  ║  Supported: OBJ, PLY, STL         ║ │
│  ║                                   ║ │
│  ║  [Choose Files]                   ║ │
│  ╚═══════════════════════════════════╝ │
│                                         │
│  Selected Files (3):                    │
│  📄 axe_001.obj      2.3 MB      [×]   │
│  📄 axe_002.obj      2.1 MB      [×]   │
│  📄 axe_003.obj      2.4 MB      [×]   │
│                                         │
│  [Upload Selected] [Clear All]          │
│                                         │
└────────────────────────────────────────┘
```

### Analysis Page
```
┌────────────────────────────────────────┐
│   Morphometric Analysis                 │
├────────────────────────────────────────┤
│                                         │
│  PCA Configuration:                     │
│  Components: [Auto]                     │
│  Variance: [0.95]                       │
│  [Run PCA]                              │
│                                         │
│  ✓ PCA completed                        │
│  Components: 5                          │
│  Variance: 96.3%                        │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │     PCA Scree Plot               │  │
│  │  %  ██████                       │  │
│  │  50 ████                         │  │
│  │  30 ██                           │  │
│  │  10 █                            │  │
│  │     PC1 PC2 PC3 PC4 PC5          │  │
│  └──────────────────────────────────┘  │
│                                         │
└────────────────────────────────────────┘
```

## Accessing from Other Devices

If you want to access from another device on your network:

1. **Find your IP:**
   ```bash
   # macOS/Linux
   ifconfig | grep "inet "

   # Windows
   ipconfig
   ```

2. **Start server on 0.0.0.0:**
   ```bash
   python run_web.py
   # Server runs on 0.0.0.0:5000
   ```

3. **Access from other device:**
   ```
   http://YOUR_IP:5000/web/
   ```

## Troubleshooting

### Port 5000 Already in Use

```bash
# Option 1: Kill process
lsof -ti:5000 | xargs kill -9

# Option 2: Use different port
# Edit run_web.py and change port=5000 to port=8000
```

### Styles Not Loading

1. Clear browser cache (Cmd+Shift+R / Ctrl+Shift+R)
2. Check console for errors (F12)
3. Verify static files exist:
   ```bash
   ls -la acs/web/static/css/style.css
   ```

### Upload Fails

Check upload folder:
```bash
ls -la /tmp/acs_uploads
# If doesn't exist:
mkdir -p /tmp/acs_uploads
chmod 755 /tmp/acs_uploads
```

### Analysis Returns Error

- Need at least 2 artifacts loaded
- Upload some meshes first

## Tips

1. **Start Simple:** Upload 2-3 files first to test
2. **Use Chrome/Firefox:** Best browser compatibility
3. **Keep Terminal Open:** See real-time logs
4. **Bookmark:** Add http://localhost:5000/web/ to bookmarks

## Stopping the Server

Press **Ctrl+C** in the terminal where server is running

## Next Steps

After launching:

1. ✅ Upload some test OBJ files
2. ✅ Browse artifacts
3. ✅ Run PCA analysis
4. ✅ Define a test class
5. ✅ Classify an artifact
6. ✅ Export results

## Full Documentation

See [WEB_INTERFACE.md](WEB_INTERFACE.md) for complete documentation.

---

**Ready to Launch!** 🚀

```bash
python run_web.py
```

Then visit: **http://localhost:5000/web/**
