# Savignano Integration Plan
## Architectural Redesign for Integrated AI-Driven Classification

**Version:** 1.0
**Date:** 9 November 2025
**Status:** Implementation Roadmap

---

## Executive Summary

This document outlines the complete integration of Savignano morphometric analysis into the main Archaeological Classifier System (ACS) workflow. The goal is to transform Savignano from a **separate feature** into an **integrated component** of the AI-driven classification pipeline.

### Key Objectives

1. **Auto-extract** Savignano morphometric features during standard upload workflow
2. **Integrate** features into AI Analysis prompts for intelligent classification
3. **Enable ML learning** to recognize Savignano types and suggest new typologies
4. **Merge** comparison features with existing 3D viewer comparison
5. **Generate** technical drawings (front, profile, section) with measurements
6. **Register everything** in database for ML training

---

## Current Architecture Analysis

### What Exists Today

**Classification System (4 Pathways):**
- ✅ AI Classification (Claude 4.5 Sonnet)
- ✅ ML Classification (scikit-learn Random Forest)
- ✅ Hybrid Classification (AI + ML fusion)
- ✅ Stylistic Analysis (parametric taxonomy)

**Taxonomy System:**
- ✅ Formal parametric taxonomy with 5 Bronze Age axe types:
  - Flanged Axe
  - Palstave
  - Socketed Axe
  - Flat Axe
  - Winged Axe
- ✅ Feature-based decision tree classification
- ✅ Database schema for types, features, and attributes

**3D Capabilities:**
- ✅ Interactive 3D viewer (Three.js)
- ✅ Mesh comparison (side-by-side view)
- ✅ Mesh storage in permanent location

**Savignano Module:**
- ✅ Morphometric feature extraction (20 parameters)
- ✅ Matrix identification (hierarchical clustering)
- ✅ Fusion estimation
- ✅ Separate comparison interface
- ❌ NOT integrated into main upload workflow
- ❌ NOT included in AI/ML classification
- ❌ NOT part of taxonomy system

### The Problem

**Current Workflow (Separate):**
```
User uploads mesh
    ↓
Standard analysis (generic features)
    ↓
AI/ML Classification (no Savignano context)
    ↓
User must SEPARATELY go to Savignano Analysis
    ↓
Upload mesh AGAIN
    ↓
Savignano features extracted
    ↓
Separate comparison view
```

**Desired Workflow (Integrated):**
```
User uploads mesh
    ↓
Auto-detect if Bronze Age axe
    ↓
Extract ALL features (standard + Savignano)
    ↓
AI Analysis with full morphometric context
    ↓
Classify with Savignano type awareness
    ↓
Suggest: "This is Savignano type" or "New subclass needed"
    ↓
Unified comparison + technical drawings
    ↓
Everything registered for ML training
```

---

## Integration Architecture

### Phase 1: Auto-Extraction Pipeline

**Goal:** Automatically extract Savignano features during standard upload

**Implementation:**

1. **Modify `/api/upload` endpoint** (`acs/api/blueprints/artifacts.py`)
   - After mesh upload, check if artifact category = "axe"
   - If yes, automatically trigger Savignano extraction
   - Run in background task (async) to avoid blocking

2. **Create feature detector** (`acs/savignano/feature_detector.py`)
   ```python
   def should_extract_savignano(artifact_data: dict) -> bool:
       """Determine if Savignano analysis should run"""
       category = artifact_data.get('category', '').lower()
       description = artifact_data.get('description', '').lower()

       # Check for Bronze Age axe indicators
       is_axe = 'axe' in category or 'ascia' in category
       has_bronze = 'bronze' in description or 'bronzo' in description

       return is_axe and has_bronze
   ```

3. **Background task queue** (use existing or add simple queue)
   - Prevent UI blocking during long mesh processing
   - Show progress indicator in UI
   - Store results in same database entry

**Files to Modify:**
- `acs/api/blueprints/artifacts.py` (upload endpoint)
- `acs/savignano/morphometric_extractor.py` (make callable from main workflow)
- `acs/core/database.py` (ensure single artifact entry, not duplicate)

**Database Changes:**
- NO new tables needed
- Use existing `features` JSON field in `artifacts` table
- Structure: `{"standard": {...}, "savignano": {...}}`

---

### Phase 2: AI Analysis Integration

**Goal:** Feed Savignano features into Claude prompts for intelligent classification

**Implementation:**

