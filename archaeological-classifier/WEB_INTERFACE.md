# Web Interface Documentation

## Overview

Archaeological Classifier System now includes a modern web interface for interactive analysis!

## Features

✅ **Dashboard** - Overview of your project with statistics
✅ **Upload Interface** - Drag-and-drop mesh file upload (OBJ, PLY, STL)
✅ **Artifacts Browser** - Browse and explore loaded 3D artifacts
✅ **Morphometric Analysis** - Interactive PCA and clustering
✅ **Taxonomy Management** - Define and manage formal taxonomic classes
✅ **Classification** - Classify artifacts with confidence scores
✅ **Visualizations** - Interactive charts with Plotly.js
✅ **Real-time Updates** - Live progress indicators
✅ **Export Functionality** - Download results and data

## Quick Start

### 1. Start the Web Server

```bash
# Option 1: Using the launcher script
python run_web.py

# Option 2: Using CLI
acs-cli server --port 5000

# Option 3: Direct Python
python -m flask --app acs.api.app run --debug
```

### 2. Access the Interface

Open your browser and navigate to:

**http://localhost:5000/web/**

## Pages Overview

### 🏠 Dashboard (`/web/`)

Main overview page showing:
- Total meshes loaded
- Features analyzed
- Classes defined
- Recent activity
- Quick actions
- System status

**Quick Actions:**
- Upload Meshes → Direct link to upload page
- Run Analysis → Quick PCA analysis
- Manage Taxonomy → Access taxonomy management
- Export Data → Export taxonomy or features

### 📤 Upload (`/web/upload`)

Upload 3D mesh files:
- **Drag and drop** support
- Multiple file selection
- Supported formats: OBJ, PLY, STL
- Real-time upload progress
- Automatic processing
- Success/error feedback

**Usage:**
1. Click "Choose Files" or drag files onto the upload zone
2. Review selected files
3. Click "Upload Selected Files"
4. Wait for processing to complete
5. View uploaded artifacts in the Artifacts page

### 📦 Artifacts Browser (`/web/artifacts`)

Browse all loaded 3D artifacts:
- Grid view of all artifacts
- Search functionality
- Key metrics displayed:
  - Volume
  - Length
  - Width
  - Number of vertices/faces
- Click any artifact to view details

### 🔍 Artifact Details (`/web/artifact/<id>`)

Detailed view of single artifact:
- All geometric features
- Mesh properties
- Actions:
  - Find similar artifacts
  - Classify this artifact
  - Export features to JSON

### 📊 Morphometric Analysis (`/web/morphometric`)

Interactive analysis interface:

**PCA (Principal Component Analysis):**
- Set number of components (or auto-detect)
- Set variance threshold
- View scree plot
- See variance explained per component

**Clustering:**
- **Hierarchical Clustering:**
  - Choose number of clusters
  - Select linkage method (Ward, Complete, Average)
- **DBSCAN:**
  - Set epsilon parameter
  - Set minimum samples
- View cluster distribution
- Interactive visualizations

### 🏷️ Taxonomy Management (`/web/taxonomy`)

Define and manage formal taxonomic classes:

**Define New Class:**
1. Enter class name
2. Specify reference artifact IDs (comma-separated)
3. Set tolerance factor (default 0.15)
4. Click "Define Class"

**View Defined Classes:**
- Card view of all classes
- Key information:
  - Number of reference samples
  - Number of parameters
  - Confidence threshold
  - Creation date
- Actions per class:
  - View details
  - Use for classification

**Classify Artifact:**
1. Enter artifact ID
2. Click "Classify"
3. View results with confidence scores
4. See top 5 matches

## Technology Stack

### Backend
- **Flask** - Web framework
- **Flask-CORS** - CORS support
- All existing ACS core modules

### Frontend
- **HTML5/CSS3** - Structure and styling
- **Vanilla JavaScript** - Interactivity
- **Plotly.js** - Interactive visualizations
- **Modern CSS** - Responsive design with CSS Grid/Flexbox

### Design Principles
- **Clean & Modern** - Professional archaeological research tool
- **Responsive** - Works on desktop and tablets
- **Accessible** - Clear labels and semantic HTML
- **Fast** - Minimal dependencies, optimized assets

## API Endpoints (Web Blueprint)

All web endpoints are under `/web/`:

### Pages (GET)
- `/web/` - Dashboard
- `/web/upload` - Upload page
- `/web/artifacts` - Artifacts browser
- `/web/artifact/<id>` - Artifact details
- `/web/morphometric` - Analysis page
- `/web/taxonomy` - Taxonomy management

