#!/usr/bin/env python3
"""
Technical Drawing Generator for Savignano Axes
==============================================

Generates professional archaeological technical drawings with measurements:
- Front view (vista frontale)
- Longitudinal profile (profilo longitudinale)
- Cross sections (sezioni trasversali)

Supports PDF export with multilanguage options (Italian, English, etc.)
"""

import numpy as np

# CRITICAL: Set matplotlib backend to non-GUI 'Agg' BEFORE importing pyplot
# This prevents "NSWindow should only be instantiated on the main thread!" error on macOS
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon, FancyBboxPatch, Arc
from matplotlib.lines import Line2D
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import trimesh
from datetime import datetime

# PDF export
from matplotlib.backends.backend_pdf import PdfPages


class TechnicalDrawingLocalizer:
    """Handles multilanguage support for technical drawings."""

    TRANSLATIONS = {
        'it': {
            'front_view': 'Vista Frontale',
            'longitudinal_profile': 'Profilo Longitudinale',
            'cross_sections': 'Sezioni Trasversali',
            'section': 'Sezione',
            'tallone': 'Tallone',
            'corpo': 'Corpo',
            'tagliente': 'Tagliente',
            'incavo': 'Incavo',
            'incavo_depth': 'Profondità Incavo',
            'incavo_width': 'Larghezza Incavo',
            'tallone_width': 'Larghezza Tallone',
            'tallone_thickness': 'Spessore Tallone',
            'tagliente_width': 'Larghezza Tagliente',
            'margini_rialzati': 'Margini Rialzati',
            'length': 'Lunghezza',
            'width': 'Larghezza',
            'thickness': 'Spessore',
            'weight': 'Peso',
            'scale': 'Scala',
            'artifact_id': 'ID Reperto',
            'date': 'Data',
            'morphometric_analysis': 'Analisi Morfometrica',
            'savignano_type': 'Tipo Savignano',
            'matrix': 'Matrice',
            'measurements': 'Misure'
        },
        'en': {
            'front_view': 'Front View',
            'longitudinal_profile': 'Longitudinal Profile',
            'cross_sections': 'Cross Sections',
            'section': 'Section',
            'tallone': 'Butt',
            'corpo': 'Body',
            'tagliente': 'Blade',
            'incavo': 'Socket',
            'incavo_depth': 'Socket Depth',
            'incavo_width': 'Socket Width',
            'tallone_width': 'Butt Width',
            'tallone_thickness': 'Butt Thickness',
            'tagliente_width': 'Blade Width',
            'margini_rialzati': 'Raised Flanges',
            'length': 'Length',
            'width': 'Width',
            'thickness': 'Thickness',
            'weight': 'Weight',
            'scale': 'Scale',
            'artifact_id': 'Artifact ID',
            'date': 'Date',
            'morphometric_analysis': 'Morphometric Analysis',
            'savignano_type': 'Savignano Type',
            'matrix': 'Matrix',
            'measurements': 'Measurements'
        }
    }

    def __init__(self, language='it'):
        """
        Initialize localizer.

        Args:
            language: Language code ('it', 'en')
        """
        self.language = language
        if language not in self.TRANSLATIONS:
            raise ValueError(f"Unsupported language: {language}. Use 'it' or 'en'")

    def get(self, key: str) -> str:
        """Get translated string."""
        return self.TRANSLATIONS[self.language].get(key, key)