1. **Enhance AI analysis prompt** (`acs/api/blueprints/ai_classifier.py`)

   **Current prompt structure:**
   ```python
   prompt = f"""
   Analyze this Bronze Age artifact:
   - Category: {category}
   - Material: {material}
   - Description: {description}
   - Dimensions: {dimensions}

   Provide classification...
   """
   ```

   **New prompt structure:**
   ```python
   prompt = f"""
   Analyze this Bronze Age artifact:
   - Category: {category}
   - Material: {material}
   - Description: {description}
   - Dimensions: {dimensions}

   === MORPHOMETRIC ANALYSIS ===
   {format_savignano_features(features)}

   === CLASSIFICATION TASK ===
   1. Determine primary type (Flanged, Palstave, Socketed, Flat, Winged)
   2. Check if this matches Savignano morphometric profile:
      - Socket (incavo) present
      - Raised flanges (margini rialzati)
      - Lunate blade (tagliente lunato)
      - Typical dimensions (tallone, corpo, tagliente measurements)
   3. If Savignano type detected:
      - Identify specific subclass (if known matrices exist)
      - OR suggest new subclass if morphometry differs significantly
   4. Provide confidence scores and reasoning

   Provide classification in JSON format...
   """
   ```

2. **Create prompt formatter** (`acs/savignano/prompt_formatter.py`)
   ```python
   def format_savignano_features(features: dict) -> str:
       """Format Savignano features for AI prompt"""
       sav = features.get('savignano', {})

       if not sav:
           return "No detailed morphometric analysis available."

       return f"""
   Socket (Incavo): {"Present" if sav['incavo_presente'] else "Absent"}
   - Width: {sav['incavo_larghezza']:.1f}mm
   - Depth: {sav['incavo_profondita']:.1f}mm

   Raised Flanges (Margini Rialzati): {"Present" if sav['margini_rialzati_presenti'] else "Absent"}
   - Length: {sav['margini_rialzati_lunghezza']:.1f}mm
   - Max thickness: {sav['margini_rialzati_spessore_max']:.1f}mm

   Blade (Tagliente): {sav['tagliente_forma']}
   - Width: {sav['tagliente_larghezza']:.1f}mm
   - Expansion: {"Yes" if sav['tagliente_espanso'] else "No"}

   Butt (Tallone):
   - Width: {sav['tallone_larghezza']:.1f}mm
   - Thickness: {sav['tallone_spessore']:.1f}mm

   Weight: {sav['peso']:.1f}g
   Matrix: {sav.get('matrix_id', 'Unknown')}
       """
   ```

3. **Update classification response** to include Savignano type
   ```python
   {
       "primary_type": "Socketed Axe",
       "subtype": "Savignano Type",
       "matrix_id": "MAT_A",
       "confidence": 0.95,
       "savignano_match": true,
       "suggestions": [
           "This axe matches Savignano morphometric profile",
           "Matrix A characteristics (similar to axe974, axe942)",
           "Consider creating subclass: Savignano_Matrix_A"
       ]
   }
   ```

**Files to Modify:**
- `acs/api/blueprints/ai_classifier.py` (main AI classification)
- `acs/savignano/prompt_formatter.py` (NEW - feature formatting)
- `acs/core/database.py` (store AI suggestions)

---

### Phase 3: Taxonomy Integration

**Goal:** Add Savignano as formal type/subtype in parametric taxonomy

**Implementation:**

1. **Extend taxonomy database** (`acs_artifacts.db`)

   **New taxonomy entries:**
   ```sql
   -- Add Savignano as subtype of Socketed Axe
   INSERT INTO types (name, category, parent_type_id) VALUES
   ('Savignano Type', 'axe', (SELECT id FROM types WHERE name = 'Socketed Axe'));

   -- Add Savignano-specific features
   INSERT INTO features (type_id, feature_name, description) VALUES
   ((SELECT id FROM types WHERE name = 'Savignano Type'), 'incavo_presente', 'Socket present on butt end'),
   ((SELECT id FROM types WHERE name = 'Savignano Type'), 'margini_rialzati_presenti', 'Raised flanges along body'),
   ((SELECT id FROM types WHERE name = 'Savignano Type'), 'tagliente_lunato', 'Lunate (crescent) blade shape');

   -- Add matrix subclasses
   INSERT INTO types (name, category, parent_type_id) VALUES
   ('Savignano Matrix A', 'axe', (SELECT id FROM types WHERE name = 'Savignano Type')),
   ('Savignano Matrix B', 'axe', (SELECT id FROM types WHERE name = 'Savignano Type')),
   ('Savignano Matrix C', 'axe', (SELECT id FROM types WHERE name = 'Savignano Type'));
   ```

2. **Create classification rules** (`acs/classifiers/taxonomy_classifier.py`)
   ```python
   def classify_savignano(features: dict) -> dict:
       """Classify Savignano type based on morphometric features"""
       sav = features.get('savignano', {})

       if not sav:
           return None

       # Check Savignano criteria
       has_socket = sav.get('incavo_presente', False)
       has_raised_flanges = sav.get('margini_rialzati_presenti', False)
       is_lunate_blade = sav.get('tagliente_forma') == 'lunato'

       # All three must be present for Savignano type
       if has_socket and has_raised_flanges and is_lunate_blade:
           matrix_id = sav.get('matrix_id', 'Unknown')

           return {
               'type': 'Savignano Type',
               'subtype': f'Savignano {matrix_id}',
               'confidence': 0.95,
               'features_matched': ['socket', 'raised_flanges', 'lunate_blade']
           }

       return None
   ```

