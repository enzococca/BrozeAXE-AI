"""
Technical Drawing Module for Archaeological Artifacts
======================================================

Generates professional technical drawings for Bronze Age axes following
archaeological standards with:
- Longitudinal profile
- Cross-sections (max/min points)
- Front and back views
- Fine hatching for shadows
- Standard archaeological conventions
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Force non-GUI backend BEFORE importing pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from typing import Dict, List, Tuple, Optional
import io
from PIL import Image


class TechnicalDrawingGenerator:
    """Generate professional technical drawings for archaeological artifacts."""

    def __init__(self, dpi: int = 300):
        """
        Initialize drawing generator.

        Args:
            dpi: Resolution for output images
        """
        self.dpi = dpi
        # Italian archaeological standard style
        self.line_width = 0.3  # Very thin lines
        self.hatching_spacing = 0.5  # Dense parallel hatching (mm)
        self.hatching_line_width = 0.15  # Very thin hatching lines
        self.scale_bar_length = 30  # 3 cm scale bar

    def generate_complete_drawing(self, mesh, artifact_id: str,
                                  features: Dict = None) -> Dict[str, bytes]:
        """
        Generate complete technical drawing sheet with all standard views.

        Args:
            mesh: Trimesh object
            artifact_id: Artifact identifier
            features: Optional morphometric features

        Returns:
            Dictionary with image buffers for each view
        """
        # Reorient mesh to standard archaeological position
        oriented_mesh = self._reorient_mesh(mesh)

        views = {}

        # Generate standard archaeological views:
        # 1. Longitudinal profile (SIDE view - most important!)
        views['longitudinal_profile'] = self._draw_longitudinal_profile(oriented_mesh, artifact_id)

        # 2. Three cross-sections at different heights (archaeological standard)
        views['cross_section_high'] = self._draw_cross_section(oriented_mesh, 'high')   # 70% - blade
        views['cross_section_mid'] = self._draw_cross_section(oriented_mesh, 'mid')     # 50% - middle
        views['cross_section_low'] = self._draw_cross_section(oriented_mesh, 'low')     # 30% - shaft

        # 3. Front view (optional)
        views['front_view'] = self._draw_front_view(oriented_mesh)

        # Generate complete composite sheet (archaeological layout)
        views['complete_sheet'] = self._create_composite_sheet(
            oriented_mesh, artifact_id, features, views
        )

        return views

    def _reorient_mesh(self, mesh):
        """
        Reorient mesh to standard archaeological position.

        Standard orientation for axes:
        - Blade pointing up (Z+)
        - Maximum width along X axis
        - Thickness along Y axis
        """
        import trimesh

        # Create a copy to avoid modifying original
        oriented = mesh.copy()

        try:
            import numpy as np
            from scipy.spatial.transform import Rotation

            # Get principal axes
            principal_inertia = oriented.principal_inertia_vectors

            # Align longest axis with Z (blade direction)
            # Create rotation from principal axis to [0, 0, 1]
            v1 = principal_inertia[0] / np.linalg.norm(principal_inertia[0])
            v2 = np.array([0, 0, 1])

            # Calculate rotation axis and angle
            rotation_axis = np.cross(v1, v2)
            if np.linalg.norm(rotation_axis) > 1e-6:  # Not already aligned
                rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
                rotation_angle = np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0))

                # Create rotation matrix
                rotation = Rotation.from_rotvec(rotation_angle * rotation_axis)
                transform_matrix = np.eye(4)
                transform_matrix[:3, :3] = rotation.as_matrix()

                oriented.apply_transform(transform_matrix)
        except Exception as e:
            print(f"Warning: Could not reorient mesh ({str(e)}), using original orientation")
            # Return copy as-is if reorientation fails

        return oriented

    def _draw_longitudinal_profile(self, mesh, artifact_id: str) -> bytes:
        """
        Draw longitudinal profile (side view) with STIPPLING for shadows.

        Professional archaeological drawing with dots for depth shading.
        """
        fig, ax = plt.subplots(figsize=(8, 6), dpi=self.dpi)

        try:
            # Project mesh onto YZ plane (side view)
            vertices_3d = mesh.vertices

            # Get silhouette outline from side view
            from scipy.spatial import ConvexHull

            # Project to 2D (Y=0 view, use X and Z)
            vertices_2d = vertices_3d[:, [0, 2]]  # X and Z coordinates

            # Get convex hull for outer contour
            hull = ConvexHull(vertices_2d)
            outline_indices = hull.vertices
            outline = vertices_2d[outline_indices]

            # Close the outline
            outline_closed = np.vstack([outline, outline[0]])

            # Draw THICK outline (archaeological style)
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=0.8, solid_capstyle='round')

            # Add STIPPLING for depth and form
            self._add_stippling_shading(ax, mesh, vertices_2d, outline, view='side')

        except Exception as e:
            print(f"Warning: Could not create longitudinal profile ({str(e)})")
            ax.text(0.5, 0.5, 'Profile unavailable', ha='center', va='center',
                   transform=ax.transAxes)

        # Add scale bar
        self._add_scale_bar(ax)

        # Add title
        ax.set_title(f'{artifact_id} - Profilo Longitudinale',
                    fontsize=10, pad=10)

        # Clean axes
        ax.set_aspect('equal')
        ax.axis('off')

        # Save to buffer
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=self.dpi, bbox_inches='tight')
        plt.close()
        buf.seek(0)

        return buf.getvalue()

    def _draw_cross_section(self, mesh, section_type: str = 'mid') -> bytes:
        """
        Draw cross-section at specific height with STIPPLING.

        Args:
            mesh: Trimesh object
            section_type: 'high' (70%), 'mid' (50%), or 'low' (30%) along Z axis
        """
        fig, ax = plt.subplots(figsize=(3.5, 3.5), dpi=self.dpi)

        # Find section position along Z axis (archaeological standard: 3 sections)
        bounds = mesh.bounds
        z_range = bounds[1][2] - bounds[0][2]

        if section_type == 'high':
            z_pos = bounds[0][2] + z_range * 0.70  # 70% - blade/upper part
            title = "Sez. Alta"
        elif section_type == 'mid':
            z_pos = bounds[0][2] + z_range * 0.50  # 50% - middle
            title = "Sez. Media"
        else:  # 'low'
            z_pos = bounds[0][2] + z_range * 0.30  # 30% - shaft/lower part
            title = "Sez. Bassa"

        try:
            # Get vertices at this Z level for depth mapping
            from scipy.spatial import ConvexHull

            # Get all vertices near this Z position (within a small band)
            z_band = 5.0  # mm
            mask = np.abs(mesh.vertices[:, 2] - z_pos) < z_band
            nearby_vertices = mesh.vertices[mask]

            if len(nearby_vertices) > 3:
                # Project to 2D (X, Y coordinates)
                vertices_2d = nearby_vertices[:, :2]

                # Get convex hull for outline
                hull = ConvexHull(vertices_2d)
                outline = vertices_2d[hull.vertices]

                # Close outline
                outline_closed = np.vstack([outline, outline[0]])

                # Draw THICK outline
                ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                       'k-', linewidth=0.8, solid_capstyle='round')

                # Add STIPPLING for cross-section
                # For sections, use uniform density (it's a cut, not depth shading)
                self._add_section_stippling(ax, vertices_2d, outline)
            else:
                raise ValueError("Not enough vertices at this Z position")

        except Exception as e:
            print(f"Warning: Could not create cross-section ({str(e)})")
            ax.text(0.5, 0.5, 'Section unavailable', ha='center', va='center',
                   transform=ax.transAxes)

        ax.set_title(title, fontsize=10, pad=10)
        ax.set_aspect('equal')
        ax.axis('off')

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=self.dpi, bbox_inches='tight')
        plt.close()
        buf.seek(0)

        return buf.getvalue()

    def _draw_front_view(self, mesh) -> bytes:
        """Draw front view (looking down Z axis) with STIPPLING."""
        fig, ax = plt.subplots(figsize=(4, 8), dpi=self.dpi)

        # Project onto XY plane
        vertices_2d = mesh.vertices[:, :2]  # X, Y coordinates

        # Get convex hull for outline
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(vertices_2d)
            outline = vertices_2d[hull.vertices]

            # Close outline
            outline_closed = np.vstack([outline, outline[0]])

            # Draw THICK outline
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=0.8, solid_capstyle='round')

            # Add STIPPLING for depth
            self._add_stippling_shading(ax, mesh, vertices_2d, outline, view='front')

        except Exception as e:
            # Fallback: use bounding box
            print(f"Warning: Could not compute convex hull ({str(e)}), using bounding box")
            min_x, min_y = vertices_2d.min(axis=0)
            max_x, max_y = vertices_2d.max(axis=0)
            outline = np.array([
                [min_x, min_y],
                [max_x, min_y],
                [max_x, max_y],
                [min_x, max_y],
                [min_x, min_y]
            ])
            ax.plot(outline[:, 0], outline[:, 1],
                   'k-', linewidth=0.8)

        ax.set_title('Vista Frontale', fontsize=10, pad=10)
        ax.set_aspect('equal')
        ax.axis('off')

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=self.dpi, bbox_inches='tight')
        plt.close()
        buf.seek(0)

        return buf.getvalue()

    def _draw_back_view(self, mesh) -> bytes:
        """Draw back view (opposite of front) with STIPPLING."""
        fig, ax = plt.subplots(figsize=(4, 8), dpi=self.dpi)

        vertices_2d = mesh.vertices[:, :2].copy()  # Make a copy
        vertices_2d[:, 0] = -vertices_2d[:, 0]  # Flip X

        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(vertices_2d)
            outline = vertices_2d[hull.vertices]

            # Close outline
            outline_closed = np.vstack([outline, outline[0]])

            # Draw THICK outline
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=0.8, solid_capstyle='round')

            # Add STIPPLING for depth
            self._add_stippling_shading(ax, mesh, vertices_2d, outline, view='back')

        except Exception as e:
            # Fallback: use bounding box
            print(f"Warning: Could not compute convex hull ({str(e)}), using bounding box")
            min_x, min_y = vertices_2d.min(axis=0)
            max_x, max_y = vertices_2d.max(axis=0)
            outline = np.array([
                [min_x, min_y],
                [max_x, min_y],
                [max_x, max_y],
                [min_x, max_y],
                [min_x, min_y]
            ])
            ax.plot(outline[:, 0], outline[:, 1],
                   'k-', linewidth=0.8)

        ax.set_title('Vista Posteriore', fontsize=10, pad=10)
        ax.set_aspect('equal')
        ax.axis('off')

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=self.dpi, bbox_inches='tight')
        plt.close()
        buf.seek(0)

        return buf.getvalue()

    def _add_section_stippling(self, ax, vertices_2d: np.ndarray, outline: np.ndarray):
        """
        Add uniform stippling for cross-sections.

        For sections, stippling is UNIFORM (not depth-based) because
        it represents a cut surface, not depth shading.

        Args:
            ax: Matplotlib axis
            vertices_2d: 2D vertices
            outline: Outline vertices
        """
        from matplotlib.path import Path

        if len(outline) < 3:
            return

        # Create polygon path for masking
        path = Path(outline)

        # Get bounding box
        min_x, min_y = vertices_2d.min(axis=0)
        max_x, max_y = vertices_2d.max(axis=0)

        # Generate UNIFORM stippling grid for sections
        dot_spacing = 1.5  # Slightly denser than depth shading
        width = max_x - min_x
        height = max_y - min_y

        n_x = int(width / dot_spacing) * 2
        n_y = int(height / dot_spacing) * 2

        x_grid = np.linspace(min_x, max_x, n_x)
        y_grid = np.linspace(min_y, max_y, n_y)

        dot_x = []
        dot_y = []

        # UNIFORM probability for sections (25-35% coverage)
        uniform_probability = 0.30

        for x in x_grid:
            for y in y_grid:
                point = np.array([x, y])

                # Check if point is inside outline
                if not path.contains_point(point):
                    continue

                # Uniform random stippling
                if np.random.random() < uniform_probability:
                    dot_x.append(x)
                    dot_y.append(y)

        # Draw uniform dots
        if len(dot_x) > 0:
            ax.scatter(dot_x, dot_y, s=0.6, c='black',
                      marker='.', linewidths=0, alpha=0.85, zorder=1)

    def _add_stippling_shading(self, ax, mesh, vertices_2d: np.ndarray,
                              outline: np.ndarray, view: str = 'side'):
        """
        Add STIPPLING (dots) for professional archaeological shading.

        Stippling technique:
        - More dots in shadowed/deeper areas
        - Fewer dots in highlighted areas
        - Dots sized and spaced based on depth/curvature

        Args:
            ax: Matplotlib axis
            mesh: Original 3D mesh
            vertices_2d: 2D projected vertices
            outline: Outline vertices
            view: 'side', 'front', or 'back'
        """
        from matplotlib.path import Path
        from scipy.spatial import cKDTree

        if len(outline) < 3:
            return

        # Create polygon path for masking
        path = Path(outline)

        # Get bounding box
        min_x, min_y = vertices_2d.min(axis=0)
        max_x, max_y = vertices_2d.max(axis=0)

        # Calculate depth/curvature for each vertex (for shading)
        if view == 'side':
            # Depth is Y coordinate (how far from viewing plane)
            depth_values = mesh.vertices[:, 1]  # Y depth
        elif view == 'front':
            depth_values = mesh.vertices[:, 2]  # Z depth
        else:  # back
            depth_values = -mesh.vertices[:, 2]

        # Normalize depth to 0-1
        if len(depth_values) > 0:
            depth_min, depth_max = depth_values.min(), depth_values.max()
            if depth_max > depth_min:
                depth_normalized = (depth_values - depth_min) / (depth_max - depth_min)
            else:
                depth_normalized = np.zeros_like(depth_values)
        else:
            depth_normalized = np.zeros(len(vertices_2d))

        # Create KDTree for depth lookup
        tree = cKDTree(vertices_2d)

        # Generate stippling grid - RIDOTTO per evitare grigio uniforme
        dot_spacing_base = 2.0  # AUMENTATO da 0.8 a 2.0 mm - meno denso
        width = max_x - min_x
        height = max_y - min_y

        # Create sampling grid (MENO denso)
        n_x = int(width / dot_spacing_base) * 2  # RIDOTTO da *4 a *2
        n_y = int(height / dot_spacing_base) * 2  # RIDOTTO da *4 a *2

        x_grid = np.linspace(min_x, max_x, n_x)
        y_grid = np.linspace(min_y, max_y, n_y)

        # Stippling dots
        dot_x = []
        dot_y = []
        dot_sizes = []

        for x in x_grid:
            for y in y_grid:
                point = np.array([x, y])

                # Check if point is inside outline
                if not path.contains_point(point):
                    continue

                # Find nearest mesh vertex to get depth
                dist, idx = tree.query(point)

                if idx < len(depth_normalized):
                    depth = depth_normalized[idx]

                    # Probability RIDOTTA - solo zone profonde hanno stippling
                    # Archaeological convention: stippling solo per ombre marcate
                    probability = 0.05 + (depth * 0.35)  # RIDOTTO da 15-75% a 5-40%

                    if np.random.random() < probability:
                        dot_x.append(x)
                        dot_y.append(y)
                        # Dot size varies slightly
                        dot_sizes.append(0.5 + depth * 0.4)  # Puntini leggermente più grandi

        # Draw dots (stippling)
        if len(dot_x) > 0:
            ax.scatter(dot_x, dot_y, s=dot_sizes, c='black',
                      marker='.', linewidths=0, alpha=0.9, zorder=1)

    def _add_hatching(self, ax, vertices: np.ndarray, direction: str = 'vertical',
                     density: float = 2.0):
        """
        Add fine hatching for shadows following Italian archaeological conventions.

        Uses very dense, thin parallel lines (typically on one side to show depth).

        Args:
            ax: Matplotlib axis
            vertices: Outline vertices
            direction: 'vertical', 'horizontal', or 'diagonal'
            density: Hatching density multiplier (default 2.0 for dense hatching)
        """
        if len(vertices) < 3:
            return

        # Get bounding box - hatch only RIGHT half (traditional convention)
        min_x, min_y = vertices.min(axis=0)
        max_x, max_y = vertices.max(axis=0)

        # Hatch only right side (traditional Italian style)
        mid_x = (min_x + max_x) / 2
        hatch_start = mid_x + (max_x - min_x) * 0.1  # Start from 60% point
        hatch_end = max_x - (max_x - min_x) * 0.02    # Small margin

        # Create DENSE hatching lines
        spacing = self.hatching_spacing / density

        if direction == 'vertical':
            x_lines = np.arange(hatch_start, hatch_end, spacing)
            for x in x_lines:
                # Draw thin vertical lines
                ax.plot([x, x], [min_y, max_y], 'k-',
                       linewidth=self.hatching_line_width, alpha=0.8, zorder=1)

        elif direction == 'diagonal':
            # 45-degree hatching
            for offset in np.arange(-max_y, max_x, spacing):
                x_start = max(min_x, offset)
                y_start = max(min_y, -offset + min_x)
                x_end = min(max_x, max_y + offset)
                y_end = min(max_y, max_y - offset + max_x)
                ax.plot([x_start, x_end], [y_start, y_end],
                       'k-', linewidth=0.2, alpha=0.5, zorder=1)

    def _add_cross_hatching(self, ax, vertices: np.ndarray):
        """Add cross-hatching for cut sections."""
        self._add_hatching(ax, vertices, direction='diagonal', density=1.5)
        # Add perpendicular hatching
        min_x, min_y = vertices.min(axis=0)
        max_x, max_y = vertices.max(axis=0)
        spacing = self.hatching_spacing / 1.5

        for offset in np.arange(-max_y, max_x, spacing):
            x_start = max(min_x, max_y - offset)
            y_start = max(min_y, offset - min_x)
            x_end = min(max_x, -min_y + offset + max_y)
            y_end = min(max_y, offset + max_x + min_y)
            ax.plot([x_start, x_end], [y_start, y_end],
                   'k-', linewidth=0.2, alpha=0.5, zorder=1)

    def _add_scale_bar(self, ax, length_mm: int = 30):
        """
        Add scale bar following Italian archaeological standard.

        Simple black bar with "3 cm" label below (standard Italian style).
        """
        # Place in bottom center
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # Center the scale bar
        x_center = (xlim[0] + xlim[1]) / 2
        x_start = x_center - length_mm / 2
        x_end = x_center + length_mm / 2
        y_pos = ylim[0] + (ylim[1] - ylim[0]) * 0.08

        # Draw thick solid black bar (Italian archaeological style)
        ax.plot([x_start, x_end], [y_pos, y_pos],
               'k-', linewidth=4, solid_capstyle='butt')

        # Add label below (simple "3 cm" style)
        ax.text(x_center, y_pos - 5, '3 cm',
               ha='center', va='top', fontsize=9, fontfamily='sans-serif')

    def _create_composite_sheet(self, mesh, artifact_id: str,
                                features: Dict, views: Dict) -> bytes:
        """
        Create complete professional composite sheet - ARCHAEOLOGICAL STANDARD LAYOUT.

        Layout (standard archeologico italiano):
        - Sinistra: Profilo longitudinale (vista laterale - PRINCIPALE)
        - Destra: 3 sezioni trasversali impilate (alta, media, bassa)
        - Info panel in basso
        """
        fig = plt.figure(figsize=(11, 14), dpi=self.dpi)  # A4 proportions

        # Title
        fig.suptitle(f'Documentazione Tecnica - {artifact_id}',
                    fontsize=14, fontweight='bold', y=0.98)

        # Create grid for archaeological layout
        gs = fig.add_gridspec(5, 2, hspace=0.25, wspace=0.3,
                             left=0.05, right=0.95, top=0.94, bottom=0.05,
                             height_ratios=[3, 1, 1, 1, 1.5])

        # SINISTRA: Profilo longitudinale (GRANDE - vista più importante!)
        ax_long = fig.add_subplot(gs[0:3, 0])
        self._plot_image_in_axis(ax_long, views['longitudinal_profile'])
        ax_long.set_title('Profilo Longitudinale', fontweight='bold', fontsize=12)

        # DESTRA: 3 sezioni trasversali impilate (standard archeologico)
        ax_high = fig.add_subplot(gs[0, 1])
        self._plot_image_in_axis(ax_high, views['cross_section_high'])

        ax_mid = fig.add_subplot(gs[1, 1])
        self._plot_image_in_axis(ax_mid, views['cross_section_mid'])

        ax_low = fig.add_subplot(gs[2, 1])
        self._plot_image_in_axis(ax_low, views['cross_section_low'])

        # Vista frontale (opzionale, in basso a sinistra)
        ax_front = fig.add_subplot(gs[3, 0])
        self._plot_image_in_axis(ax_front, views['front_view'])

        # Metadata panel (basso a destra)
        ax_info = fig.add_subplot(gs[3:5, 1])
        ax_info.axis('off')
        self._add_info_panel(ax_info, artifact_id, features)

        # Save composite
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=self.dpi, bbox_inches='tight')
        plt.close()
        buf.seek(0)

        return buf.getvalue()

    def _plot_image_in_axis(self, ax, image_bytes: bytes):
        """Plot image from bytes in axis."""
        img = Image.open(io.BytesIO(image_bytes))
        ax.imshow(img)
        ax.axis('off')

    def _add_info_panel(self, ax, artifact_id: str, features: Dict):
        """Add information panel with measurements and metadata."""
        info_text = f"IDENTIFICAZIONE\n"
        info_text += f"ID: {artifact_id}\n\n"

        if features:
            info_text += "DIMENSIONI\n"
            if 'length' in features:
                info_text += f"Lunghezza: {features['length']:.1f} mm\n"
            if 'width' in features:
                info_text += f"Larghezza: {features['width']:.1f} mm\n"
            if 'height' in features:
                info_text += f"Altezza: {features['height']:.1f} mm\n"
            if 'volume' in features:
                info_text += f"Volume: {features['volume']:.1f} mm³\n"
            if 'surface_area' in features:
                info_text += f"Superficie: {features['surface_area']:.1f} mm²\n"

            info_text += "\nFORMA\n"
            if 'compactness' in features:
                info_text += f"Compattezza: {features['compactness']:.3f}\n"
            if 'sphericity' in features:
                info_text += f"Sfericità: {features['sphericity']:.3f}\n"

        ax.text(0.05, 0.95, info_text, transform=ax.transAxes,
               fontsize=8, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))


# Singleton instance
_technical_drawing_generator = None


def get_technical_drawing_generator() -> TechnicalDrawingGenerator:
    """Get or create technical drawing generator instance."""
    global _technical_drawing_generator
    if _technical_drawing_generator is None:
        _technical_drawing_generator = TechnicalDrawingGenerator()
    return _technical_drawing_generator