class TechnicalDrawingGenerator:
    """
    Generates professional archaeological technical drawings from 3D meshes.
    """

    def __init__(self, mesh_path: str, features: Dict, language='it'):
        """
        Initialize generator.

        Args:
            mesh_path: Path to 3D mesh file (.obj, .stl, .ply)
            features: Savignano morphometric features dictionary
            language: Language for labels ('it' or 'en')
        """
        self.mesh_path = Path(mesh_path)
        self.mesh = trimesh.load(str(mesh_path))
        self.features = features
        self.localizer = TechnicalDrawingLocalizer(language)

        # Compute mesh properties
        self.mesh.vertices = self.mesh.vertices - self.mesh.centroid
        self.bbox = self.mesh.bounds

        # Drawing style
        self.style = {
            'outline_color': '#2c3e50',
            'outline_width': 1.5,
            'measurement_color': '#34495e',
            'measurement_width': 0.8,
            'socket_color': '#e74c3c',
            'socket_alpha': 0.2,
            'scale_color': '#7f8c8d',
            'font_size': 9,
            'title_font_size': 12
        }

    def generate_all_views(self, output_dir: str, artifact_id: str,
                          export_pdf=True) -> Dict[str, str]:
        """
        Generate all technical drawing views.

        Args:
            output_dir: Directory for output files
            artifact_id: Artifact identifier
            export_pdf: If True, also export as PDF

        Returns:
            Dictionary with paths to generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}

        # Generate individual views
        print(f"Generating technical drawings for {artifact_id}...")

        # 1. Front view
        print("  - Front view...")
        front_fig = self.generate_front_view()
        front_path = output_path / f"{artifact_id}_front_view.png"
        front_fig.savefig(front_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(front_fig)
        results['front'] = str(front_path)

        # 2. Longitudinal profile
        print("  - Longitudinal profile...")
        profile_fig = self.generate_profile_view()
        profile_path = output_path / f"{artifact_id}_longitudinal_profile.png"
        profile_fig.savefig(profile_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(profile_fig)
        results['profile'] = str(profile_path)

        # 3. Cross sections
        print("  - Cross sections...")
        sections_fig = self.generate_sections_view()
        sections_path = output_path / f"{artifact_id}_cross_sections.png"
        sections_fig.savefig(sections_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(sections_fig)
        results['sections'] = str(sections_path)

        # 4. Combined PDF
        if export_pdf:
            print("  - Exporting PDF...")
            pdf_path = output_path / f"{artifact_id}_technical_drawings.pdf"
            self.export_to_pdf(str(pdf_path), artifact_id)
            results['pdf'] = str(pdf_path)

        print(f"✓ Technical drawings generated in {output_dir}")
        return results

    def generate_front_view(self) -> plt.Figure:
        """Generate front view with width measurements."""
        fig, ax = plt.subplots(figsize=(8, 12))

        # Project mesh onto XZ plane (front view)
        vertices_2d = self.mesh.vertices[:, [0, 2]]  # X, Z coordinates
        outline = self._extract_outline(vertices_2d)

        # Draw outline
        poly = Polygon(outline, fill=False, edgecolor=self.style['outline_color'],
                      linewidth=self.style['outline_width'])
        ax.add_patch(poly)

        # Add measurements
        self._add_front_measurements(ax, outline)

        # Add socket highlighting if present
        if self.features.get('incavo_presente'):
            self._highlight_socket_front(ax, outline)

        # Styling
        self._style_axis(ax, self.localizer.get('front_view'))
        self._add_scale_bar(ax)

        return fig

    def generate_profile_view(self) -> plt.Figure:
        """Generate longitudinal profile with thickness measurements."""
        fig, ax = plt.subplots(figsize=(14, 7))

        # Project onto YZ plane (side view)
        vertices_2d = self.mesh.vertices[:, [1, 2]]  # Y, Z coordinates
        outline = self._extract_outline(vertices_2d)

        # Draw outline
        poly = Polygon(outline, fill=False, edgecolor=self.style['outline_color'],
                      linewidth=self.style['outline_width'])
        ax.add_patch(poly)

        # Highlight socket region if present
        if self.features.get('incavo_presente'):
            self._highlight_socket_profile(ax, outline)

        # Add measurements
        self._add_profile_measurements(ax, outline)

        # Styling
        self._style_axis(ax, self.localizer.get('longitudinal_profile'))
        self._add_scale_bar(ax)

        return fig

    def generate_sections_view(self) -> plt.Figure:
        """Generate cross-section views at key points."""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Three sections: tallone, corpo, tagliente
        sections = [
            (self.localizer.get('tallone'), self._get_section_at_z(0.9)),
            (self.localizer.get('corpo'), self._get_section_at_z(0.5)),
            (self.localizer.get('tagliente'), self._get_section_at_z(0.1))
        ]

        for ax, (label, section_verts) in zip(axes, sections):
            if section_verts is not None and len(section_verts) > 2:
                # Draw section outline
                poly = Polygon(section_verts, fill=True, facecolor='#ecf0f1',
                             edgecolor=self.style['outline_color'],
                             linewidth=self.style['outline_width'])
                ax.add_patch(poly)

                # Add width measurement
                width = np.ptp(section_verts[:, 0])
                self._add_dimension_line(
                    ax,
                    (section_verts[np.argmin(section_verts[:, 0]), 0],
                     section_verts[np.argmin(section_verts[:, 0]), 1]),
                    (section_verts[np.argmax(section_verts[:, 0]), 0],
                     section_verts[np.argmax(section_verts[:, 0]), 1]),
                    f"{width:.1f}mm",
                    'horizontal'
                )

                ax.set_aspect('equal')
                ax.set_title(f'{self.localizer.get("section")}: {label}',
                           fontsize=self.style['title_font_size'], fontweight='bold')
                ax.axis('off')
                ax.set_xlim(section_verts[:, 0].min() - 10, section_verts[:, 0].max() + 10)
                ax.set_ylim(section_verts[:, 1].min() - 10, section_verts[:, 1].max() + 10)

        fig.suptitle(self.localizer.get('cross_sections'),
                    fontsize=14, fontweight='bold', y=0.98)

        return fig

    def export_to_pdf(self, pdf_path: str, artifact_id: str):
        """
        Export all views to a single PDF document.

        Args:
            pdf_path: Path for output PDF
            artifact_id: Artifact identifier
        """
        with PdfPages(pdf_path) as pdf:
            # Cover page
            cover_fig = self._create_cover_page(artifact_id)
            pdf.savefig(cover_fig, bbox_inches='tight')
            plt.close(cover_fig)

            # Front view
            front_fig = self.generate_front_view()
            pdf.savefig(front_fig, bbox_inches='tight')
            plt.close(front_fig)

            # Profile view
            profile_fig = self.generate_profile_view()
            pdf.savefig(profile_fig, bbox_inches='tight')
            plt.close(profile_fig)

            # Sections
            sections_fig = self.generate_sections_view()
            pdf.savefig(sections_fig, bbox_inches='tight')
            plt.close(sections_fig)

            # Metadata page
            metadata = pdf.infodict()
            metadata['Title'] = f'Technical Drawings - {artifact_id}'
            metadata['Author'] = 'Archaeological Classifier System'
            metadata['Subject'] = 'Savignano Bronze Age Axe - Morphometric Analysis'
            metadata['Keywords'] = 'Archaeology, Bronze Age, Savignano, Morphometry'
            metadata['CreationDate'] = datetime.now()

    def _create_cover_page(self, artifact_id: str) -> plt.Figure:
        """Create PDF cover page with metadata."""
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')

        # Title
        ax.text(0.5, 0.85, self.localizer.get('morphometric_analysis'),
               ha='center', va='center', fontsize=24, fontweight='bold',
               transform=ax.transAxes)

        # Artifact ID
        ax.text(0.5, 0.75, f"{self.localizer.get('artifact_id')}: {artifact_id}",
               ha='center', va='center', fontsize=18,
               transform=ax.transAxes)

        # Classification
        if self.features.get('incavo_presente') and \
           self.features.get('margini_rialzati_presenti'):
            ax.text(0.5, 0.65, self.localizer.get('savignano_type'),
                   ha='center', va='center', fontsize=16, style='italic',
                   transform=ax.transAxes)

        # Matrix
        matrix_id = self.features.get('matrix_id', 'Unknown')
        if matrix_id and matrix_id != 'Unknown':
            ax.text(0.5, 0.58, f"{self.localizer.get('matrix')}: {matrix_id}",
                   ha='center', va='center', fontsize=14,
                   transform=ax.transAxes)

        # Key measurements table
        y_start = 0.45
        measurements = [
            (self.localizer.get('length'), self.features.get('length', 0)),
            (self.localizer.get('width'), self.features.get('width', 0)),
            (self.localizer.get('thickness'), self.features.get('thickness', 0)),
            (self.localizer.get('weight'), self.features.get('peso', 0)),
        ]

        ax.text(0.5, y_start + 0.05, self.localizer.get('measurements'),
               ha='center', va='center', fontsize=14, fontweight='bold',
               transform=ax.transAxes)

        for i, (label, value) in enumerate(measurements):
            y = y_start - (i * 0.05)
            unit = 'mm' if 'weight' not in label.lower() and 'peso' not in label.lower() else 'g'
            ax.text(0.3, y, label + ':', ha='right', va='center', fontsize=12,
                   transform=ax.transAxes)
            ax.text(0.32, y, f"{value:.1f} {unit}", ha='left', va='center',
                   fontsize=12, transform=ax.transAxes)

        # Date
        ax.text(0.5, 0.1, f"{self.localizer.get('date')}: {datetime.now().strftime('%Y-%m-%d')}",
               ha='center', va='center', fontsize=10, color='gray',
               transform=ax.transAxes)

        # Footer
        ax.text(0.5, 0.05, 'Generated by Archaeological Classifier System v3.0',
               ha='center', va='center', fontsize=9, color='gray',
               transform=ax.transAxes)

        return fig

    def _extract_outline(self, vertices_2d: np.ndarray) -> np.ndarray:
        """Extract 2D outline from projected vertices using convex hull."""
        from scipy.spatial import ConvexHull
        if len(vertices_2d) < 3:
            return vertices_2d
        hull = ConvexHull(vertices_2d)
        return vertices_2d[hull.vertices]

    def _get_section_at_z(self, relative_height: float) -> Optional[np.ndarray]:
        """
        Get cross-section at relative height (0.0 = bottom, 1.0 = top).

        Args:
            relative_height: Height as fraction of total height

        Returns:
            2D vertices of cross-section
        """
        z_min, z_max = self.bbox[0][2], self.bbox[1][2]
        z_cut = z_min + (z_max - z_min) * relative_height

        # Find vertices near the cutting plane
        tolerance = 2.0  # mm
        mask = np.abs(self.mesh.vertices[:, 2] - z_cut) < tolerance

        if mask.sum() < 3:
            return None

        section_verts_3d = self.mesh.vertices[mask]
        section_verts_2d = section_verts_3d[:, [0, 1]]  # X, Y coordinates

        # Return outline
        return self._extract_outline(section_verts_2d)

    def _add_dimension_line(self, ax, start, end, label, orientation='horizontal'):
        """Add dimension line with arrows and label."""
        # Draw main line
        ax.plot([start[0], end[0]], [start[1], end[1]],
               color=self.style['measurement_color'],
               linewidth=self.style['measurement_width'],
               linestyle='--', alpha=0.7)

        # Draw end ticks
        tick_size = 2
        if orientation == 'horizontal':
            ax.plot([start[0], start[0]], [start[1]-tick_size, start[1]+tick_size],
                   color=self.style['measurement_color'],
                   linewidth=self.style['measurement_width'])
            ax.plot([end[0], end[0]], [end[1]-tick_size, end[1]+tick_size],
                   color=self.style['measurement_color'],
                   linewidth=self.style['measurement_width'])
        else:
            ax.plot([start[0]-tick_size, start[0]+tick_size], [start[1], start[1]],
                   color=self.style['measurement_color'],
                   linewidth=self.style['measurement_width'])
            ax.plot([end[0]-tick_size, end[0]+tick_size], [end[1], end[1]],
                   color=self.style['measurement_color'],
                   linewidth=self.style['measurement_width'])

        # Add label
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        offset = 5 if orientation == 'horizontal' else 8

        ax.text(mid_x, mid_y + offset if orientation == 'horizontal' else mid_y,
               label, fontsize=self.style['font_size'],
               ha='center', va='bottom' if orientation == 'horizontal' else 'center',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                        edgecolor=self.style['measurement_color'], linewidth=0.5))

    def _add_front_measurements(self, ax, outline):
        """Add measurements to front view."""
        # Tallone width
        if self.features.get('tallone_larghezza'):
            top_points = outline[outline[:, 1] > np.percentile(outline[:, 1], 90)]
            if len(top_points) >= 2:
                left = top_points[np.argmin(top_points[:, 0])]
                right = top_points[np.argmax(top_points[:, 0])]
                self._add_dimension_line(ax, left, right,
                                        f"{self.features['tallone_larghezza']:.1f}mm",
                                        'horizontal')

        # Tagliente width
        if self.features.get('tagliente_larghezza'):
            bottom_points = outline[outline[:, 1] < np.percentile(outline[:, 1], 10)]
            if len(bottom_points) >= 2:
                left = bottom_points[np.argmin(bottom_points[:, 0])]
                right = bottom_points[np.argmax(bottom_points[:, 0])]
                self._add_dimension_line(ax, left, right,
                                        f"{self.features['tagliente_larghezza']:.1f}mm",
                                        'horizontal')

    def _add_profile_measurements(self, ax, outline):
        """Add measurements to profile view."""
        # Length
        if self.features.get('length'):
            top = outline[np.argmax(outline[:, 1])]
            bottom = outline[np.argmin(outline[:, 1])]
            self._add_dimension_line(ax, bottom, top,
                                    f"{self.features['length']:.1f}mm",
                                    'vertical')

        # Tallone thickness
        if self.features.get('tallone_spessore'):
            top_points = outline[outline[:, 1] > np.percentile(outline[:, 1], 90)]
            if len(top_points) >= 2:
                front = top_points[np.argmax(top_points[:, 0])]
                back = top_points[np.argmin(top_points[:, 0])]
                self._add_dimension_line(ax, back, front,
                                        f"{self.features['tallone_spessore']:.1f}mm",
                                        'horizontal')

    def _highlight_socket_front(self, ax, outline):
        """Highlight socket region on front view."""
        # Socket is at top
        socket_depth = self.features.get('incavo_profondita', 10)
        top_y = outline[:, 1].max()
        socket_threshold = top_y - socket_depth

        socket_region = outline[outline[:, 1] > socket_threshold]
        if len(socket_region) > 2:
            poly = Polygon(socket_region, fill=True,
                          facecolor=self.style['socket_color'],
                          alpha=self.style['socket_alpha'],
                          edgecolor='none')
            ax.add_patch(poly)

    def _highlight_socket_profile(self, ax, outline):
        """Highlight socket region on profile view."""
        socket_depth = self.features.get('incavo_profondita', 10)
        top_y = outline[:, 1].max()
        socket_threshold = top_y - socket_depth

        socket_region = outline[outline[:, 1] > socket_threshold]
        if len(socket_region) > 2:
            poly = Polygon(socket_region, fill=True,
                          facecolor=self.style['socket_color'],
                          alpha=self.style['socket_alpha'],
                          edgecolor='red', linewidth=1, linestyle='--')
            ax.add_patch(poly)

            # Add label
            centroid = socket_region.mean(axis=0)
            ax.text(centroid[0], centroid[1],
                   f"{self.localizer.get('incavo')}\n{socket_depth:.1f}mm",
                   ha='center', va='center', fontsize=8,
                   color='darkred', fontweight='bold')

    def _add_scale_bar(self, ax, length_mm=50):
        """Add scale bar to drawing."""
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        x_start = xlim[0] + (xlim[1] - xlim[0]) * 0.1
        y_pos = ylim[0] + (ylim[1] - ylim[0]) * 0.05

        # Draw scale bar
        ax.plot([x_start, x_start + length_mm], [y_pos, y_pos],
               color=self.style['scale_color'], linewidth=2)

        # Draw ticks
        ax.plot([x_start, x_start], [y_pos - 1, y_pos + 1],
               color=self.style['scale_color'], linewidth=1.5)
        ax.plot([x_start + length_mm, x_start + length_mm], [y_pos - 1, y_pos + 1],
               color=self.style['scale_color'], linewidth=1.5)

        # Label
        ax.text(x_start + length_mm/2, y_pos - 3,
               f'{length_mm}mm',
               fontsize=8, ha='center', va='top',
               color=self.style['scale_color'])

    def _style_axis(self, ax, title):
        """Apply consistent styling to axis."""
        ax.set_aspect('equal')
        ax.set_title(title, fontsize=self.style['title_font_size'],
                    fontweight='bold', pad=15)
        ax.axis('off')


# Convenience function
def generate_technical_drawings(mesh_path: str, features: Dict,
                               output_dir: str, artifact_id: str,
                               language='it', export_pdf=True) -> Dict[str, str]:
    """
    Generate technical drawings for a Savignano axe.

    Args:
        mesh_path: Path to 3D mesh file
        features: Savignano morphometric features
        output_dir: Output directory for drawings
        artifact_id: Artifact identifier
        language: Language for labels ('it' or 'en')
        export_pdf: If True, also export as PDF

    Returns:
        Dictionary with paths to generated files
    """
    generator = TechnicalDrawingGenerator(mesh_path, features, language)
    return generator.generate_all_views(output_dir, artifact_id, export_pdf)


# Example usage
if __name__ == "__main__":
    # Test with sample mesh
    test_mesh = "/Volumes/extesione4T/3dasce/axe974/axe974.obj"
    test_features = {
        'artifact_id': 'axe974',
        'incavo_presente': True,
        'incavo_larghezza': 45.2,
        'incavo_profondita': 12.3,
        'margini_rialzati_presenti': True,
        'tallone_larghezza': 42.1,
        'tallone_spessore': 15.6,
        'tagliente_larghezza': 98.6,
        'length': 165.3,
        'width': 98.6,
        'thickness': 28.9,
        'peso': 387.0,
        'matrix_id': 'MAT_A'
    }

    # Generate drawings in both languages
    for lang in ['it', 'en']:
        print(f"\n=== Generating drawings in {lang.upper()} ===")
        output_dir = f"./test_drawings_{lang}"
        results = generate_technical_drawings(
            test_mesh,
            test_features,
            output_dir,
            'axe974',
            language=lang,
            export_pdf=True
        )

        print(f"\nGenerated files:")
        for view, path in results.items():
            print(f"  {view}: {path}")