3. **Update hybrid classifier** to use taxonomy rules
   - Currently: AI + ML fusion
   - New: AI + ML + Taxonomy (Savignano rules)

**Files to Modify:**
- `acs/classifiers/taxonomy_classifier.py` (add Savignano rules)
- `acs/api/blueprints/hybrid_classifier.py` (integrate taxonomy)
- Database migration script (add new types)

---

### Phase 4: Unified Comparison Interface

**Goal:** Merge Savignano comparison with existing 3D viewer comparison

**Implementation:**

1. **Enhance 3D viewer comparison** (`acs/web/templates/artifact_detail.html`)

   **Current view:**
   - Side-by-side 3D meshes
   - Basic dimension comparison

   **New view:**
   - Side-by-side 3D meshes
   - **Highlighted features** (socket, flanges, blade in different colors)
   - Morphometric overlay (measurements shown on 3D model)
   - Similarity score (if both are Savignano type)
   - Matrix relationship (same matrix or different)

2. **Create 3D highlight system** (`acs/web/static/js/mesh_highlighter.js`)
   ```javascript
   class SavignanoHighlighter {
       constructor(mesh, features) {
           this.mesh = mesh;
           this.features = features;
       }

       highlightSocket() {
           // Highlight incavo region in red
           const socketVertices = this.getSocketVertices();
           this.applyColor(socketVertices, 0xff0000);
       }

       highlightFlanges() {
           // Highlight margini rialzati in blue
           const flangeVertices = this.getFlangeVertices();
           this.applyColor(flangeVertices, 0x0000ff);
       }

       highlightBlade() {
           // Highlight tagliente in green
           const bladeVertices = this.getBladeVertices();
           this.applyColor(bladeVertices, 0x00ff00);
       }

       showMeasurements() {
           // Add measurement annotations
           this.addLabel('Tallone Width', this.features.tallone_larghezza);
           this.addLabel('Incavo Depth', this.features.incavo_profondita);
           this.addLabel('Tagliente Width', this.features.tagliente_larghezza);
       }
   }
   ```

3. **Update comparison API** (`acs/api/blueprints/comparison.py`)
   ```python
   @bp.route('/compare/<id1>/<id2>')
   def compare_artifacts(id1, id2):
       # Get both artifacts with features
       artifact1 = db.get_artifact(id1)
       artifact2 = db.get_artifact(id2)

       # Standard comparison
       comparison = {
           'artifacts': [artifact1, artifact2],
           'dimensions': compare_dimensions(artifact1, artifact2)
       }

       # If both are Savignano type, add morphometric comparison
       if has_savignano_features(artifact1) and has_savignano_features(artifact2):
           comparison['savignano_similarity'] = calculate_savignano_similarity(
               artifact1['features']['savignano'],
               artifact2['features']['savignano']
           )
           comparison['matrix_relationship'] = compare_matrices(
               artifact1['features']['savignano']['matrix_id'],
               artifact2['features']['savignano']['matrix_id']
           )
           comparison['highlights'] = {
               'socket': True,
               'flanges': True,
               'blade': True
           }

       return jsonify(comparison)
   ```

4. **Remove separate Savignano comparison page** (`/web/savignano-compare`)
   - All comparison now happens in unified view
   - Keep backend API for compatibility

**Files to Modify:**
- `acs/web/templates/artifact_detail.html` (add highlight controls)
- `acs/web/static/js/mesh_viewer.js` (add highlight rendering)
- `acs/web/static/js/mesh_highlighter.js` (NEW - highlight logic)
- `acs/api/blueprints/comparison.py` (unified comparison API)

**Files to Remove:**
- `acs/web/templates/savignano_compare.html` (merge into artifact_detail)
- Separate Savignano comparison routes

---

### Phase 5: Technical Drawing Generation

**Goal:** Generate professional archaeological technical drawings (front, profile, section)

**Implementation:**