### Actions (POST)
- `/web/upload-mesh` - Handle mesh upload
- `/web/run-pca` - Execute PCA analysis
- `/web/run-clustering` - Execute clustering
- `/web/define-class` - Define new class
- `/web/classify-artifact` - Classify artifact
- `/web/export-data` - Export data

### Data (GET)
- `/web/statistics` - Get current statistics (JSON)

## Color Scheme

The interface uses a modern, archaeological-themed color palette:

- **Primary Blue:** #4361ee - Main actions, links
- **Secondary Purple:** #7209b7 - Secondary actions
- **Success Green:** #06d6a0 - Success states
- **Warning Yellow:** #ffd60a - Warnings
- **Danger Red:** #ef476f - Errors
- **Dark Text:** #2b2d42 - Primary text
- **Light Background:** #f8f9fa - Page background

## Customization

### Change Upload Folder

Set environment variable:

```bash
export UPLOAD_FOLDER="/path/to/uploads"
python run_web.py
```

### Modify Styles

Edit `acs/web/static/css/style.css`

CSS variables are defined in `:root`:

```css
:root {
    --primary-color: #4361ee;
    --secondary-color: #7209b7;
    /* ... etc */
}
```

### Add Custom Pages

1. Create template in `acs/web/templates/`
2. Add route in `acs/web/routes.py`
3. Add navigation link in `base.html`

## Troubleshooting

### Port Already in Use

```bash
# Use different port
python run_web.py --port 8000

# Or kill process using port 5000
lsof -ti:5000 | xargs kill -9
```

### Upload Not Working

Check upload folder permissions:

```bash
# Default location: /tmp/acs_uploads
ls -la /tmp/acs_uploads

# If doesn't exist, create it:
mkdir -p /tmp/acs_uploads
chmod 755 /tmp/acs_uploads
```

### Styles Not Loading

Clear browser cache (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)

### Analysis Returns Error

Ensure you have at least 2 artifacts loaded before running analysis.

## Examples

### Complete Workflow Example

1. **Start Server:**
   ```bash
   python run_web.py
   ```

2. **Upload Meshes:**
   - Go to http://localhost:5000/web/upload
   - Drag 10 OBJ files onto the upload zone
   - Click "Upload Selected Files"
   - Wait for processing

3. **Run Analysis:**
   - Go to http://localhost:5000/web/morphometric
   - Click "Run PCA" with default settings
   - Click "Run Clustering" with 3 clusters
   - View visualizations

4. **Define Class:**
   - Go to http://localhost:5000/web/taxonomy
   - Enter class name: "Test Type"
   - Enter reference IDs: "AXE_001, AXE_002, AXE_003"
   - Click "Define Class"

5. **Classify:**
   - Enter artifact ID: "AXE_004"
   - Click "Classify"
   - View confidence scores

6. **Export:**
   - Go to http://localhost:5000/web/
   - Click "Export Data"
   - Choose "taxonomy"
   - Download JSON file

## Advanced Usage

### Programmatic Access

All web actions have corresponding API endpoints:

```python
import requests

# Upload mesh
with open('axe.obj', 'rb') as f:
    files = {'file': f}
    data = {'artifact_id': 'AXE_001'}
    response = requests.post(
        'http://localhost:5000/web/upload-mesh',
        files=files,
        data=data
    )

# Run PCA
response = requests.post(
    'http://localhost:5000/web/run-pca',
    json={'explained_variance': 0.95}
)

# Get statistics
response = requests.get('http://localhost:5000/web/statistics')
stats = response.json()
```

### Batch Processing via Web

For batch uploads, use the command line:

```bash
# Upload all OBJ files in directory
acs-cli batch ./meshes --pattern "*.obj"

# Then view in web interface
# Go to http://localhost:5000/web/artifacts
```

## Security Notes

⚠️ **This is a development server** - Not for production use!

For production deployment:
- Use a production WSGI server (Gunicorn, uWSGI)
- Set up proper authentication
- Use HTTPS
- Configure file upload limits
- Set up proper file validation

## Future Enhancements

Planned features:
- [ ] 3D mesh viewer (Three.js integration)
- [ ] Batch classification interface
- [ ] Timeline view of modifications
- [ ] User authentication
- [ ] Project management (save/load sessions)
- [ ] Export to PDF reports
- [ ] Comparison view (side-by-side artifacts)
- [ ] Advanced filtering and sorting
- [ ] Data visualization gallery

---

**Web Interface Ready!** 🎉

Access at: **http://localhost:5000/web/**

For questions or issues, check the main [README.md](README.md)