1. **Create drawing generator** (`acs/savignano/technical_drawings.py`)
   ```python
   import numpy as np
   import matplotlib.pyplot as plt
   from matplotlib.patches import Polygon
   from trimesh import Trimesh

   class TechnicalDrawingGenerator:
       """Generate archaeological technical drawings with measurements"""

       def __init__(self, mesh: Trimesh, features: dict):
           self.mesh = mesh
           self.features = features

       def generate_all_views(self) -> dict:
           """Generate front, profile, and section views"""
           return {
               'front_view': self.generate_front_view(),
               'longitudinal_profile': self.generate_profile_view(),
               'cross_section': self.generate_section_view()
           }

       def generate_front_view(self) -> plt.Figure:
           """Front view with width measurements"""
           fig, ax = plt.subplots(figsize=(8, 12))

           # Project mesh vertices onto XY plane (front view)
           vertices_2d = self.mesh.vertices[:, [0, 2]]  # X, Z coords
           outline = self._extract_outline(vertices_2d)

           # Draw outline
           poly = Polygon(outline, fill=False, edgecolor='black', linewidth=1.5)
           ax.add_patch(poly)

           # Add measurements
           self._add_measurement_line(
               ax,
               start=outline[self._find_tallone_top()],
               end=outline[self._find_tallone_bottom()],
               label=f"{self.features['tallone_larghezza']:.1f}mm",
               side='right'
           )

           self._add_measurement_line(
               ax,
               start=outline[self._find_tagliente_left()],
               end=outline[self._find_tagliente_right()],
               label=f"{self.features['tagliente_larghezza']:.1f}mm",
               side='bottom'
           )

           # Add scale bar
           self._add_scale_bar(ax)

           # Styling
           ax.set_aspect('equal')
           ax.set_title('Front View (Vista Frontale)', fontsize=14, fontweight='bold')
           ax.axis('off')

           return fig

       def generate_profile_view(self) -> plt.Figure:
           """Longitudinal profile with thickness measurements"""
           fig, ax = plt.subplots(figsize=(12, 6))

           # Project onto YZ plane (side view)
           vertices_2d = self.mesh.vertices[:, [1, 2]]  # Y, Z coords
           outline = self._extract_outline(vertices_2d)

           # Draw outline
           poly = Polygon(outline, fill=False, edgecolor='black', linewidth=1.5)
           ax.add_patch(poly)

           # Add measurements along profile
           self._add_measurement_line(
               ax,
               start=outline[self._find_tallone_back()],
               end=outline[self._find_tallone_front()],
               label=f"{self.features['tallone_spessore']:.1f}mm",
               side='top'
           )

           # Highlight socket if present
           if self.features.get('incavo_presente'):
               socket_region = self._extract_socket_profile()
               socket_poly = Polygon(socket_region, fill=True,
                                    facecolor='red', alpha=0.3,
                                    edgecolor='red', linewidth=1)
               ax.add_patch(socket_poly)

               # Add socket depth measurement
               self._add_measurement_line(
                   ax,
                   start=socket_region[0],
                   end=socket_region[-1],
                   label=f"Incavo: {self.features['incavo_profondita']:.1f}mm",
                   side='top'
               )

           # Add scale bar
           self._add_scale_bar(ax)

           ax.set_aspect('equal')
           ax.set_title('Longitudinal Profile (Profilo Longitudinale)',
                       fontsize=14, fontweight='bold')
           ax.axis('off')

           return fig

       def generate_section_view(self) -> plt.Figure:
           """Cross-section views at key points"""
           fig, axes = plt.subplots(1, 3, figsize=(15, 5))

           # Three sections: tallone, corpo, tagliente
           sections = [
               ('Tallone', self._get_section_at_tallone()),
               ('Corpo', self._get_section_at_corpo()),
               ('Tagliente', self._get_section_at_tagliente())
           ]

           for ax, (label, section_verts) in zip(axes, sections):
               # Draw section outline
               poly = Polygon(section_verts, fill=True,
                            facecolor='lightgray', edgecolor='black', linewidth=1.5)
               ax.add_patch(poly)

               # Add width measurement
               width = np.ptp(section_verts[:, 0])
               self._add_measurement_line(
                   ax,
                   start=section_verts[np.argmin(section_verts[:, 0])],
                   end=section_verts[np.argmax(section_verts[:, 0])],
                   label=f"{width:.1f}mm",
                   side='bottom'
               )

               ax.set_aspect('equal')
               ax.set_title(f'Section: {label}', fontsize=12, fontweight='bold')
               ax.axis('off')

           fig.suptitle('Cross Sections (Sezioni Trasversali)',
                       fontsize=14, fontweight='bold')

           return fig

       def _extract_outline(self, vertices_2d: np.ndarray) -> np.ndarray:
           """Extract 2D outline from projected vertices"""
           from scipy.spatial import ConvexHull
           hull = ConvexHull(vertices_2d)
           return vertices_2d[hull.vertices]

       def _add_measurement_line(self, ax, start, end, label, side='right'):
           """Add measurement line with label"""
           # Draw measurement line
           ax.plot([start[0], end[0]], [start[1], end[1]],
                  'k--', linewidth=0.8, alpha=0.5)

           # Draw ticks at ends
           tick_size = 2
           ax.plot([start[0], start[0]], [start[1]-tick_size, start[1]+tick_size],
                  'k-', linewidth=1)
           ax.plot([end[0], end[0]], [end[1]-tick_size, end[1]+tick_size],
                  'k-', linewidth=1)

           # Add label
           mid_x = (start[0] + end[0]) / 2
           mid_y = (start[1] + end[1]) / 2

           offset = 5 if side == 'right' else -5
           ax.text(mid_x + offset, mid_y, label,
                  fontsize=9, ha='left' if side == 'right' else 'right',
                  bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray'))

       def _add_scale_bar(self, ax, length_mm=50):
           """Add scale bar"""
           # Place at bottom left
           xlim = ax.get_xlim()
           ylim = ax.get_ylim()

           x_start = xlim[0] + (xlim[1] - xlim[0]) * 0.1
           y_pos = ylim[0] + (ylim[1] - ylim[0]) * 0.05

           ax.plot([x_start, x_start + length_mm], [y_pos, y_pos],
                  'k-', linewidth=2)
           ax.text(x_start + length_mm/2, y_pos - 3, f'{length_mm}mm',
                  fontsize=9, ha='center')

       def save_all_drawings(self, output_dir: str, artifact_id: str):
           """Save all drawings as PNG files"""
           from pathlib import Path
           output_path = Path(output_dir)
           output_path.mkdir(parents=True, exist_ok=True)

           drawings = self.generate_all_views()

           for view_name, fig in drawings.items():
               filename = f"{artifact_id}_{view_name}.png"
               fig.savefig(output_path / filename, dpi=300, bbox_inches='tight')
               plt.close(fig)

           return {
               'front': str(output_path / f"{artifact_id}_front_view.png"),
               'profile': str(output_path / f"{artifact_id}_longitudinal_profile.png"),
               'section': str(output_path / f"{artifact_id}_cross_section.png")
           }
   ```

2. **Add API endpoint** (`acs/api/blueprints/savignano.py`)
   ```python
   @bp.route('/generate-drawings/<artifact_id>', methods=['POST'])
   def generate_technical_drawings(artifact_id: str):
       """Generate technical drawings for artifact"""
       # Get artifact and mesh
       artifact = db.get_artifact(artifact_id)
       mesh_path = artifact.get('mesh_path')

       if not mesh_path or not Path(mesh_path).exists():
           return jsonify({'error': 'Mesh file not found'}), 404

       # Load mesh
       mesh = trimesh.load(mesh_path)

       # Get Savignano features
       features = artifact.get('features', {}).get('savignano', {})

       if not features:
           return jsonify({'error': 'Savignano features not available'}), 400

       # Generate drawings
       generator = TechnicalDrawingGenerator(mesh, features)
       output_dir = Path.home() / ".acs" / "drawings" / artifact_id

       drawing_paths = generator.save_all_drawings(str(output_dir), artifact_id)

       # Save paths to database
       db.update_artifact(artifact_id, {'technical_drawings': drawing_paths})

       return jsonify({
           'success': True,
           'drawings': drawing_paths
       })
   ```

3. **Add UI button** in artifact detail page
   ```html
   <!-- acs/web/templates/artifact_detail.html -->
   <div class="technical-drawings-section">
       <h3>Technical Drawings</h3>

       {% if artifact.technical_drawings %}
           <div class="drawings-grid">
               <img src="{{ url_for('static', filename=artifact.technical_drawings.front) }}"
                    alt="Front View">
               <img src="{{ url_for('static', filename=artifact.technical_drawings.profile) }}"
                    alt="Profile View">
               <img src="{{ url_for('static', filename=artifact.technical_drawings.section) }}"
                    alt="Section View">
           </div>
       {% else %}
           <button onclick="generateDrawings('{{ artifact.id }}')" class="btn btn-primary">
               Generate Technical Drawings
           </button>
       {% endif %}
   </div>
   ```

**Files to Create:**
- `acs/savignano/technical_drawings.py` (NEW - drawing generation)
- Tests for drawing generation

**Files to Modify:**
- `acs/api/blueprints/savignano.py` (add drawing endpoint)
- `acs/web/templates/artifact_detail.html` (add drawing display)
- `acs/web/static/js/artifact_detail.js` (add drawing generation trigger)

---

### Phase 6: ML Training Integration

**Goal:** Register all data for ML training to recognize Savignano types

**Implementation:**

1. **Create training dataset** (`acs/ml/savignano_dataset.py`)
   ```python
   class SavignanoDataset:
       """Dataset for training Savignano classification model"""

       def __init__(self, db):
           self.db = db

       def export_training_data(self) -> pd.DataFrame:
           """Export all Savignano features as training dataset"""
           artifacts = self.db.get_all_artifacts()

           training_data = []
           for artifact in artifacts:
               features = artifact.get('features', {})
               sav = features.get('savignano', {})

               if sav:
                   training_data.append({
                       'artifact_id': artifact['artifact_id'],
                       # Feature vector (20 morphometric parameters)
                       'tallone_larghezza': sav.get('tallone_larghezza', 0),
                       'tallone_spessore': sav.get('tallone_spessore', 0),
                       'incavo_presente': int(sav.get('incavo_presente', False)),
                       'incavo_larghezza': sav.get('incavo_larghezza', 0),
                       'incavo_profondita': sav.get('incavo_profondita', 0),
                       # ... all 20 parameters

                       # Labels
                       'is_savignano': self._is_savignano(sav),
                       'matrix_id': sav.get('matrix_id', 'Unknown'),
                       'classification': artifact.get('classification', 'Unknown')
                   })

           return pd.DataFrame(training_data)

       def _is_savignano(self, features: dict) -> bool:
           """Determine if artifact is Savignano type"""
           return (
               features.get('incavo_presente', False) and
               features.get('margini_rialzati_presenti', False) and
               features.get('tagliente_forma') == 'lunato'
           )
   ```

2. **Train binary classifier** (Savignano vs Non-Savignano)
   ```python
   from sklearn.ensemble import RandomForestClassifier
   from sklearn.model_selection import train_test_split

   def train_savignano_classifier():
       """Train model to recognize Savignano axes"""
       # Load dataset
       dataset = SavignanoDataset(get_database())
       df = dataset.export_training_data()

       # Feature matrix
       X = df[[col for col in df.columns if col not in ['artifact_id', 'is_savignano', 'matrix_id', 'classification']]]
       y = df['is_savignano']

       # Train-test split
       X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

       # Train classifier
       clf = RandomForestClassifier(n_estimators=100, random_state=42)
       clf.fit(X_train, y_train)

       # Evaluate
       accuracy = clf.score(X_test, y_test)
       print(f"Savignano classifier accuracy: {accuracy:.2%}")

       # Save model
       import joblib
       joblib.dump(clf, 'models/savignano_classifier.pkl')

       return clf
   ```

3. **Integrate into ML classification pipeline**
   ```python
   # acs/classifiers/ml_classifier.py

   def classify_with_ml(artifact_data: dict) -> dict:
       """ML classification with Savignano detection"""
       features = artifact_data.get('features', {})

       # Standard ML classification
       primary_class = standard_ml_classifier.predict(features)

       # Check for Savignano type
       if 'savignano' in features:
           savignano_clf = joblib.load('models/savignano_classifier.pkl')
           is_savignano = savignano_clf.predict([extract_feature_vector(features['savignano'])])[0]

           if is_savignano:
               # Get matrix prediction
               matrix_clf = joblib.load('models/savignano_matrix_classifier.pkl')
               matrix_id = matrix_clf.predict([extract_feature_vector(features['savignano'])])[0]

               return {
                   'primary_type': 'Socketed Axe',
                   'subtype': 'Savignano Type',
                   'matrix_id': matrix_id,
                   'confidence': savignano_clf.predict_proba([...])[0].max(),
                   'method': 'ML'
               }

       return primary_class
   ```

**Files to Create:**
- `acs/ml/savignano_dataset.py` (NEW - dataset export)
- `acs/ml/train_savignano.py` (NEW - training script)
- `models/savignano_classifier.pkl` (trained model)

**Files to Modify:**
- `acs/classifiers/ml_classifier.py` (integrate Savignano detection)

---

### Phase 7: WebGUI Updates

**Goal:** Update dashboard and navigation to reflect integrated workflow

**Implementation:**

1. **Remove separate Savignano menu items** (`acs/web/templates/base.html`)
   - Remove "Savignano Analysis" from nav
   - Remove "Savignano Comparison" from nav
   - Keep everything in unified "AI Analysis" and "Artifacts" sections

2. **Update dashboard cards** (`acs/web/templates/index.html`)

   **Before:**
   ```html
   <div class="card">
       <h3>🗡️ Savignano Axes Analysis</h3>
       <p>Specialized morphometric analysis</p>
       <a href="/web/savignano-analysis">Analyze →</a>
   </div>
   ```

   **After:**
   ```html
   <div class="card">
       <h3>🤖 AI Analysis</h3>
       <p>Intelligent classification with morphometric analysis</p>
       <ul>
           <li>Auto-detect artifact types</li>
           <li>Extract morphometric features (including Savignano)</li>
           <li>Suggest typologies and subclasses</li>
       </ul>
       <a href="/web/upload">Upload Artifact →</a>
   </div>
   ```

3. **Add feature indicators** in artifact list
   ```html
   <!-- acs/web/templates/artifacts.html -->
   <div class="artifact-card">
       <h4>{{ artifact.artifact_id }}</h4>
       <span class="badge">{{ artifact.classification }}</span>

       {% if artifact.features.savignano %}
           <span class="badge badge-savignano">
               🗡️ Savignano Type
               {% if artifact.features.savignano.matrix_id %}
                   ({{ artifact.features.savignano.matrix_id }})
               {% endif %}
           </span>
       {% endif %}
   </div>
   ```

4. **Update upload page** to show auto-analysis
   ```html
   <!-- acs/web/templates/upload.html -->
   <div class="info-box">
       <h4>Automatic Analysis</h4>
       <p>When you upload a Bronze Age axe, the system will automatically:</p>
       <ul>
           <li>✓ Extract standard features (dimensions, material, etc.)</li>
           <li>✓ Perform morphometric analysis (if applicable)</li>
           <li>✓ Check for Savignano type characteristics</li>
           <li>✓ Generate AI classification with confidence scores</li>
           <li>✓ Suggest typology and subclasses</li>
       </ul>
   </div>
   ```

**Files to Modify:**
- `acs/web/templates/base.html` (remove separate Savignano menu)
- `acs/web/templates/index.html` (update dashboard cards)
- `acs/web/templates/artifacts.html` (add Savignano badges)
- `acs/web/templates/upload.html` (explain auto-analysis)

**Files to Remove:**
- `acs/web/templates/savignano_analysis.html` (merged into upload)
- `acs/web/templates/savignano_compare.html` (merged into artifact comparison)

---

## Implementation Timeline

### Week 1: Auto-Extraction + AI Integration
- **Days 1-2:** Phase 1 - Auto-extraction pipeline
- **Days 3-4:** Phase 2 - AI prompt integration
- **Day 5:** Testing and debugging

**Deliverables:**
- ✅ Savignano features auto-extracted on upload
- ✅ AI Analysis includes morphometric context
- ✅ Classification results mention Savignano type

### Week 2: Taxonomy + Comparison
- **Days 1-2:** Phase 3 - Taxonomy integration
- **Days 3-5:** Phase 4 - Unified comparison interface

**Deliverables:**
- ✅ Savignano type in formal taxonomy
- ✅ Unified 3D comparison with highlights
- ✅ Matrix relationship display

### Week 3: Technical Drawings + ML
- **Days 1-3:** Phase 5 - Technical drawing generation
- **Days 4-5:** Phase 6 - ML training integration

**Deliverables:**
- ✅ Technical drawings (front, profile, section)
- ✅ ML classifier for Savignano detection
- ✅ Training dataset exported

### Week 4: WebGUI + Testing
- **Days 1-2:** Phase 7 - WebGUI updates
- **Days 3-5:** End-to-end testing and refinement

**Deliverables:**
- ✅ Updated navigation and dashboard
- ✅ Integrated workflow functional
- ✅ Documentation updated

---

## Success Metrics

### Technical Metrics
1. **Auto-extraction success rate:** >95% for Bronze Age axes
2. **AI classification accuracy:** >85% for Savignano type detection
3. **ML model accuracy:** >90% for Savignano vs Non-Savignano
4. **Drawing generation time:** <30 seconds per artifact
5. **3D highlight rendering:** <2 seconds load time

### User Experience Metrics
1. **Single upload workflow:** User uploads once, gets complete analysis
2. **No duplicate features:** Savignano not separate from main workflow
3. **Unified comparison:** All comparison in one interface
4. **Clear classification:** System clearly indicates Savignano type
5. **Actionable suggestions:** AI suggests subclasses when appropriate

---

## Database Schema Changes

### Minimal Changes Required

**Existing tables remain unchanged:**
- `artifacts` (already has `features` JSON field)
- `types` (add Savignano entries)
- `features` (add Savignano features)

**New fields in `artifacts` table:**
```sql
ALTER TABLE artifacts ADD COLUMN technical_drawings TEXT;
-- Stores JSON: {"front": "path/to/front.png", "profile": "...", "section": "..."}
```

**New taxonomy entries:**
```sql
-- Taxonomy types
INSERT INTO types (name, category, parent_type_id) VALUES
('Savignano Type', 'axe', (SELECT id FROM types WHERE name = 'Socketed Axe')),
('Savignano Matrix A', 'axe', (SELECT id FROM types WHERE name = 'Savignano Type')),
('Savignano Matrix B', 'axe', (SELECT id FROM types WHERE name = 'Savignano Type'));

-- Savignano-specific features
INSERT INTO features (type_id, feature_name, description) VALUES
((SELECT id FROM types WHERE name = 'Savignano Type'), 'incavo_presente', 'Socket present'),
((SELECT id FROM types WHERE name = 'Savignano Type'), 'margini_rialzati_presenti', 'Raised flanges'),
((SELECT id FROM types WHERE name = 'Savignano Type'), 'tagliente_lunato', 'Lunate blade');
```

---

## Risk Mitigation

### Risk 1: Performance Degradation
**Risk:** Auto-extraction may slow down uploads

**Mitigation:**
- Run Savignano extraction as background task
- Show progress indicator in UI
- Only trigger for Bronze Age axes
- Cache results in database

### Risk 2: False Positives
**Risk:** System incorrectly classifies non-Savignano as Savignano

**Mitigation:**
- Use strict criteria (all 3 features required)
- Show confidence scores
- Allow manual override
- Continuous ML model improvement

### Risk 3: Backward Compatibility
**Risk:** Existing artifacts may not have Savignano features

**Mitigation:**
- Batch processing script to analyze existing axes
- Clear indication when features missing
- "Re-analyze" button for existing artifacts

### Risk 4: Technical Drawing Accuracy
**Risk:** Generated drawings may not match archaeological standards

**Mitigation:**
- Validate with archaeological experts
- Allow manual adjustment of measurements
- Provide both auto-generated and manual drawing options

---

## Testing Strategy

### Unit Tests
- Savignano feature extraction
- Classification rules (taxonomy)
- ML model predictions
- Drawing generation

### Integration Tests
- End-to-end upload workflow
- AI Analysis with Savignano context
- Unified comparison interface
- Database persistence

### User Acceptance Tests
1. Upload Bronze Age axe → Verify auto-extraction
2. View artifact detail → Verify Savignano badge
3. Run AI Analysis → Verify Savignano mentioned in results
4. Compare two Savignano axes → Verify highlights and similarity
5. Generate technical drawings → Verify accuracy

---

## Future Enhancements

### Phase 8: Advanced Features (Post-MVP)

1. **3D Morphometric Heatmaps**
   - Color-code entire mesh by thickness, curvature
   - Interactive exploration of morphometric parameters

2. **Automated Matrix Discovery**
   - Unsupervised learning to discover new matrices
   - Suggest when new subclass should be created

3. **Comparative Statistics**
   - Population analysis across all Savignano axes
   - Statistical distributions of parameters
   - Outlier detection

4. **Export to Archaeological Standards**
   - Export drawings in SVG format (editable)
   - Generate reports in ADS/OASIS format
   - Integration with museum collection management systems

---

## Appendix A: File Structure

### New Files to Create
```
acs/
├── savignano/
│   ├── feature_detector.py         # Auto-detection logic
│   ├── prompt_formatter.py         # AI prompt formatting
│   ├── technical_drawings.py       # Drawing generation
│   └── taxonomy_rules.py           # Classification rules
├── ml/
│   ├── savignano_dataset.py        # Training dataset export
│   └── train_savignano.py          # ML training script
└── web/
    └── static/
        └── js/
            └── mesh_highlighter.js  # 3D highlight rendering
```

### Files to Modify
```
acs/
├── api/
│   └── blueprints/
│       ├── artifacts.py            # Add auto-extraction
│       ├── ai_classifier.py        # Enhance prompts
│       ├── savignano.py            # Add drawing endpoint
│       └── comparison.py           # Unified comparison
├── classifiers/
│   ├── taxonomy_classifier.py      # Add Savignano rules
│   ├── ml_classifier.py            # Integrate Savignano detection
│   └── hybrid_classifier.py        # Use taxonomy + ML
└── web/
    ├── templates/
    │   ├── base.html               # Remove separate menu
    │   ├── index.html              # Update dashboard
    │   ├── artifacts.html          # Add badges
    │   ├── upload.html             # Explain auto-analysis
    │   └── artifact_detail.html    # Add highlights + drawings
    └── static/
        └── js/
            └── mesh_viewer.js      # Add highlight support
```

### Files to Remove
```
acs/web/templates/
├── savignano_analysis.html         # Merged into upload
└── savignano_compare.html          # Merged into artifact_detail
```

---

## Appendix B: API Changes

### New Endpoints

**POST `/api/artifacts/{id}/generate-drawings`**
- Generate technical drawings
- Returns: `{"front": "...", "profile": "...", "section": "..."}`

**GET `/api/artifacts/{id}/savignano-features`**
- Get Savignano features for artifact
- Returns: `{"incavo_presente": true, ...}`

**POST `/api/ml/train-savignano`**
- Trigger ML training on current dataset
- Returns: `{"accuracy": 0.92, "model_path": "..."}`

### Modified Endpoints

**POST `/api/upload`**
- Now auto-extracts Savignano features for Bronze Age axes
- Returns includes: `"savignano_features_extracted": true`

**POST `/api/ai-classify`**
- Prompt now includes Savignano context
- Returns may include: `"subtype": "Savignano Type"`

**GET `/api/compare/{id1}/{id2}`**
- Now includes Savignano similarity if both are Savignano type
- Returns includes: `"savignano_similarity": 0.87`

---

## Appendix C: Configuration

### Environment Variables

```bash
# .env

# Savignano Settings
SAVIGNANO_AUTO_EXTRACT=true                    # Enable auto-extraction
SAVIGNANO_MIN_CONFIDENCE=0.80                  # Minimum confidence for classification
SAVIGNANO_DRAWING_DPI=300                      # Drawing resolution

# ML Settings
ML_MODEL_PATH=models/savignano_classifier.pkl
ML_TRAINING_ENABLED=true

# Performance
BACKGROUND_TASK_TIMEOUT=300                    # 5 minutes for mesh processing
```

---

## Conclusion

This integration plan transforms Savignano morphometric analysis from a **separate feature** into a **core component** of the Archaeological Classifier System's AI-driven workflow.

**Key Achievements:**
1. ✅ Single upload workflow with auto-analysis
2. ✅ AI-powered classification with morphometric context
3. ✅ Unified comparison interface with 3D highlights
4. ✅ Professional technical drawings
5. ✅ ML training for continuous improvement
6. ✅ Seamless user experience

**Timeline:** 3-4 weeks for complete implementation

**Next Steps:** Begin Phase 1 (Auto-Extraction Pipeline)
