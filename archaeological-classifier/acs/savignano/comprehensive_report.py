#!/usr/bin/env python3
"""
Comprehensive Archaeological Report Generator for Savignano Axes
================================================================

Generates complete professional archaeological reports including:
- Realistic 3D mesh renderings (front, profile, sections)
- Socket (incavo) visualization
- Complete measurements table
- AI interpretation and classification
- Hammering (martellamento) analysis
- Casting technique analysis
- PCA and clustering analysis
- Comparative analysis with other axes
- Multi-page professional PDF export

Author: Archaeological Classifier System
Date: November 2025
"""

import numpy as np
import trimesh
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import json

# Matplotlib with Agg backend for headless rendering
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon
import matplotlib.gridspec as gridspec


class SavignanoComprehensiveReport:
    """Generates comprehensive archaeological reports for Savignano axes."""

    def __init__(self, mesh_path: str, features: Dict, artifact_id: str, language: str = 'it'):
        """
        Initialize report generator.

        Args:
            mesh_path: Path to the 3D mesh file (OBJ)
            features: Dictionary of Savignano morphometric features
            artifact_id: Unique artifact identifier
            language: Report language ('it' or 'en')
        """
        self.mesh_path = Path(mesh_path)
        self.features = features
        self.artifact_id = artifact_id
        self.language = language

        # Load mesh
        print(f"Loading mesh from {mesh_path}...")
        self.mesh = trimesh.load(str(mesh_path))

        # Translations
        self.translations = self._init_translations()

    def _init_translations(self) -> Dict:
        """Initialize translation strings."""
        return {
            'it': {
                'title': 'Rapporto Archeologico Completo',
                'subtitle': 'Ascia Savignano',
                'page_morphometry': 'Analisi Morfometrica',
                'page_3d': 'Visualizzazione 3D e Sezioni',
                'page_ai': 'Interpretazione AI',
                'page_techniques': 'Analisi Tecniche di Produzione',
                'page_pca': 'Analisi Statistica (PCA)',
                'page_comparison': 'Analisi Comparativa',
                'measurements': 'Misurazioni',
                'socket': 'Incavo',
                'butt': 'Tallone',
                'blade': 'Tagliente',
                'flanges': 'Margini Rialzati',
                'present': 'Presente',
                'absent': 'Assente',
                'length': 'Lunghezza',
                'width': 'Larghezza',
                'depth': 'Profondità',
                'thickness': 'Spessore',
                'weight': 'Peso',
                'shape': 'Forma',
                'hammering_analysis': 'Analisi Martellamento',
                'casting_analysis': 'Analisi Tecnica di Fusione',
                'ai_interpretation': 'Interpretazione AI',
                'statistical_analysis': 'Analisi Statistica',
                'comparative_analysis': 'Analisi Comparativa',
                'front_view': 'Vista Frontale',
                'profile_view': 'Vista Profilo',
                'cross_sections': 'Sezioni Trasversali',
                'matrix': 'Matrice',
                'generated_on': 'Generato il',
            },
            'en': {
                'title': 'Comprehensive Archaeological Report',
                'subtitle': 'Savignano Axe',
                'page_morphometry': 'Morphometric Analysis',
                'page_3d': '3D Visualization and Sections',
                'page_ai': 'AI Interpretation',
                'page_techniques': 'Production Technique Analysis',
                'page_pca': 'Statistical Analysis (PCA)',
                'page_comparison': 'Comparative Analysis',
                'measurements': 'Measurements',
                'socket': 'Socket',
                'butt': 'Butt',
                'blade': 'Blade',
                'flanges': 'Raised Flanges',
                'present': 'Present',
                'absent': 'Absent',
                'length': 'Length',
                'width': 'Width',
                'depth': 'Depth',
                'thickness': 'Thickness',
                'weight': 'Weight',
                'shape': 'Shape',
                'hammering_analysis': 'Hammering Analysis',
                'casting_analysis': 'Casting Technique Analysis',
                'ai_interpretation': 'AI Interpretation',
                'statistical_analysis': 'Statistical Analysis',
                'comparative_analysis': 'Comparative Analysis',
                'front_view': 'Front View',
                'profile_view': 'Profile View',
                'cross_sections': 'Cross Sections',
                'matrix': 'Matrix',
                'generated_on': 'Generated on',
            }
        }

    def t(self, key: str) -> str:
        """Get translated string."""
        return self.translations.get(self.language, {}).get(key, key)

    def _create_table_of_contents_page(self, pdf):
        """Create professional Table of Contents page (Indice)."""
        fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Title - REDUCED to 10pt to fit on one page
        ax.text(0.5, 0.95, 'INDICE / TABLE OF CONTENTS',
               ha='center', fontsize=10, fontweight='bold', color='#2C3E50')

        # Subtitle - REDUCED to 8pt to fit on one page
        ax.text(0.5, 0.91, f'Rapporto Archeologico Completo - {self.artifact_id}',
               ha='center', fontsize=8, style='italic', color='#34495E')

        # Separator line
        ax.plot([0.1, 0.9], [0.88, 0.88], 'k-', linewidth=1.5, alpha=0.5)

        # Table of contents entries - UPDATED for 8-page structure
        toc_data = [
            (1, 'COPERTINA E MORFOMETRIA', [
                ('1.1', 'Identificazione Artefatto'),
                ('1.2', 'Tabella Misure Morfometriche'),
                ('1.3', 'Features Savignano-Specific'),
            ]),
            (2, 'DISEGNI TECNICI ARCHEOLOGICI', [
                ('2.1', 'Prospetto (Vista Frontale)'),
                ('2.2', 'Profilo Longitudinale (Vista Laterale)'),
                ('2.3', 'Sezione Trasversale Tallone (80%)'),
            ]),
            (3, 'INTERPRETAZIONE AI', [
                ('3.1', 'Valutazione Morfometrica'),
                ('3.2', 'Classificazione Tipologica'),
                ('3.3', 'Note Archeologiche'),
            ]),
            (4, 'ANALISI MARTELLATURA', [
                ('4.1', 'Rugosità superficiale per regione'),
                ('4.2', 'Interpretazione lavorazione a freddo'),
            ]),
            (5, 'ANALISI FUSIONE', [
                ('5.1', 'Simmetria bilaterale'),
                ('5.2', 'Variazione spessore'),
                ('5.3', 'Tecnica dello stampo'),
            ]),
            (6, 'ANALISI STATISTICA (PCA)', [
                ('6.1', 'Scatter Plot Componenti Principali'),
                ('6.2', 'Loadings e Varianza Spiegata'),
                ('6.3', 'Interpretazione Archeologica'),
            ]),
            (7, 'ANALISI COMPARATIVA', [
                ('7.1', 'Top-5 Artefatti Simili'),
                ('7.2', 'Grafici Similarità'),
                ('7.3', 'Implicazioni Archeologiche'),
            ]),
        ]

        y_pos = 0.83
        line_height = 0.020  # REDUCED from 0.025 to 0.020 for tighter spacing

        for page_num, section_title, subsections in toc_data:
            # Main section - REDUCED to 7pt
            ax.text(0.12, y_pos, f'{page_num}.', ha='left', fontsize=7, fontweight='bold', color='#2980B9')
            ax.text(0.17, y_pos, section_title, ha='left', fontsize=7, fontweight='bold', color='#2980B9')
            # Clickable page number link - REDUCED to 6pt
            ax.text(0.88, y_pos, f'{page_num}', ha='right', fontsize=6, fontweight='bold', color='#2980B9',
                   url=f'#page={page_num}')

            # Dotted line
            n_dots = int((0.88 - 0.17 - len(section_title)*0.005) / 0.01)
            dots_x = np.linspace(0.17 + len(section_title)*0.005, 0.86, n_dots)
            for dot_x in dots_x[::3]:  # Every 3rd position for spacing
                ax.plot(dot_x, y_pos + 0.003, 'k.', markersize=1.5, alpha=0.3)

            y_pos -= line_height

            # Subsections - REDUCED to 6pt
            for sub_num, sub_title in subsections:
                if sub_num.strip():
                    ax.text(0.20, y_pos, sub_num, ha='left', fontsize=6, color='#7F8C8D')
                ax.text(0.26, y_pos, sub_title, ha='left', fontsize=6, color='#34495E')
                y_pos -= line_height * 0.85

            y_pos -= line_height * 0.3  # Extra space between sections

        # Footer
        ax.plot([0.1, 0.9], [0.08, 0.08], 'k-', linewidth=1, alpha=0.3)
        ax.text(0.5, 0.05, f'Generato il {datetime.now().strftime("%d/%m/%Y %H:%M")}',
               ha='center', fontsize=8, style='italic', color='gray')
        ax.text(0.5, 0.025, 'Sistema di Classificazione Archeologica - Asce Savignano',
               ha='center', fontsize=8, color='gray')

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def generate_complete_report(self, output_path: str) -> Dict:
        """
        Generate complete archaeological report.

        Returns:
            Dictionary with paths to generated files
        """
        output_path = Path(output_path)

        print(f"Generating comprehensive archaeological report for {self.artifact_id}...")

        # VERIFY AND LOG INCAVO MEASUREMENTS WITH VALIDATION
        if self.features.get('incavo_presente', False):
            print(f"\n  === INCAVO MEASUREMENTS DEBUG ===")
            incavo_larghezza = self.features.get('incavo_larghezza')
            incavo_profondita = self.features.get('incavo_profondita')
            incavo_profilo = self.features.get('incavo_profilo')
            tallone_larghezza = self.features.get('tallone_larghezza')

            if incavo_larghezza is not None:
                print(f"    - Larghezza (width): {incavo_larghezza:.2f} mm")

                # VALIDATION: Incavo width should be <= tallone width
                if tallone_larghezza is not None:
                    if incavo_larghezza > tallone_larghezza:
                        print(f"    ⚠️  WARNING: Incavo width ({incavo_larghezza:.1f}mm) > tallone width ({tallone_larghezza:.1f}mm)")
                        print(f"        This is geometrically impossible - check measurement extraction!")
                    else:
                        print(f"    ✓  Valid: Incavo width < tallone width ({tallone_larghezza:.1f}mm)")

            if incavo_profondita is not None:
                print(f"    - Profondità (depth): {incavo_profondita:.2f} mm")

                # VALIDATION: Incavo depth should be reasonable (typically < 20mm)
                if incavo_profondita > 20.0:
                    print(f"    ⚠️  WARNING: Incavo depth ({incavo_profondita:.1f}mm) seems unusually large")
                    print(f"        Typical values are 2-15mm - verify measurement!")
                elif incavo_profondita < 1.0:
                    print(f"    ⚠️  WARNING: Incavo depth ({incavo_profondita:.1f}mm) seems too shallow")
                    print(f"        Values < 1mm are unlikely for a functional socket")
                else:
                    print(f"    ✓  Valid: Depth within normal range (1-20mm)")

            if incavo_profilo is not None:
                print(f"    - Profilo (profile): {incavo_profilo}")

            print(f"  === END INCAVO DEBUG ===\n")
        else:
            print(f"  INCAVO: Not present")

        results = {}

        with PdfPages(str(output_path)) as pdf:
            # Page 0: Professional Table of Contents (INDEX)
            print("  - Page 0: Table of Contents (Indice)...")
            self._create_table_of_contents_page(pdf)

            # Page 1: Cover + Morphometric Measurements
            print("  - Page 1: Cover and Morphometry...")
            self._create_cover_and_morphometry_page(pdf)

            # Page 2: Technical Drawings (3D Visualizations)
            print("  - Page 2: Technical Drawings...")
            self._create_3d_visualization_page(pdf)

            # Page 3: AI Interpretation
            print("  - Page 3: AI Interpretation...")
            self._create_ai_interpretation_page(pdf)

            # Page 4: Hammering Analysis (SEPARATE PAGE)
            print("  - Page 4: Hammering Analysis...")
            self._create_hammering_analysis_page(pdf)

            # Page 5: Casting Analysis (SEPARATE PAGE)
            print("  - Page 5: Casting Analysis...")
            self._create_casting_analysis_page(pdf)

            # Page 6: PCA and Clustering
            print("  - Page 6: Statistical Analysis (PCA)...")
            self._create_pca_analysis_page(pdf)

            # Page 7: Comparative Analysis
            print("  - Page 7: Comparative Analysis...")
            self._create_comparative_analysis_page(pdf)

        results['pdf'] = str(output_path)

        print(f"✓ Comprehensive report generated: {output_path}")

        return results

    def _create_cover_and_morphometry_page(self, pdf):
        """Create cover page with complete measurements table."""
        fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        gs = gridspec.GridSpec(4, 1, height_ratios=[1, 2, 1, 0.2], hspace=0.3)

        # Title section - reduced font sizes and adjusted positions to avoid overlap
        ax_title = fig.add_subplot(gs[0])
        ax_title.axis('off')
        ax_title.text(0.5, 0.7, self.t('title'),
                     ha='center', va='center', fontsize=16, fontweight='bold')
        ax_title.text(0.5, 0.4, f"{self.t('subtitle')} - {self.artifact_id}",
                     ha='center', va='center', fontsize=12)
        ax_title.text(0.5, 0.1, f"{self.t('generated_on')} {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                     ha='center', va='center', fontsize=9, style='italic')

        # Measurements table
        ax_table = fig.add_subplot(gs[1])
        ax_table.axis('off')

        # Build measurements data
        measurements_data = self._build_measurements_table()

        # Create table
        table = ax_table.table(cellText=measurements_data['data'],
                              colLabels=measurements_data['headers'],
                              cellLoc='left',
                              loc='center',
                              colWidths=[0.4, 0.3, 0.3])

        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)

        # Style table
        for (i, j), cell in table.get_celld().items():
            if i == 0:  # Header
                cell.set_facecolor('#4A90E2')
                cell.set_text_props(weight='bold', color='white')
            elif i % 2 == 0:
                cell.set_facecolor('#F0F0F0')

        # Summary section
        ax_summary = fig.add_subplot(gs[2])
        ax_summary.axis('off')

        summary_text = self._generate_summary_text()
        ax_summary.text(0.1, 0.5, summary_text, ha='left', va='center',
                       fontsize=10, wrap=True)

        # Footer with page number
        ax_footer = fig.add_subplot(gs[3])
        ax_footer.axis('off')
        ax_footer.text(0.5, 0.5, f'{self.artifact_id} | Pagina 1',
                     ha='center', va='center', fontsize=9, color='gray')

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _build_measurements_table(self) -> Dict:
        """Build complete measurements table data."""
        headers = [self.t('measurements'), 'Value', 'Unit']
        data = []

        f = self.features

        # Total length
        if 'lunghezza_totale' in f:
            data.append([self.t('length') + ' totale', f'{f["lunghezza_totale"]:.2f}', 'mm'])

        # Socket (Incavo)
        socket_status = self.t('present') if f.get('incavo_presente', False) else self.t('absent')
        data.append([f"{self.t('socket')} - Status", socket_status, ''])
        if f.get('incavo_presente', False):
            if 'incavo_larghezza' in f:
                data.append([f"  {self.t('width')}", f'{f["incavo_larghezza"]:.2f}', 'mm'])
            if 'incavo_profondita' in f:
                data.append([f"  {self.t('depth')}", f'{f["incavo_profondita"]:.2f}', 'mm'])

        # Butt (Tallone)
        data.append([f"{self.t('butt')}", '', ''])
        if 'tallone_larghezza' in f:
            data.append([f"  {self.t('width')}", f'{f["tallone_larghezza"]:.2f}', 'mm'])
        if 'tallone_spessore' in f:
            data.append([f"  {self.t('thickness')}", f'{f["tallone_spessore"]:.2f}', 'mm'])

        # Blade (Tagliente)
        data.append([f"{self.t('blade')}", '', ''])
        if 'tagliente_larghezza' in f:
            data.append([f"  {self.t('width')}", f'{f["tagliente_larghezza"]:.2f}', 'mm'])
        if 'tagliente_arco_misura' in f:
            data.append([f"  Arco", f'{f["tagliente_arco_misura"]:.2f}', 'mm'])
        if 'tagliente_corda_misura' in f:
            data.append([f"  Corda", f'{f["tagliente_corda_misura"]:.2f}', 'mm'])
        if 'tagliente_forma' in f:
            data.append([f"  {self.t('shape')}", f['tagliente_forma'], ''])

        # Raised Flanges (Margini Rialzati)
        flanges_status = self.t('present') if f.get('margini_rialzati_presenti', False) else self.t('absent')
        data.append([f"{self.t('flanges')} - Status", flanges_status, ''])
        if f.get('margini_rialzati_presenti', False) and 'margini_rialzati_lunghezza' in f:
            data.append([f"  {self.t('length')}", f'{f["margini_rialzati_lunghezza"]:.2f}', 'mm'])

        # Matrix
        if 'matrix_id' in f:
            data.append([self.t('matrix'), f['matrix_id'], ''])

        # Weight
        if 'peso' in f and f['peso'] > 0:
            data.append([self.t('weight'), f'{f["peso"]:.2f}', 'g'])

        return {'headers': headers, 'data': data}

    def _generate_summary_text(self) -> str:
        """Generate summary text for cover page."""
        f = self.features

        summary_parts = []

        # Socket description
        if f.get('incavo_presente', False):
            socket_desc = f"{self.t('socket')}: {self.t('present')}"
            if 'incavo_larghezza' in f and 'incavo_profondita' in f:
                socket_desc += f" ({f['incavo_larghezza']:.1f} x {f['incavo_profondita']:.1f} mm)"
            summary_parts.append(socket_desc)

        # Matrix classification
        if 'matrix_id' in f:
            summary_parts.append(f"{self.t('matrix')}: {f['matrix_id']}")

        # Raised flanges
        if f.get('margini_rialzati_presenti', False):
            summary_parts.append(f"{self.t('flanges')}: {self.t('present')}")

        return " • ".join(summary_parts) if summary_parts else ""

    def _calculate_global_dimensions(self):
        """Calculate global dimensions from mesh for uniform scaling across subplots.
        Returns: (max_width, max_length, max_thickness) in mm"""
        vertices = self.mesh.vertices
        x_range = vertices[:, 0].max() - vertices[:, 0].min()  # Width
        y_range = vertices[:, 1].max() - vertices[:, 1].min()  # Length
        z_range = vertices[:, 2].max() - vertices[:, 2].min()  # Thickness

        # TASK 5: Return global max dimensions for uniform scaling
        return (x_range, y_range, z_range)

    def _create_3d_visualization_page(self, pdf):
        """Create technical drawings page following archaeological standards.

        CRITICAL LAYOUT (Professional Publication Standard):
        ┌─────────────────────────────────────────────────────────┐
        │  SEZIONE TALLONE (80%) - Top                            │
        │  [Same width as prospetto below]                        │
        ├────────────────────────┬────────────────────────────────┤
        │                        │                                │
        │                        │   PROFILO LONGITUDINALE        │
        │      PROSPETTO         │   (vertical orientation)       │
        │    (front view)        │   [Same HEIGHT as prospetto]   │
        │                        │                                │
        │                        │                                │
        ├────────────────────────┴────────────────────────────────┤
        │  SEZIONE TAGLIENTE (20%) - Bottom                       │
        │  [Same width as prospetto above]                        │
        └─────────────────────────────────────────────────────────┘
        """

        # Calculate global dimensions for uniform scale
        global_dims = self._calculate_global_dimensions()

        fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape

        # Create GridSpec with 2 rows, 2 columns
        # Row heights: tallone section (small), prospetto (large)
        # Column widths: prospetto (wide), profilo (narrow)
        # FIXED: Profilo spans both rows to be same height as prospetto
        gs = gridspec.GridSpec(2, 2,
                              hspace=0.25, wspace=0.30,
                              height_ratios=[1, 3],        # Smaller sezione, larger prospetto
                              width_ratios=[2.2, 1],       # Prospetto wider, profilo narrower
                              left=0.06, right=0.96,       # Better margins for centering
                              top=0.93, bottom=0.08)       # Vertical centering

        # Title
        fig.suptitle(f"Disegni Tecnici Archeologici - {self.artifact_id}",
                    fontsize=13, fontweight='bold', y=0.97)

        # 2. PROSPETTO (Bottom left - full detail with annotations) - RENDER FIRST to get width AND length
        ax_prospetto = fig.add_subplot(gs[1, 0])
        prospetto_width, butt_width, prospetto_length = self._render_prospetto(ax_prospetto, global_dims)
        ax_prospetto.set_title('Prospetto (Vista Frontale)',
                              fontweight='bold', fontsize=10, pad=8)

        # 1. SEZIONE TALLONE (Top left - MATCH butt width at 80% position, NOT full prospetto width!)
        ax_sezione_tallone = fig.add_subplot(gs[0, 0])
        self._render_sezione(ax_sezione_tallone, 0.8, global_dims, butt_width)
        ax_sezione_tallone.set_title('Sezione Trasversale - Tallone (80%)',
                                    fontweight='bold', fontsize=9, pad=5)

        # 3. PROFILO LONGITUDINALE (Right side - SPANS BOTH ROWS for full height, MATCH prospetto length!)
        ax_profilo = fig.add_subplot(gs[:, 1])  # Span both rows
        self._render_profilo_longitudinale(ax_profilo, global_dims, prospetto_length)
        ax_profilo.set_title('Profilo Longitudinale (Vista Laterale)',
                            fontweight='bold', fontsize=9, pad=5)

        # Save without bbox_inches='tight' to preserve manual GridSpec centering
        # Force white background for figure and all axes
        fig.patch.set_facecolor('white')
        for ax in fig.get_axes():
            ax.set_facecolor('white')
        pdf.savefig(fig, facecolor='white')
        plt.close(fig)

    def _render_mesh_view(self, ax, view_type: str):
        """Render mesh from specified view angle."""
        # Get mesh projection based on view type
        vertices = self.mesh.vertices.copy()

        if view_type == 'front':
            # Front view: project onto YZ plane
            projected = vertices[:, [1, 2]]
        elif view_type == 'profile':
            # Profile view: project onto XZ plane
            projected = vertices[:, [0, 2]]
        else:
            projected = vertices[:, [0, 1]]

        # CRITICAL FIX: Subsample vertices to reduce PDF size
        # Use only 1% of vertices (max 5000 points) to keep PDF under 1MB
        n_points = len(projected)
        max_points = 5000
        subsample_indices = None
        if n_points > max_points:
            subsample_rate = max_points / n_points
            subsample_indices = np.random.choice(n_points, max_points, replace=False)
            projected_display = projected[subsample_indices]
        else:
            projected_display = projected

        # Plot mesh outline (rasterized for smaller file size)
        ax.scatter(projected_display[:, 0], projected_display[:, 1], s=0.1, c='black', alpha=0.3, rasterized=True)

        # Highlight socket if present (use original projected vertices for correct threshold calculation)
        if self.features.get('incavo_presente', False) and view_type == 'profile':
            self._highlight_socket(ax, projected, subsample_indices)

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('mm')
        ax.set_ylabel('mm')

    def _highlight_socket(self, ax, projected_vertices, subsample_indices=None):
        """Highlight socket (incavo) region in profile view."""
        # Find socket region (top ~20% of the mesh in Z direction)
        # Use full vertices for accurate threshold calculation
        z_coords = projected_vertices[:, 1]
        z_threshold = np.percentile(z_coords, 80)
        socket_mask = z_coords >= z_threshold
        socket_points = projected_vertices[socket_mask]

        # If subsampling was applied, also subsample socket points
        if subsample_indices is not None and len(socket_points) > 0:
            # Find which subsampled indices are in socket region
            socket_indices_in_subsample = np.isin(subsample_indices, np.where(socket_mask)[0])
            if np.any(socket_indices_in_subsample):
                socket_points = projected_vertices[subsample_indices[socket_indices_in_subsample]]

        # Limit socket points to max 1000 for PDF size
        if len(socket_points) > 1000:
            socket_indices = np.random.choice(len(socket_points), 1000, replace=False)
            socket_points = socket_points[socket_indices]

        if len(socket_points) > 0:
            ax.scatter(socket_points[:, 0], socket_points[:, 1],
                      s=1, c='red', alpha=0.6, label=self.t('socket'), rasterized=True)
            ax.legend()

    def _render_cross_sections(self, ax):
        """Render cross-sectional views."""
        # Extract 3 cross sections: butt, middle, blade
        z_coords = self.mesh.vertices[:, 2]
        z_min, z_max = z_coords.min(), z_coords.max()

        sections_z = [
            z_min + 0.2 * (z_max - z_min),  # Butt
            z_min + 0.5 * (z_max - z_min),  # Middle
            z_min + 0.8 * (z_max - z_min),  # Blade
        ]

        section_labels = [self.t('butt'), 'Middle', self.t('blade')]

        for i, (z, label) in enumerate(zip(sections_z, section_labels)):
            # Extract vertices near this Z plane
            tolerance = (z_max - z_min) * 0.05
            mask = np.abs(z_coords - z) < tolerance
            section_verts = self.mesh.vertices[mask][:, [0, 1]]

            if len(section_verts) > 0:
                # Subsample section vertices to reduce PDF size (max 1000 points per section)
                if len(section_verts) > 1000:
                    indices = np.random.choice(len(section_verts), 1000, replace=False)
                    section_verts = section_verts[indices]

                offset_x = i * 100  # Horizontal offset for each section
                ax.scatter(section_verts[:, 0] + offset_x, section_verts[:, 1],
                          s=0.5, label=label, rasterized=True)

        ax.set_aspect('equal')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('mm')
        ax.set_ylabel('mm')

    # NEW RENDERING FUNCTIONS - ARCHAEOLOGICAL TECHNICAL DRAWING STANDARD

    def _render_prospetto(self, ax, global_dims=None):
        """Render PROSPETTO (front view) - complete XY projection with all details.
        This is the main technical view showing the artifact from the front.

        Args:
            ax: Matplotlib axis to render on
            global_dims: Tuple of (max_width, max_length, max_thickness) for uniform scaling
        """
        vertices = self.mesh.vertices

        # Project to XY plane (width x length)
        projected = vertices[:, [0, 1]]

        # TASK 1: Normalize to origin (0, 0)
        x_min = projected[:, 0].min()
        y_min = projected[:, 1].min()
        projected[:, 0] -= x_min
        projected[:, 1] -= y_min

        # Also normalize original vertices for annotations
        vertices_normalized = vertices.copy()
        vertices_normalized[:, 0] -= x_min
        vertices_normalized[:, 1] -= y_min

        # Subsample to ~15000 points for performance but keep detail
        n_points = len(projected)
        if n_points > 15000:
            indices = np.random.choice(n_points, 15000, replace=False)
            projected = projected[indices]
            vertices_sub = vertices_normalized[indices]
        else:
            vertices_sub = vertices_normalized

        # FORCE white background for the axes
        ax.set_facecolor('white')

        # Draw ALL projected points in very light gray to show the shape WHITE interior
        # This preserves concavities (like the socket/incavo) that ConvexHull would fill
        ax.scatter(projected[:, 0], projected[:, 1],
                  c='lightgray', s=0.2, alpha=0.2, zorder=1, edgecolors='none')

        # Find approximate outline using edge detection on X/Y extremes
        # Group points by angle and find edge points
        center = projected.mean(axis=0)
        angles = np.arctan2(projected[:, 1] - center[1], projected[:, 0] - center[0])

        # Divide into angular bins to find edge points
        n_bins = 360
        angle_bins = np.linspace(-np.pi, np.pi, n_bins)
        edge_points = []

        for i in range(len(angle_bins) - 1):
            mask = (angles >= angle_bins[i]) & (angles < angle_bins[i+1])
            if np.any(mask):
                bin_points = projected[mask]
                # Find the point furthest from center in this angular bin
                distances = np.sqrt(np.sum((bin_points - center)**2, axis=1))
                furthest_idx = np.argmax(distances)
                edge_points.append(bin_points[furthest_idx])

        if len(edge_points) > 0:
            edge_array = np.array(edge_points)
            # Close the outline
            edge_closed = np.vstack([edge_array, edge_array[0]])
            # Draw black outline
            ax.plot(edge_closed[:, 0], edge_closed[:, 1],
                   'k-', linewidth=1.5, zorder=2)

        # MARGINI RIALZATI - Highlight raised flanges if present (green thick lines on edges)
        if self.features.get('margini_rialzati_presenti', False):
            x_coords_proj = projected[:, 0]
            y_coords_proj = projected[:, 1]

            # Define flange regions: leftmost and rightmost 15% of X coordinates
            x_left_threshold = np.percentile(x_coords_proj, 15)
            x_right_threshold = np.percentile(x_coords_proj, 85)

            # Also limit to upper portion (tallone region - top 30%)
            y_top_threshold = np.percentile(y_coords_proj, 70)

            # Left flange
            left_mask = (x_coords_proj <= x_left_threshold) & (y_coords_proj >= y_top_threshold)
            left_flange = projected[left_mask]
            if len(left_flange) > 0:
                # Sort by Y coordinate for continuous line
                left_sorted = left_flange[np.argsort(left_flange[:, 1])]
                ax.plot(left_sorted[:, 0], left_sorted[:, 1],
                       'g-', linewidth=2.5, alpha=0.7, zorder=4, label='Margini rialzati')

            # Right flange
            right_mask = (x_coords_proj >= x_right_threshold) & (y_coords_proj >= y_top_threshold)
            right_flange = projected[right_mask]
            if len(right_flange) > 0:
                # Sort by Y coordinate for continuous line
                right_sorted = right_flange[np.argsort(right_flange[:, 1])]
                ax.plot(right_sorted[:, 0], right_sorted[:, 1],
                       'g-', linewidth=2.5, alpha=0.7, zorder=4)

        # Highlight socket (incavo) if present - REMOVED scatter, using only outline
        # User requested: white interior, only black border
        # Socket will be indicated by annotations only

        # Add measurement annotations (like in reference image)
        self._add_prospetto_annotations(ax, vertices_normalized)

        # Use 'box' adjustable to respect axis limits while maintaining equal aspect
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('Larghezza (mm)', fontsize=9)
        ax.set_ylabel('Lunghezza (mm)', fontsize=9)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)

        # Match tick style with other views for consistency
        ax.tick_params(axis='both', which='major', labelsize=8,
                      direction='out', length=4, width=1, color='black')
        ax.minorticks_on()
        ax.tick_params(axis='both', which='minor', direction='out',
                      length=2, width=0.5, color='gray')

        # ISSUE 5: Add 1mm tick marks on X and Y axes
        x_min_proj, x_max_proj = projected[:, 0].min(), projected[:, 0].max()
        y_min_proj, y_max_proj = projected[:, 1].min(), projected[:, 1].max()

        # TASK 1: Set origin at (0, 0)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

        # Return prospetto width, butt width AND length for profilo alignment
        prospetto_width = vertices_normalized[:, 0].max() - vertices_normalized[:, 0].min()
        prospetto_length = vertices_normalized[:, 1].max() - vertices_normalized[:, 1].min()

        # Calculate butt width at 80% position along Y axis
        y_coords_norm = vertices_normalized[:, 1]
        y_min_norm, y_max_norm = y_coords_norm.min(), y_coords_norm.max()
        butt_y_position = y_min_norm + 0.8 * (y_max_norm - y_min_norm)

        # Find vertices near butt position (within 5% tolerance)
        y_tolerance = (y_max_norm - y_min_norm) * 0.05
        butt_mask = np.abs(y_coords_norm - butt_y_position) < y_tolerance
        if np.any(butt_mask):
            butt_vertices = vertices_normalized[butt_mask]
            butt_width = butt_vertices[:, 0].max() - butt_vertices[:, 0].min()
        else:
            # Fallback: use full width
            butt_width = prospetto_width

        print(f"\n  === PROSPETTO DIMENSIONS DEBUG ===")
        print(f"    Prospetto width: {prospetto_width:.2f} mm")
        print(f"    Prospetto length: {prospetto_length:.2f} mm")
        print(f"    Butt width at 80% Y: {butt_width:.2f} mm")
        print(f"    Width ratio: {butt_width/prospetto_width:.2f}")
        print(f"  === END DEBUG ===\n")

        return prospetto_width, butt_width, prospetto_length

    def _render_butt_view(self, ax):
        """Render butt view (from above looking down at butt) - XZ projection.
        Uses REAL mesh data."""
        vertices = self.mesh.vertices

        # Project to XZ plane (width x thickness)
        projected = vertices[:, [0, 2]]

        # Subsample and sort by angle
        n_points = len(projected)
        if n_points > 15000:
            indices = np.random.choice(n_points, 15000, replace=False)
            projected = projected[indices]

        center = projected.mean(axis=0)
        angles = np.arctan2(projected[:, 1] - center[1], projected[:, 0] - center[0])
        sorted_idx = np.argsort(angles)
        outline = projected[sorted_idx]

        # Draw continuous outline
        outline_closed = np.vstack([outline, outline[0]])
        ax.plot(outline_closed[:, 0], outline_closed[:, 1],
               'k-', linewidth=1.5, zorder=2)

        ax.set_aspect('equal')
        ax.set_xlabel('Larghezza (mm)', fontsize=8)
        ax.set_ylabel('Spessore (mm)', fontsize=8)
        ax.grid(True, alpha=0.2)

    def _render_frontal_section(self, ax):
        """Render frontal section (central transverse cross-section).
        Uses REAL mesh slicing."""
        from .render_helpers import extract_cross_section

        vertices = self.mesh.vertices
        # Extract section at 50% along Y axis (longitudinal middle)
        section_2d = extract_cross_section(vertices, axis=1, position=0.5, tolerance=0.02)

        if len(section_2d) > 0:
            # Sort by angle to create outline
            center = section_2d.mean(axis=0)
            angles = np.arctan2(section_2d[:, 1] - center[1], section_2d[:, 0] - center[0])
            sorted_idx = np.argsort(angles)
            outline = section_2d[sorted_idx]

            # Draw continuous outline
            outline_closed = np.vstack([outline, outline[0]])
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=1.5, zorder=2)

        ax.set_aspect('equal')
        ax.set_xlabel('Larghezza (mm)', fontsize=8)
        ax.set_ylabel('Spessore (mm)', fontsize=8)
        ax.grid(True, alpha=0.2)

    def _render_transverse_section(self, ax, position, label):
        """Render transverse cross-section at specified position along Y axis.
        Uses REAL mesh slicing."""
        from .render_helpers import extract_cross_section

        vertices = self.mesh.vertices
        # Extract section at specified position along Y axis
        section_2d = extract_cross_section(vertices, axis=1, position=position, tolerance=0.02)

        if len(section_2d) > 0:
            # Sort by angle to create outline
            center = section_2d.mean(axis=0)
            angles = np.arctan2(section_2d[:, 1] - center[1], section_2d[:, 0] - center[0])
            sorted_idx = np.argsort(angles)
            outline = section_2d[sorted_idx]

            # Draw continuous outline
            outline_closed = np.vstack([outline, outline[0]])
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=1.5, zorder=2, label=label)

        ax.set_aspect('equal')
        ax.set_xlabel('Larghezza (mm)', fontsize=8)
        ax.set_ylabel('Spessore (mm)', fontsize=8)
        ax.grid(True, alpha=0.2)

    def _add_section_indicators(self, ax):
        """Add arrows/lines on longitudinal profile indicating where sections are taken."""
        # Get Y range for positioning arrows
        y_coords = self.mesh.vertices[:, 1]
        y_min, y_max = y_coords.min(), y_coords.max()

        # Section position (CORRECTED: 80%=tallone)
        butt_pos = y_min + 0.8 * (y_max - y_min)   # Tallone (butt) at 80%

        # Draw horizontal dashed line at section position
        ax.axhline(y=butt_pos, color='blue', linestyle='--', linewidth=1, alpha=0.6, label='Sezione Tallone (80%)')
        ax.legend(fontsize=7, loc='upper right')

    def _render_sezione(self, ax, position, global_dims=None, prospetto_width=None):
        """Render SEZIONE (transverse cross-section) at specified Y position.
        Enhanced to show incavo (socket), margini rialzati (flanges), and tagliente thickness.

        Args:
            ax: Matplotlib axis to render on
            position: Position along Y axis (0.0 to 1.0)
            global_dims: Tuple of (max_width, max_length, max_thickness) for uniform scaling
            prospetto_width: Width of prospetto for alignment (optional)
        """
        from .render_helpers import extract_cross_section

        vertices = self.mesh.vertices
        section_2d = extract_cross_section(vertices, axis=1, position=position, tolerance=0.02)

        if len(section_2d) > 0:
            # TASK 3: Normalize to origin (0, 0)
            print(f"\n  === DEBUG: Before normalization (position={position:.2f}) ===")
            print(f"    X range: [{section_2d[:, 0].min():.2f}, {section_2d[:, 0].max():.2f}]")
            print(f"    Z range: [{section_2d[:, 1].min():.2f}, {section_2d[:, 1].max():.2f}]")

            x_min = section_2d[:, 0].min()
            z_min = section_2d[:, 1].min()
            section_2d[:, 0] -= x_min
            section_2d[:, 1] -= z_min

            print(f"  === DEBUG: After normalization ===")
            print(f"    X range: [{section_2d[:, 0].min():.2f}, {section_2d[:, 0].max():.2f}]")
            print(f"    Z range: [{section_2d[:, 1].min():.2f}, {section_2d[:, 1].max():.2f}]")
            print(f"  === END DEBUG ===\n")

            center = section_2d.mean(axis=0)
            angles = np.arctan2(section_2d[:, 1] - center[1], section_2d[:, 0] - center[0])
            sorted_idx = np.argsort(angles)
            outline = section_2d[sorted_idx]

            # Draw main outline
            outline_closed = np.vstack([outline, outline[0]])
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=1.5, zorder=2)

            # TASK 3: Highlight features based on position
            x_coords = section_2d[:, 0]
            z_coords = section_2d[:, 1]
            x_max = x_coords.max()
            z_max = z_coords.max()

            # For tallone section (80% - butt end)
            if position >= 0.75:
                # Highlight incavo (socket) if present - top region
                if self.features.get('incavo_presente', False):
                    socket_threshold = np.percentile(z_coords, 70)  # Top 30%
                    socket_mask = z_coords >= socket_threshold
                    socket_points = section_2d[socket_mask]
                    if len(socket_points) > 0:
                        ax.scatter(socket_points[:, 0], socket_points[:, 1],
                                 c='red', s=8, alpha=0.7, zorder=3, label='Incavo')

                # Highlight margini rialzati (flanges) - edges with thicker lines
                if self.features.get('margini_rialzati_presenti', False):
                    # Left edge (flange)
                    left_mask = x_coords <= np.percentile(x_coords, 15)
                    left_points = section_2d[left_mask]
                    if len(left_points) > 0:
                        left_sorted = left_points[np.argsort(left_points[:, 1])]
                        ax.plot(left_sorted[:, 0], left_sorted[:, 1],
                               'g-', linewidth=2.5, alpha=0.7, zorder=4, label='Margini')

                    # Right edge (flange)
                    right_mask = x_coords >= np.percentile(x_coords, 85)
                    right_points = section_2d[right_mask]
                    if len(right_points) > 0:
                        right_sorted = right_points[np.argsort(right_points[:, 1])]
                        ax.plot(right_sorted[:, 0], right_sorted[:, 1],
                               'g-', linewidth=2.5, alpha=0.7, zorder=4)

            # For tagliente section (20% - blade end)
            elif position <= 0.25:
                # Highlight blade thickness - should be thinner, emphasize with hatching
                ax.fill(outline_closed[:, 0], outline_closed[:, 1],
                       color='brown', alpha=0.1, hatch='///', zorder=1, label='Tagliente')

                # Show cutting edge (bottom/thinnest point)
                z_min_idx = np.argmin(z_coords)
                ax.plot(x_coords[z_min_idx], z_coords[z_min_idx],
                       'ro', markersize=4, zorder=5, label='Filo tagliente')

            if position >= 0.75 or position <= 0.25:
                ax.legend(fontsize=6, loc='best')

        ax.set_aspect('equal')
        ax.set_xlabel('Larghezza (mm)', fontsize=8)
        ax.set_ylabel('Spessore (mm)', fontsize=8)
        ax.grid(True, alpha=0.15)

        # CRITICAL FIX: Scale section PROPORTIONALLY to match prospetto width
        if prospetto_width is not None and len(section_2d) > 0:
            # Calculate natural section width
            section_width = section_2d[:, 0].max() - section_2d[:, 0].min()

            # Calculate scale factor to match prospetto width
            if section_width > 0:
                scale_factor = prospetto_width / section_width

                # DEBUG: Print scaling information
                print(f"\n  === SECTION SCALING DEBUG (position={position:.2f}) ===")
                print(f"    Original section width: {section_width:.2f} mm")
                print(f"    Prospetto width: {prospetto_width:.2f} mm")
                print(f"    Scale factor: {scale_factor:.4f}")

                # Re-plot with scaled data
                ax.clear()

                # Scale BOTH X and Z coordinates by same factor to maintain aspect ratio
                # Since section_2d is already normalized to (0,0), scaling preserves this:
                # 0 * scale_factor = 0, so minimum stays at 0
                section_2d_scaled = section_2d * scale_factor

                # DEBUG: Verify scaled width matches prospetto and min is still 0
                scaled_width = section_2d_scaled[:, 0].max() - section_2d_scaled[:, 0].min()
                print(f"    Scaled section width: {scaled_width:.2f} mm")
                print(f"    Scaled X range: [{section_2d_scaled[:, 0].min():.4f}, {section_2d_scaled[:, 0].max():.2f}]")
                print(f"    Scaled Z range: [{section_2d_scaled[:, 1].min():.4f}, {section_2d_scaled[:, 1].max():.2f}]")
                if abs(scaled_width - prospetto_width) > 0.1:
                    print(f"    ⚠️  WARNING: Scaled width doesn't match prospetto width!")
                else:
                    print(f"    ✓  Success: Scaled width matches prospetto")
                print(f"  === END SECTION SCALING DEBUG ===\n")

                # Recalculate outline with scaled data
                center = section_2d_scaled.mean(axis=0)
                angles = np.arctan2(section_2d_scaled[:, 1] - center[1], section_2d_scaled[:, 0] - center[0])
                sorted_idx = np.argsort(angles)
                outline_scaled = section_2d_scaled[sorted_idx]

                # FORCE white background
                ax.set_facecolor('white')

                # Draw all section points in light gray to show WHITE interior
                # Same approach as prospetto - preserves concavities
                ax.scatter(section_2d_scaled[:, 0], section_2d_scaled[:, 1],
                          c='lightgray', s=0.3, alpha=0.3, zorder=1, edgecolors='none')

                # Draw ONLY the border outline - NO FILL
                outline_closed = np.vstack([outline_scaled, outline_scaled[0]])
                ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                       'k-', linewidth=1.5, zorder=2)

                # For tagliente section (20% - blade end) - REMOVED: only using tallone now
                # elif position <= 0.25:
                #     # Highlight blade thickness
                #     ax.fill(outline_closed[:, 0], outline_closed[:, 1],
                #            color='brown', alpha=0.1, hatch='///', zorder=1)
                #
                #     # Show cutting edge - find minimum thickness in CENTRAL region (not at extremities)
                #     x_min, x_max = x_coords.min(), x_coords.max()
                #     x_range = x_max - x_min
                #     x_center_min = x_min + 0.2 * x_range  # exclude outer 20% on left
                #     x_center_max = x_max - 0.2 * x_range  # exclude outer 20% on right
                #
                #     # Filter for central region only
                #     center_mask = (x_coords >= x_center_min) & (x_coords <= x_center_max)
                #     center_indices = np.where(center_mask)[0]
                #
                #     if len(center_indices) > 0:
                #         # Find minimum z (blade edge) within central region
                #         center_z_coords = z_coords[center_indices]
                #         min_z_local_idx = np.argmin(center_z_coords)
                #         z_min_idx = center_indices[min_z_local_idx]
                #
                #         ax.plot(x_coords[z_min_idx], z_coords[z_min_idx],
                #                'ro', markersize=4, zorder=5)

                # NO LEGEND - user requested removal

                # CRITICAL: Set x-limit to match prospetto width
                # This ensures sections have same width as prospetto for visual alignment
                ax.set_xlim(0, prospetto_width)
                y_max_scaled = section_2d_scaled[:, 1].max() * 1.05
                ax.set_ylim(0, y_max_scaled)

                # Set labels and grid AFTER limits to ensure proper display
                ax.set_xlabel('Larghezza (mm)', fontsize=9)
                ax.set_ylabel('Spessore (mm)', fontsize=9)
                ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

                # Ensure axes are visible with proper ticks
                ax.tick_params(axis='both', which='major', labelsize=8,
                              direction='out', length=4, width=1, color='black')

                # Enable minor ticks for better scale visibility
                ax.minorticks_on()
                ax.tick_params(axis='both', which='minor', direction='out',
                              length=2, width=0.5, color='gray')

                # Use equal aspect like prospetto for consistent appearance
                # Use 'box' adjustable to respect xlim constraints
                ax.set_aspect('equal', adjustable='box')
        else:
            # TASK 3: Set origin at (0, 0)
            ax.set_xlim(left=0)
            ax.set_ylim(bottom=0)

    def _render_profilo_longitudinale(self, ax, global_dims=None, prospetto_length=None):
        """Render PROFILO LONGITUDINALE (lateral side view - VERTICAL orientation).
        This is the SIDE VIEW showing thickness profile in VERTICAL orientation.
        ROTATED 90 degrees: X-axis = thickness (horizontal), Y-axis = length (vertical).

        Args:
            ax: Matplotlib axis to render on
            global_dims: Tuple of (max_width, max_length, max_thickness) for uniform scaling
            prospetto_length: Length of prospetto to match Y-axis limit (optional)
        """
        vertices = self.mesh.vertices

        # Project to YZ plane (lateral side view)
        # Y = length, Z = thickness
        projected = vertices[:, [1, 2]]  # YZ

        # Normalize to origin (0, 0)
        y_min, z_min = projected[:, 0].min(), projected[:, 1].min()
        projected[:, 0] -= y_min
        projected[:, 1] -= z_min

        # SWAP AXES FOR VERTICAL ORIENTATION: thickness on X, length on Y
        # Original: projected[:, 0] = length, projected[:, 1] = thickness
        # Swapped: projected[:, 0] = thickness, projected[:, 1] = length
        projected_vertical = np.column_stack([projected[:, 1], projected[:, 0]])

        # Get extreme points for front (min X) and back (max X) profiles
        y_unique = np.unique(projected_vertical[:, 1].round(decimals=1))
        front_profile = []  # Min X (thickness) for each Y (length)
        back_profile = []   # Max X (thickness) for each Y (length)

        for y_val in y_unique:
            mask = np.abs(projected_vertical[:, 1] - y_val) < 0.5
            x_vals = projected_vertical[mask, 0]
            if len(x_vals) > 0:
                front_profile.append([x_vals.min(), y_val])
                back_profile.append([x_vals.max(), y_val])

        front_profile = np.array(front_profile)
        back_profile = np.array(back_profile)

        # Plot profiles (now vertical) - NO LEGEND to avoid overlap
        if len(front_profile) > 0:
            ax.plot(front_profile[:, 0], front_profile[:, 1],
                   'k-', linewidth=1.5, zorder=2)
        if len(back_profile) > 0:
            ax.plot(back_profile[:, 0], back_profile[:, 1],
                   'k-', linewidth=1.5, zorder=2)

        # Add spessore massimo annotation OUTSIDE the drawing area
        x_max_val = projected_vertical[:, 0].max()
        y_max = projected_vertical[:, 1].max()

        # Find max thickness position
        max_thickness_idx = np.argmax(projected_vertical[:, 0])
        y_at_max = projected_vertical[max_thickness_idx, 1]

        # Draw reference line for max thickness (horizontal in vertical view)
        ax.plot([0, x_max_val], [y_at_max, y_at_max],
               'b--', linewidth=0.8, alpha=0.5, zorder=1)

        # Annotation positioned OUTSIDE to the RIGHT of the drawing
        # Use x position beyond the max thickness
        x_annotation_pos = x_max_val + 0.5  # Just outside the drawing
        ax.text(x_annotation_pos, y_at_max, f'← spess. max\n{x_max_val:.1f}mm',
               ha='left', fontsize=7, color='blue', va='center',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7, pad=0.3))

        # Set origin at (0,0) and MATCH prospetto dimensions for symmetry
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

        # CRITICAL: Match profilo length to prospetto length for symmetry
        if prospetto_length is not None:
            ax.set_ylim(top=prospetto_length)
            print(f"\n  === PROFILO SYMMETRY DEBUG ===")
            print(f"    Profilo natural length: {projected_vertical[:, 1].max():.2f} mm")
            print(f"    Profilo natural thickness: {projected_vertical[:, 0].max():.2f} mm")
            print(f"    Prospetto length (target): {prospetto_length:.2f} mm")
            print(f"    ✓ Profilo Y-axis limited to match prospetto")
            print(f"  === END DEBUG ===\n")

        # Use equal aspect to match prospetto style - ensures same visual proportions
        # Use 'box' adjustable to respect axis limits
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('Spessore (mm)', fontsize=9)
        ax.set_ylabel('Lunghezza (mm)', fontsize=9)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Match tick style with prospetto for consistency
        ax.tick_params(axis='both', which='major', labelsize=8,
                      direction='out', length=4, width=1, color='black')
        ax.minorticks_on()
        ax.tick_params(axis='both', which='minor', direction='out',
                      length=2, width=0.5, color='gray')

    def _add_prospetto_annotations(self, ax, vertices):
        """Add ESSENTIAL measurement annotations to prospetto using dashed lines.
        Uses dashed lines for clear visual connection, with all key measurements."""

        f = self.features
        y_coords = vertices[:, 1]
        x_coords = vertices[:, 0]
        z_coords = vertices[:, 2]

        y_min, y_max = y_coords.min(), y_coords.max()
        x_min, x_max = x_coords.min(), x_coords.max()

        # Divide artifact into regions
        y_range = y_max - y_min
        tallone_region = y_max - 0.2 * y_range  # Top 20%
        tagliente_region = y_min + 0.2 * y_range  # Bottom 20%
        middle_region = (y_max + y_min) / 2  # Middle

        # RIGHT SIDE MEASUREMENTS - Stack vertically with equal spacing
        right_measurements = []

        # Collect all right-side measurements
        if 'tallone_larghezza' in f:
            right_measurements.append(('Tallone largh.', f["tallone_larghezza"], y_max - 0.05 * y_range, 'black'))

        if 'tallone_spessore' in f:
            right_measurements.append(('Tallone spess.', f["tallone_spessore"], y_max - 0.08 * y_range, 'black'))

        z_min, z_max = z_coords.min(), z_coords.max()
        spessore_max = z_max - z_min
        max_thickness_mask = np.abs(z_coords - z_max) < 1.0
        if np.any(max_thickness_mask):
            y_at_max_thickness = y_coords[max_thickness_mask].mean()
            right_measurements.append(('Spessore max', spessore_max, y_at_max_thickness, 'blue'))

        if 'larghezza_minima' in f:
            right_measurements.append(('Largh. minima', f["larghezza_minima"], middle_region, 'purple'))

        # Space right-side measurements evenly - COMPLETELY OUTSIDE bbox
        text_x_right = x_max + 35  # FAR outside to ensure completely outside bbox
        if len(right_measurements) > 0:
            # Calculate vertical spacing to avoid overlap
            spacing = max(15, y_range / (len(right_measurements) + 1))
            for idx, (label, value, measurement_y, color) in enumerate(right_measurements):
                # Position text with consistent vertical spacing from top
                text_y = y_max - (idx + 1) * spacing

                # Draw horizontal dashed line from edge to measurement point
                ax.plot([x_max, x_max + 10], [measurement_y, measurement_y],
                       linestyle='--', color=color, linewidth=0.8, alpha=0.7)

                # Add text label
                ax.text(text_x_right, text_y, f'{label}: {value:.1f}mm',
                       fontsize=7, ha='left', va='center', color=color)

                # Connect text to measurement line if they're at different heights
                if abs(text_y - measurement_y) > 2:
                    ax.plot([x_max + 10, text_x_right - 2], [measurement_y, text_y],
                           linestyle='--', color=color, linewidth=0.5, alpha=0.5)

        # LEFT SIDE MEASUREMENTS - Socket measurements (COMPLETELY away from Y-axis labels)
        if f.get('incavo_presente', False):
            text_x_left = x_min - 60  # Position FAR away from Y-axis and bbox

            # Socket width
            if 'incavo_larghezza' in f:
                measurement_y = y_max - 0.13 * y_range
                # Draw horizontal dashed line
                ax.plot([x_min - 10, x_min], [measurement_y, measurement_y],
                       linestyle='--', color='red', linewidth=0.8, alpha=0.7)
                # Add text label
                ax.text(text_x_left, measurement_y, f'Incavo largh.: {f["incavo_larghezza"]:.1f}mm',
                       fontsize=7, ha='right', va='center', color='red')

            # Socket depth
            if 'incavo_profondita' in f and f['incavo_profondita'] > 2.0:
                measurement_y = y_max - 0.09 * y_range
                # Draw horizontal dashed line
                ax.plot([x_min - 10, x_min], [measurement_y, measurement_y],
                       linestyle='--', color='red', linewidth=0.8, alpha=0.7)
                # Add text label
                ax.text(text_x_left, measurement_y, f'Incavo prof.: {f["incavo_profondita"]:.1f}mm',
                       fontsize=7, ha='right', va='center', color='red')

            # Socket HEIGHT (new measurement)
            if 'incavo_altezza' in f and f['incavo_altezza'] > 0:
                measurement_y = y_max - 0.05 * y_range
                # Draw horizontal dashed line
                ax.plot([x_min - 10, x_min], [measurement_y, measurement_y],
                       linestyle='--', color='red', linewidth=0.8, alpha=0.7)
                # Add text label
                ax.text(text_x_left, measurement_y, f'Incavo alt.: {f["incavo_altezza"]:.1f}mm',
                       fontsize=7, ha='right', va='center', color='red')

        # BLADE MEASUREMENTS (bottom) - With arc and chord
        blade_measurements_y = []

        # 1. Tagliente larghezza (blade width) - horizontal dashed line at WIDEST PART of blade
        if 'tagliente_larghezza' in f:
            # Find the Y position where blade is widest in tagliente region
            blade_mask = y_coords <= tagliente_region
            if np.any(blade_mask):
                blade_y_coords = y_coords[blade_mask]
                blade_x_coords = x_coords[blade_mask]

                # Group by Y coordinate (bin into 20 bins) and find width at each Y level
                y_unique = np.linspace(blade_y_coords.min(), blade_y_coords.max(), 20)
                widths = []
                y_positions = []

                for y_val in y_unique:
                    y_tolerance = y_range * 0.02
                    mask = np.abs(blade_y_coords - y_val) < y_tolerance
                    if np.any(mask):
                        x_at_y = blade_x_coords[mask]
                        width_at_y = x_at_y.max() - x_at_y.min()
                        widths.append(width_at_y)
                        y_positions.append(y_val)

                # Find Y where width is maximum
                if len(widths) > 0:
                    max_width_idx = np.argmax(widths)
                    measurement_y = y_positions[max_width_idx]

                    # Get X range at this Y position
                    y_tolerance = y_range * 0.02
                    mask = np.abs(y_coords - measurement_y) < y_tolerance
                    blade_x_min = x_coords[mask].min()
                    blade_x_max = x_coords[mask].max()

                    # Draw horizontal dashed line across the blade width at widest part
                    ax.plot([blade_x_min, blade_x_max], [measurement_y, measurement_y],
                           linestyle='--', color='brown', linewidth=0.8, alpha=0.7)

                    # Add text label OUTSIDE bbox (below)
                    text_y = measurement_y - 12
                    ax.text((blade_x_min + blade_x_max) / 2, text_y,
                           f'Tagliente largh.: {f["tagliente_larghezza"]:.1f}mm',
                           fontsize=7, ha='center', va='top', color='brown')

        # 2. Arc measurement (arco) - if available
        if 'tagliente_arco' in f:
            measurement_y = y_min + 0.02 * y_range
            blade_measurements_y.append(measurement_y)

            # Draw dashed arc line following the blade curve
            blade_mask = y_coords <= tagliente_region
            blade_points = np.column_stack([x_coords[blade_mask], y_coords[blade_mask]])
            if len(blade_points) > 0:
                # Sort by x coordinate for continuous arc
                sorted_idx = np.argsort(blade_points[:, 0])
                blade_arc = blade_points[sorted_idx]
                # Find points at the blade edge (minimum y in blade region)
                edge_points = blade_arc[blade_arc[:, 1] <= np.percentile(blade_arc[:, 1], 10)]
                if len(edge_points) > 1:
                    ax.plot(edge_points[:, 0], edge_points[:, 1],
                           linestyle='--', color='darkgreen', linewidth=0.8, alpha=0.7)

            # Add text label
            text_y = measurement_y - 15
            ax.text(x_min + (x_max - x_min) / 2, text_y,
                   f'Arco: {f["tagliente_arco"]:.1f}mm',
                   fontsize=7, ha='center', va='top', color='darkgreen')

        # 3. Chord measurement (corda) - straight line from edge to edge
        if 'tagliente_corda' in f:
            measurement_y = y_min + 0.02 * y_range

            # Draw straight dashed line from edge to edge (chord)
            blade_mask = y_coords <= tagliente_region
            if np.any(blade_mask):
                blade_x_coords = x_coords[blade_mask]
                chord_y = y_coords[blade_mask].min()
                ax.plot([blade_x_coords.min(), blade_x_coords.max()], [chord_y, chord_y],
                       linestyle='--', color='darkblue', linewidth=0.8, alpha=0.7)

                # Add text label
                text_y = chord_y - 22
                ax.text(x_min + (x_max - x_min) / 2, text_y,
                       f'Corda: {f["tagliente_corda"]:.1f}mm',
                       fontsize=7, ha='center', va='top', color='darkblue')

        # MINIMUM WIDTH POSITION - Horizontal dashed line at narrowest point
        if 'larghezza_minima' in f:
            # Find the Y position of minimum width (middle region)
            min_width_y = middle_region

            # Find X extent at minimum width position
            y_tolerance = y_range * 0.05
            mask = np.abs(y_coords - min_width_y) < y_tolerance
            if np.any(mask):
                min_x_coords = x_coords[mask]
                min_x_min, min_x_max = min_x_coords.min(), min_x_coords.max()

                # Draw horizontal dashed line at minimum width
                ax.plot([min_x_min, min_x_max], [min_width_y, min_width_y],
                       linestyle='--', color='purple', linewidth=0.8, alpha=0.6)

        # BUTT WIDTH - Horizontal dashed line at tallone region
        if 'tallone_larghezza' in f:
            # Position at 90% (near top, tallone region)
            butt_y = y_max - 0.05 * y_range

            # Find X extent at butt position
            y_tolerance = y_range * 0.05
            mask = np.abs(y_coords - butt_y) < y_tolerance
            if np.any(mask):
                butt_x_coords = x_coords[mask]
                butt_x_min, butt_x_max = butt_x_coords.min(), butt_x_coords.max()

                # Draw horizontal dashed line at butt width
                ax.plot([butt_x_min, butt_x_max], [butt_y, butt_y],
                       linestyle='--', color='black', linewidth=0.8, alpha=0.6)

    def _create_ai_interpretation_page(self, pdf):
        """Create AI interpretation page."""
        fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        ax = fig.add_subplot(111)
        ax.axis('off')

        ai_text = self._generate_ai_interpretation()

        ax.text(0.5, 0.9, self.t('ai_interpretation'),
               ha='center', fontsize=16, fontweight='bold')

        ax.text(0.1, 0.7, ai_text, ha='left', va='top', fontsize=10, wrap=True)

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _generate_ai_interpretation(self) -> str:
        """Generate AI interpretation text using real AI assistant."""
        try:
            # Try to import and use real AI assistant
            from acs.core.ai_assistant import get_ai_assistant

            ai = get_ai_assistant()

            if ai is not None:
                # Build features dict with Savignano data
                features_dict = {
                    'savignano': self.features,
                    **self.features  # Include all features at top level too
                }

                # FORCE ITALIAN: Prepend explicit Italian instruction to context
                italian_instruction = "IMPORTANTE: Rispondi SOLO in italiano. Non usare inglese. Tutta la tua analisi deve essere scritta in italiano.\n\n"

                # Call AI analysis with Italian context
                if self.language == 'it':
                    context = italian_instruction + f"Questa è un'ascia ad incavo dell'Età del Bronzo dalla collezione archeologica di Savignano. Matrice: {self.features.get('matrix_id', 'Sconosciuta')}"
                else:
                    context = f"This is a Bronze Age socketed axe from the Savignano archaeological collection. Matrix: {self.features.get('matrix_id', 'Unknown')}"

                # Call AI analysis (language is handled via context instruction)
                result = ai.analyze_artifact(
                    artifact_id=self.artifact_id,
                    features=features_dict,
                    context=context
                    # NOTE: language parameter NOT supported - use context instructions instead
                )

                if 'analysis' in result and result['analysis']:
                    # Parse JSON response if present
                    import re
                    import json

                    # Try to extract JSON from response
                    json_match = re.search(r'```json\s*(.*?)\s*```', result['analysis'], re.DOTALL)
                    if json_match:
                        try:
                            ai_json = json.loads(json_match.group(1))

                            # TASK 4: Format structured response WITHOUT markdown
                            interpretation = f"Artefatto: {self.artifact_id}\n\n"

                            if 'morphometric_assessment' in ai_json:
                                interpretation += f"Analisi Morfometrica:\n{ai_json['morphometric_assessment']}\n\n"

                            if 'suggested_class' in ai_json:
                                interpretation += f"Classificazione: {ai_json['suggested_class']}\n"
                                if 'subtype' in ai_json:
                                    interpretation += f"Sottotipo: {ai_json['subtype']}\n"
                                if 'confidence' in ai_json:
                                    interpretation += f"Confidenza: {ai_json['confidence']}\n\n"

                            if 'reasoning' in ai_json:
                                interpretation += f"Motivazione:\n{ai_json['reasoning']}\n\n"

                            if 'archaeological_notes' in ai_json:
                                interpretation += f"Note Archeologiche:\n{ai_json['archaeological_notes']}\n\n"

                            return interpretation

                        except json.JSONDecodeError:
                            # Fall back to raw text with markdown removed
                            text = result['analysis']
                            # TASK 4: Remove markdown formatting
                            text = text.replace('**', '')  # Remove bold markers
                            text = text.replace('*', '')   # Remove italic markers
                            text = text.replace('###', '') # Remove heading markers
                            text = text.replace('##', '')
                            text = text.replace('#', '')
                            return text
                    else:
                        # Use raw analysis text with markdown removed
                        text = result['analysis']
                        # TASK 4: Remove markdown formatting
                        text = text.replace('**', '')
                        text = text.replace('*', '')
                        text = text.replace('###', '')
                        text = text.replace('##', '')
                        text = text.replace('#', '')
                        return text

                elif 'error' in result:
                    return f"Errore Analisi AI: {result['error']}\n\n[Utilizzo interpretazione di fallback]"

            # Fallback if AI not available
            raise Exception("AI assistant not initialized")

        except Exception as e:
            # TASK 4: Fallback interpretation if AI fails - NO MARKDOWN
            f = self.features

            interpretation = f"Artefatto: {self.artifact_id}\n\n"
            interpretation += f"Nota: Analisi AI non disponibile ({str(e)}). Utilizzo interpretazione di base.\n\n"

            if 'matrix_id' in f:
                interpretation += f"Classificazione: {f['matrix_id']}\n\n"

            if f.get('incavo_presente', False):
                interpretation += "Analisi Incavo: Presente - indica meccanismo di immanicatura per attacco del manico.\n"
                if 'incavo_larghezza' in f:
                    interpretation += f"Larghezza: {f['incavo_larghezza']:.1f}mm\n"
                if 'incavo_profondita' in f:
                    interpretation += f"Profondita: {f['incavo_profondita']:.1f}mm\n"
                interpretation += "\n"

            if f.get('margini_rialzati_presenti', False):
                interpretation += "Margini Rialzati: Presenti - caratteristica morfologica delle asce tipo Savignano.\n"
                if 'margini_rialzati_lunghezza' in f:
                    interpretation += f"Lunghezza: {f['margini_rialzati_lunghezza']:.1f}mm\n"
                interpretation += "\n"

            if 'tagliente_larghezza' in f:
                interpretation += f"Tagliente: Larghezza {f['tagliente_larghezza']:.1f}mm\n"
                if 'tagliente_forma' in f:
                    interpretation += f"Forma: {f['tagliente_forma']}\n"
                interpretation += "\n"

            interpretation += "Valutazione Tipologica: Ascia con incavo dell'Eta del Bronzo con margini rialzati, coerente con la tradizione Savignano. La presenza dell'incavo indica capacita di immanicatura.\n"

            return interpretation

    def _create_production_techniques_page(self, pdf):
        """Create production techniques analysis page - DEPRECATED.
        This method is kept for backward compatibility but is no longer used.
        Use _create_hammering_analysis_page() and _create_casting_analysis_page() instead.
        """
        fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        gs = gridspec.GridSpec(2, 1, hspace=0.3)

        # Title
        fig.suptitle(self.t('page_techniques'), fontsize=14, fontweight='bold')

        # Hammering analysis
        ax_hammer = fig.add_subplot(gs[0])
        ax_hammer.axis('off')
        ax_hammer.text(0.5, 0.9, self.t('hammering_analysis'),
                      ha='center', fontsize=12, fontweight='bold')
        hammer_text = self._analyze_hammering()
        ax_hammer.text(0.1, 0.5, hammer_text, ha='left', va='top', fontsize=9, wrap=True)

        # Casting analysis
        ax_cast = fig.add_subplot(gs[1])
        ax_cast.axis('off')
        ax_cast.text(0.5, 0.9, self.t('casting_analysis'),
                    ha='center', fontsize=12, fontweight='bold')
        casting_text = self._analyze_casting()
        ax_cast.text(0.1, 0.5, casting_text, ha='left', va='top', fontsize=9, wrap=True)

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _create_hammering_analysis_page(self, pdf):
        """Create dedicated Hammering Analysis page - multiple A4 pages if needed."""
        import textwrap

        hammer_text = self._analyze_hammering()

        # Split into lines with proper wrapping
        wrapped_lines = []
        for paragraph in hammer_text.split('\n'):
            if paragraph.strip():
                wrapped_lines.extend(textwrap.wrap(paragraph, width=95, break_long_words=False))
            else:
                wrapped_lines.append('')  # Preserve empty lines

        # Split into pages (max ~45 lines per page to avoid overflow)
        lines_per_page = 45
        total_pages = (len(wrapped_lines) + lines_per_page - 1) // lines_per_page

        for page_num in range(total_pages):
            fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
            ax = fig.add_subplot(111)
            ax.axis('off')

            # Title (only on first page)
            if page_num == 0:
                ax.text(0.5, 0.97, 'ANALISI MARTELLATURA',
                       ha='center', fontsize=14, fontweight='bold', color='#2C3E50')
                ax.text(0.5, 0.95, f'Artefatto: {self.artifact_id}',
                       ha='center', fontsize=10, style='italic', color='#34495E')
                ax.plot([0.05, 0.95], [0.93, 0.93], 'k-', linewidth=1, alpha=0.3)
                text_start_y = 0.91
            else:
                ax.text(0.5, 0.97, 'ANALISI MARTELLATURA (continua)',
                       ha='center', fontsize=12, fontweight='bold', color='#2C3E50')
                ax.plot([0.05, 0.95], [0.95, 0.95], 'k-', linewidth=1, alpha=0.3)
                text_start_y = 0.93

            # Get lines for this page
            start_idx = page_num * lines_per_page
            end_idx = min(start_idx + lines_per_page, len(wrapped_lines))
            page_lines = wrapped_lines[start_idx:end_idx]

            # Display text line by line
            current_y = text_start_y
            line_height = 0.018

            for line in page_lines:
                if line.strip():
                    ax.text(0.08, current_y, line, ha='left', va='top',
                           fontsize=9, family='monospace')
                current_y -= line_height

            # Footer with page number
            ax.text(0.5, 0.02, f'{self.artifact_id} | Pagina {4 + page_num}',
                   ha='center', va='bottom', fontsize=8, color='gray')

            pdf.savefig(fig)
            plt.close(fig)

    def _create_casting_analysis_page(self, pdf):
        """Create dedicated Casting Analysis page - multiple A4 pages if needed."""
        import textwrap

        casting_text = self._analyze_casting()

        # Split into lines with proper wrapping
        wrapped_lines = []
        for paragraph in casting_text.split('\n'):
            if paragraph.strip():
                wrapped_lines.extend(textwrap.wrap(paragraph, width=95, break_long_words=False))
            else:
                wrapped_lines.append('')  # Preserve empty lines

        # Split into pages (max ~45 lines per page to avoid overflow)
        lines_per_page = 45
        total_pages = (len(wrapped_lines) + lines_per_page - 1) // lines_per_page

        # Note: Page numbers continue from hammering analysis
        # Assuming hammering takes 1-2 pages, casting starts at page 5 or 6
        # We'll calculate dynamically based on actual page count

        for page_num in range(total_pages):
            fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
            ax = fig.add_subplot(111)
            ax.axis('off')

            # Title (only on first page)
            if page_num == 0:
                ax.text(0.5, 0.97, 'ANALISI FUSIONE',
                       ha='center', fontsize=14, fontweight='bold', color='#2C3E50')
                ax.text(0.5, 0.95, f'Artefatto: {self.artifact_id}',
                       ha='center', fontsize=10, style='italic', color='#34495E')
                ax.plot([0.05, 0.95], [0.93, 0.93], 'k-', linewidth=1, alpha=0.3)
                text_start_y = 0.91
            else:
                ax.text(0.5, 0.97, 'ANALISI FUSIONE (continua)',
                       ha='center', fontsize=12, fontweight='bold', color='#2C3E50')
                ax.plot([0.05, 0.95], [0.95, 0.95], 'k-', linewidth=1, alpha=0.3)
                text_start_y = 0.93

            # Get lines for this page
            start_idx = page_num * lines_per_page
            end_idx = min(start_idx + lines_per_page, len(wrapped_lines))
            page_lines = wrapped_lines[start_idx:end_idx]

            # Display text line by line
            current_y = text_start_y
            line_height = 0.018

            for line in page_lines:
                if line.strip():
                    ax.text(0.08, current_y, line, ha='left', va='top',
                           fontsize=9, family='monospace')
                current_y -= line_height

            # Footer with page number (will be adjusted in final numbering)
            # For now, just indicate it's a casting page
            ax.text(0.5, 0.02, f'{self.artifact_id} | Analisi Fusione - Pag. {page_num + 1}',
                   ha='center', va='bottom', fontsize=8, color='gray')

            pdf.savefig(fig)
            plt.close(fig)

    def _analyze_hammering(self) -> str:
        """Analyze hammering marks and cold-working evidence using real mesh data."""
        try:
            vertices = self.mesh.vertices

            # Calculate vertex normals if available, or use face normals
            if hasattr(self.mesh, 'vertex_normals'):
                normals = self.mesh.vertex_normals
            else:
                # Estimate surface roughness using vertex spacing
                normals = None

            # Divide mesh into regions: tallone (butt), corpo (body), tagliente (blade)
            y_coords = vertices[:, 1]
            y_min, y_max = y_coords.min(), y_coords.max()
            y_range = y_max - y_min

            tallone_mask = y_coords >= (y_max - 0.25 * y_range)
            tagliente_mask = y_coords <= (y_min + 0.25 * y_range)
            corpo_mask = ~(tallone_mask | tagliente_mask)

            analysis_text = "ANALISI MARTELLAMENTO (Cold-working)\n\n"

            # Calculate surface roughness proxy for each region
            if normals is not None:
                # Use normal variance as roughness indicator
                tallone_roughness = np.std(normals[tallone_mask], axis=0).mean()
                corpo_roughness = np.std(normals[corpo_mask], axis=0).mean()
                tagliente_roughness = np.std(normals[tagliente_mask], axis=0).mean()

                analysis_text += f"Rugosità superficiale (deviazione standard delle normali):\n"
                analysis_text += f"  - Tallone: σ = {tallone_roughness:.4f}\n"
                analysis_text += f"  - Corpo: σ = {corpo_roughness:.4f}\n"
                analysis_text += f"  - Tagliente: σ = {tagliente_roughness:.4f}\n\n"

                analysis_text += "SPIEGAZIONE METRICA (σ roughness):\n"
                analysis_text += "La deviazione standard (σ) delle normali superficiali misura\n"
                analysis_text += "quanto la superficie si discosta da un piano ideale.\n\n"
                analysis_text += "  σ < 0.02: superficie molto liscia (levigatura o fusione pulita)\n"
                analysis_text += "  σ = 0.02-0.05: rugosità moderata (martellatura leggera)\n"
                analysis_text += "  σ > 0.05: superficie irregolare (martellatura intensa)\n\n"

                # Interpret results
                if tagliente_roughness > corpo_roughness * 1.5:
                    analysis_text += "INTERPRETAZIONE: La rugosità elevata nella regione del tagliente\n"
                    analysis_text += f"(σ = {tagliente_roughness:.4f}) suggerisce lavorazione a freddo intensiva,\n"
                    analysis_text += "probabilmente per affilare e rinforzare il bordo dopo la fusione.\n"
                    analysis_text += "Questo processo, detto 'martellatura a freddo', aumenta la durezza\n"
                    analysis_text += "del bronzo per deformazione plastica (work hardening).\n\n"
                elif tallone_roughness > corpo_roughness * 1.3:
                    analysis_text += "INTERPRETAZIONE: La rugosità nel tallone indica possibile martellamento\n"
                    analysis_text += "post-fusione, tipico della rifinitura dell'incavo per l'immanicatura.\n"
                    analysis_text += "Le irregolarità superficiali miglioravano l'aderenza del manico.\n\n"
                else:
                    analysis_text += "INTERPRETAZIONE: La superficie mostra rugosità relativamente uniforme,\n"
                    analysis_text += "suggerendo lavorazione a freddo minima o ben levigata con abrasivi.\n"
                    analysis_text += "Indica buona finitura e possibile uso prolungato che ha levigato\n"
                    analysis_text += "le irregolarità iniziali.\n\n"
            else:
                # Alternative: use vertex density as proxy
                from scipy.spatial import distance

                # Sample 1000 points for performance
                sample_size = min(1000, len(vertices))
                tallone_sample = vertices[tallone_mask]
                if len(tallone_sample) > sample_size:
                    tallone_sample = tallone_sample[np.random.choice(len(tallone_sample), sample_size, replace=False)]

                corpo_sample = vertices[corpo_mask]
                if len(corpo_sample) > sample_size:
                    corpo_sample = corpo_sample[np.random.choice(len(corpo_sample), sample_size, replace=False)]

                tagliente_sample = vertices[tagliente_mask]
                if len(tagliente_sample) > sample_size:
                    tagliente_sample = tagliente_sample[np.random.choice(len(tagliente_sample), sample_size, replace=False)]

                # Calculate local density variance as roughness proxy
                def calc_local_roughness(verts):
                    if len(verts) < 10:
                        return 0.0
                    # Calculate variance in Z coordinates (thickness direction)
                    return np.std(verts[:, 2])

                tallone_roughness = calc_local_roughness(tallone_sample)
                corpo_roughness = calc_local_roughness(corpo_sample)
                tagliente_roughness = calc_local_roughness(tagliente_sample)

                analysis_text += f"Analisi geometrica della superficie (varianza spessore):\n"
                analysis_text += f"  - Tallone: σ = {tallone_roughness:.3f} mm\n"
                analysis_text += f"  - Corpo: σ = {corpo_roughness:.3f} mm\n"
                analysis_text += f"  - Tagliente: σ = {tagliente_roughness:.3f} mm\n\n"

                analysis_text += "Interpretazione: L'analisi della superficie indica "
                if tagliente_roughness > corpo_roughness * 1.5:
                    analysis_text += "evidenza di martellamento concentrato sul tagliente per aumentarne la durezza e l'affilatura. "
                elif tallone_roughness > 0.5:
                    analysis_text += "tracce di lavorazione a freddo nella regione del tallone, tipica della rifinitura post-fusione. "
                else:
                    analysis_text += "una finitura relativamente liscia, suggerendo rifinitura accurata o levigatura d'uso. "

                analysis_text += "La lavorazione a freddo era pratica comune nell'Età del Bronzo per migliorare le proprietà meccaniche.\n\n"

            # Add mesh quality info
            n_vertices = len(vertices)
            analysis_text += f"Dati mesh: {n_vertices} vertici analizzati.\n"

            return analysis_text

        except Exception as e:
            return f"Analisi martellamento: Errore nell'analisi della superficie ({str(e)})\n\n" + \
                   "Nota: L'analisi richiede dati mesh di qualità sufficiente per determinare " + \
                   "le caratteristiche di lavorazione a freddo."

    def _analyze_casting(self) -> str:
        """Analyze casting technique evidence using real mesh data."""
        try:
            vertices = self.mesh.vertices
            faces = self.mesh.faces if hasattr(self.mesh, 'faces') else None

            analysis_text = "ANALISI TECNICA DI FUSIONE\n\n"

            # 1. SYMMETRY ANALYSIS - good castings are typically symmetric
            x_coords = vertices[:, 0]
            x_mean = x_coords.mean()

            # Split mesh into left and right halves
            left_mask = x_coords <= x_mean
            right_mask = x_coords > x_mean

            left_verts = vertices[left_mask]
            right_verts = vertices[right_mask]

            # Mirror right side and compare
            right_mirrored = right_verts.copy()
            right_mirrored[:, 0] = 2 * x_mean - right_mirrored[:, 0]

            # Calculate approximate symmetry by comparing distributions
            left_y_dist = np.histogram(left_verts[:, 1], bins=20)[0]
            right_y_dist = np.histogram(right_mirrored[:, 1], bins=20)[0]

            # Normalize
            left_y_dist = left_y_dist / (left_y_dist.sum() + 1e-6)
            right_y_dist = right_y_dist / (right_y_dist.sum() + 1e-6)

            symmetry_score = 1.0 - np.abs(left_y_dist - right_y_dist).sum() / 2.0
            symmetry_percent = symmetry_score * 100

            analysis_text += f"1. ANALISI SIMMETRIA\n"
            analysis_text += f"   Simmetria bilaterale: {symmetry_percent:.1f}%\n\n"

            analysis_text += f"   SPIEGAZIONE METRICA:\n"
            analysis_text += f"   La simmetria è calcolata confrontando le distribuzioni geometriche\n"
            analysis_text += f"   della metà sinistra e destra dell'ascia (specchiate).\n"
            analysis_text += f"   100% = perfettamente simmetrica, 0% = completamente asimmetrica\n\n"

            if symmetry_percent >= 85:
                analysis_text += "   INTERPRETAZIONE: Elevata simmetria (>85%) indica uso di stampo\n"
                analysis_text += "   a due valve ben allineate, tecnica tipica della fusione a cera persa\n"
                analysis_text += "   o in stampi in pietra. L'artigiano aveva elevata competenza tecnica\n"
                analysis_text += "   e strumenti di precisione per allineare le valve.\n\n"
            elif symmetry_percent >= 70:
                analysis_text += "   INTERPRETAZIONE: Simmetria moderata (70-85%), coerente con fusione\n"
                analysis_text += "   in stampo bivalve con leggero disallineamento durante la chiusura\n"
                analysis_text += "   o ritocchi post-fusione asimmetrici per rimuovere difetti.\n\n"
            else:
                analysis_text += "   INTERPRETAZIONE: Asimmetria significativa (<70%) suggerisce possibile\n"
                analysis_text += "   stampo a perdere (monouso) o estesa lavorazione post-fusione che ha\n"
                analysis_text += "   alterato la simmetria originale. Potrebbe indicare riparazioni.\n\n"

            # 2. MESH QUALITY ANALYSIS - detect potential casting defects
            if faces is not None:
                n_faces = len(faces)
                n_vertices = len(vertices)
                vertex_face_ratio = n_faces / n_vertices

                analysis_text += f"2. QUALITÀ DEL MESH (Proxy per difetti di fusione)\n"
                analysis_text += f"   Vertici: {n_vertices}, Facce: {n_faces}\n"
                analysis_text += f"   Rapporto facce/vertici: {vertex_face_ratio:.2f}\n\n"

                # High ratio suggests irregular surface (possible porosity/defects)
                if vertex_face_ratio > 2.5:
                    analysis_text += "   Interpretazione: Superficie irregolare rilevata. Potrebbero indicare porosità "
                    analysis_text += "o inclusioni di gas durante la fusione, comuni quando la colata è troppo rapida.\n\n"
                else:
                    analysis_text += "   Interpretazione: Superficie relativamente regolare, indica buon controllo "
                    analysis_text += "della temperatura di fusione e lento raffreddamento.\n\n"

            # 3. THICKNESS VARIATION - casting should have relatively uniform thickness
            z_coords = vertices[:, 2]
            y_coords = vertices[:, 1]

            # Analyze thickness variation along length
            y_bins = np.linspace(y_coords.min(), y_coords.max(), 10)
            thickness_variations = []

            for i in range(len(y_bins) - 1):
                mask = (y_coords >= y_bins[i]) & (y_coords < y_bins[i+1])
                if np.any(mask):
                    z_section = z_coords[mask]
                    thickness = z_section.max() - z_section.min()
                    thickness_variations.append(thickness)

            if len(thickness_variations) > 0:
                thickness_std = np.std(thickness_variations)
                thickness_mean = np.mean(thickness_variations)
                thickness_cv = (thickness_std / thickness_mean) * 100 if thickness_mean > 0 else 0

                analysis_text += f"3. VARIAZIONE DELLO SPESSORE\n"
                analysis_text += f"   Spessore medio: {thickness_mean:.2f} mm\n"
                analysis_text += f"   Deviazione standard: {thickness_std:.2f} mm\n"
                analysis_text += f"   Coefficiente di variazione (CV): {thickness_cv:.1f}%\n\n"

                analysis_text += f"   SPIEGAZIONE METRICA:\n"
                analysis_text += f"   Il coefficiente di variazione (CV) = (σ/media) × 100 misura\n"
                analysis_text += f"   quanto lo spessore varia lungo la lunghezza dell'ascia.\n"
                analysis_text += f"   CV basso = spessore uniforme (buon controllo fusione)\n"
                analysis_text += f"   CV alto = spessore variabile (difficoltà nella colata)\n\n"

                if thickness_cv < 15:
                    analysis_text += "   INTERPRETAZIONE: CV < 15% - Spessore molto uniforme.\n"
                    analysis_text += "   Indica controllo eccellente della fusione, tipico di artigiani esperti\n"
                    analysis_text += "   con buona gestione della colata. Il bronzo fuso aveva temperatura\n"
                    analysis_text += "   ottimale e fluidità uniforme.\n\n"
                elif thickness_cv < 30:
                    analysis_text += "   INTERPRETAZIONE: CV 15-30% - Variazione moderata dello spessore.\n"
                    analysis_text += "   Normale per fusioni complesse come asce ad incavo. La variazione\n"
                    analysis_text += "   può essere intenzionale (tagliente più sottile, tallone più spesso)\n"
                    analysis_text += "   o dovuta alla complessità geometrica dello stampo.\n\n"
                else:
                    analysis_text += "   INTERPRETAZIONE: CV > 30% - Variazione significativa.\n"
                    analysis_text += "   Suggerisce difficoltà nel controllo del flusso del metallo durante\n"
                    analysis_text += "   la colata. Possibili cause: temperatura troppo bassa (bronzo viscoso),\n"
                    analysis_text += "   colata troppo lenta, o stampo con zone di raffreddamento irregolari.\n\n"

            # 4. PRESENCE OF FLANGES (margini rialzati) - indicates mold design
            if self.features.get('margini_rialzati_presenti', False):
                analysis_text += "4. TECNICA DELLO STAMPO\n"
                analysis_text += "   Presenza di margini rialzati confermata.\n\n"
                analysis_text += "   Interpretazione: I margini rialzati sono caratteristici degli stampi bivalve "
                analysis_text += "con anima centrale per creare l'incavo. La loro presenza indica uso di tecnologia "
                analysis_text += "avanzata di fusione tipica del Bronzo Medio-Recente italiano.\n\n"

            # 5. SOCKET (INCAVO) FORMATION
            if self.features.get('incavo_presente', False):
                analysis_text += "5. FORMAZIONE DELL'INCAVO\n"
                if 'incavo_profilo' in self.features:
                    profilo = self.features['incavo_profilo']
                    analysis_text += f"   Profilo incavo: {profilo}\n\n"

                    if 'rettangolare' in profilo.lower() or 'quadrangolare' in profilo.lower():
                        analysis_text += "   Interpretazione: Incavo rettangolare suggerisce uso di anima rigida "
                        analysis_text += "(probabilmente in ceramica o legno) inserita nello stampo prima della colata.\n\n"
                    elif 'circolare' in profilo.lower():
                        analysis_text += "   Interpretazione: Incavo circolare potrebbe indicare uso di anima cilindrica "
                        analysis_text += "o tecnica a cera persa con modello in cera.\n\n"

            analysis_text += "CONCLUSIONE: L'analisi suggerisce fusione in stampo bivalve con tecnica avanzata, "
            analysis_text += "coerente con la produzione specializzata dell'Età del Bronzo italiana.\n"

            return analysis_text

        except Exception as e:
            return f"Analisi fusione: Errore nell'analisi ({str(e)})\n\n" + \
                   "Nota: L'analisi richiede mesh 3D completo per valutare le caratteristiche di fusione."

    def _create_pca_analysis_page(self, pdf):
        """Create REAL PCA and clustering analysis page with scatter plot and interpretation."""
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        from acs.core.database import get_database

        fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        gs = gridspec.GridSpec(3, 1, height_ratios=[0.5, 2, 1.5], hspace=0.3)

        # Title
        ax_title = fig.add_subplot(gs[0])
        ax_title.axis('off')
        ax_title.text(0.5, 0.5, f"{self.t('statistical_analysis')} - Analisi PCA",
                     ha='center', fontsize=16, fontweight='bold')

        # Try to perform real PCA analysis
        try:
            db = get_database()

            # Query all artifacts with Savignano features
            all_features_dict = db.get_all_features()

            # Filter to only artifacts with 'savignano' stylistic features
            savignano_artifacts = {}
            for aid, feat_dict in all_features_dict.items():
                if 'savignano' in feat_dict and isinstance(feat_dict['savignano'], dict):
                    savignano_artifacts[aid] = feat_dict['savignano']

            if len(savignano_artifacts) >= 3:  # Need at least 3 samples for PCA
                # Extract numerical features for PCA
                feature_names = ['lunghezza_totale', 'larghezza_max', 'spessore_max',
                               'tallone_larghezza', 'tallone_spessore',
                               'tagliente_larghezza', 'incavo_larghezza', 'incavo_profondita']

                artifact_ids = []
                X = []

                for aid, features in savignano_artifacts.items():
                    # Extract feature vector
                    vector = []
                    valid = True
                    for fname in feature_names:
                        val = features.get(fname, None)
                        if val is None or not isinstance(val, (int, float)):
                            valid = False
                            break
                        vector.append(float(val))

                    if valid:
                        artifact_ids.append(aid)
                        X.append(vector)

                if len(X) >= 3:
                    X = np.array(X)

                    # Standardize features
                    scaler = StandardScaler()
                    X_scaled = scaler.fit_transform(X)

                    # Perform PCA
                    pca = PCA(n_components=2)
                    X_pca = pca.fit_transform(X_scaled)

                    # Get current artifact position
                    current_idx = artifact_ids.index(self.artifact_id) if self.artifact_id in artifact_ids else None

                    # Plot scatter
                    ax_scatter = fig.add_subplot(gs[1])
                    ax_scatter.scatter(X_pca[:, 0], X_pca[:, 1], c='lightgray', s=50, alpha=0.6, label='Altre asce')

                    if current_idx is not None:
                        ax_scatter.scatter(X_pca[current_idx, 0], X_pca[current_idx, 1],
                                         c='red', s=200, marker='*', edgecolors='black', linewidth=1.5,
                                         label=f'{self.artifact_id} (corrente)', zorder=5)

                    # Add loadings vectors (biplot)
                    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
                    scale_factor = 0.7 * (X_pca.max() - X_pca.min()) / (loadings.max() - loadings.min())

                    for i, fname in enumerate(feature_names):
                        if i < len(loadings):
                            ax_scatter.arrow(0, 0, loadings[i, 0] * scale_factor, loadings[i, 1] * scale_factor,
                                           head_width=0.1, head_length=0.1, fc='blue', ec='blue', alpha=0.4)
                            ax_scatter.text(loadings[i, 0] * scale_factor * 1.15, loadings[i, 1] * scale_factor * 1.15,
                                          fname.replace('_', ' '), fontsize=6, ha='center', color='blue')

                    ax_scatter.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varianza)', fontsize=10)
                    ax_scatter.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% varianza)', fontsize=10)
                    ax_scatter.set_title('Scatter Plot PCA con Loadings', fontsize=11, fontweight='bold')
                    ax_scatter.legend(fontsize=8, loc='best')
                    ax_scatter.grid(True, alpha=0.3)
                    ax_scatter.axhline(0, color='black', linewidth=0.5, linestyle='--', alpha=0.3)
                    ax_scatter.axvline(0, color='black', linewidth=0.5, linestyle='--', alpha=0.3)

                    # Generate interpretation
                    ax_text = fig.add_subplot(gs[2])
                    ax_text.axis('off')

                    interpretation = self._generate_pca_interpretation(
                        pca, X_pca, artifact_ids, current_idx, feature_names, loadings
                    )

                    ax_text.text(0.05, 0.95, interpretation, ha='left', va='top', fontsize=9,
                               wrap=True, family='monospace')

                else:
                    raise ValueError("Insufficient valid data for PCA")
            else:
                raise ValueError("Insufficient artifacts with Savignano features")

        except Exception as e:
            # Fallback to placeholder if real PCA fails
            print(f"Warning: PCA analysis failed ({str(e)}), using placeholder")
            ax_plot = fig.add_subplot(gs[1])
            ax_plot.axis('off')
            ax_plot.text(0.5, 0.5, f"Analisi PCA non disponibile\n\nMotivo: {str(e)}\n\nSono necessari almeno 3 artefatti Savignano con features complete.",
                       ha='center', va='center', fontsize=10, wrap=True,
                       bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

            ax_text = fig.add_subplot(gs[2])
            ax_text.axis('off')

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _generate_pca_interpretation(self, pca, X_pca, artifact_ids, current_idx,
                                    feature_names, loadings) -> str:
        """Generate detailed PCA interpretation in Italian with explanations."""
        var_ratio = pca.explained_variance_ratio_

        text = "ANALISI DELLE COMPONENTI PRINCIPALI (PCA)\n\n"

        text += f"Dataset: {len(artifact_ids)} asce Savignano analizzate\n"
        text += f"Features utilizzate: {len(feature_names)} caratteristiche morfometriche\n\n"

        text += f"PC1: {var_ratio[0]*100:.1f}% della varianza totale\n"
        text += f"PC2: {var_ratio[1]*100:.1f}% della varianza totale\n"
        text += f"Varianza cumulativa: {(var_ratio[0] + var_ratio[1])*100:.1f}%\n\n"

        text += "SPIEGAZIONE:\n"
        text += f"La PCA riduce {len(feature_names)} dimensioni a 2 componenti principali che\n"
        text += f"catturano {(var_ratio[0] + var_ratio[1])*100:.1f}% della variazione morfometrica.\n\n"

        # Interpret PC1
        pc1_loadings = [(feature_names[i], loadings[i, 0]) for i in range(len(feature_names))]
        pc1_loadings.sort(key=lambda x: abs(x[1]), reverse=True)

        text += f"PC1 (asse orizzontale):\n"
        text += f"  Rappresenta principalmente: {pc1_loadings[0][0].replace('_', ' ')}\n"
        text += f"  Contributi principali:\n"
        for fname, loading in pc1_loadings[:3]:
            text += f"    - {fname.replace('_', ' ')}: {loading:.3f}\n"

        text += f"\nPC2 (asse verticale):\n"
        pc2_loadings = [(feature_names[i], loadings[i, 1]) for i in range(len(feature_names))]
        pc2_loadings.sort(key=lambda x: abs(x[1]), reverse=True)
        text += f"  Rappresenta principalmente: {pc2_loadings[0][0].replace('_', ' ')}\n"

        # Current artifact position
        if current_idx is not None:
            text += f"\nPOSIZIONE ARTEFATTO CORRENTE ({self.artifact_id}):\n"
            pc1_val = X_pca[current_idx, 0]
            pc2_val = X_pca[current_idx, 1]

            # Distance from center
            dist_center = np.sqrt(pc1_val**2 + pc2_val**2)
            mean_dist = np.sqrt((X_pca**2).sum(axis=1)).mean()

            if dist_center < mean_dist * 0.7:
                text += "  Posizione: TIPICA (vicino al centro del cluster)\n"
            elif dist_center > mean_dist * 1.5:
                text += "  Posizione: ATIPICA (outlier, caratteristiche uniche)\n"
            else:
                text += "  Posizione: MODERATA (nella distribuzione normale)\n"

        text += f"\nIMPLICAZIONI ARCHEOLOGICHE:\n"
        text += f"Le asce raggruppate nello scatter indicano similarità morfometrica,\n"
        text += f"suggerendo possibile origine comune (stessa officina, periodo, tradizione).\n"

        return text

    def _create_comparative_analysis_page(self, pdf):
        """Create REAL comparative analysis with similarity metrics and charts."""
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics.pairwise import euclidean_distances
        from acs.core.database import get_database

        fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        gs = gridspec.GridSpec(4, 1, height_ratios=[0.4, 1.5, 1.2, 1.5], hspace=0.4)

        # Title
        ax_title = fig.add_subplot(gs[0])
        ax_title.axis('off')
        ax_title.text(0.5, 0.5, self.t('comparative_analysis'),
                     ha='center', fontsize=16, fontweight='bold')

        try:
            db = get_database()

            # Query all artifacts with Savignano features
            all_features_dict = db.get_all_features()

            # Filter to only artifacts with 'savignano' stylistic features
            savignano_artifacts = {}
            for aid, feat_dict in all_features_dict.items():
                if 'savignano' in feat_dict and isinstance(feat_dict['savignano'], dict):
                    savignano_artifacts[aid] = feat_dict['savignano']

            if len(savignano_artifacts) >= 2 and self.artifact_id in savignano_artifacts:
                # Extract numerical features for comparison
                feature_names = ['lunghezza_totale', 'larghezza_max', 'spessore_max',
                               'tallone_larghezza', 'tallone_spessore',
                               'tagliente_larghezza', 'incavo_larghezza', 'incavo_profondita']

                artifact_ids = []
                X = []

                for aid, features in savignano_artifacts.items():
                    vector = []
                    valid = True
                    for fname in feature_names:
                        val = features.get(fname, None)
                        if val is None or not isinstance(val, (int, float)):
                            valid = False
                            break
                        vector.append(float(val))

                    if valid:
                        artifact_ids.append(aid)
                        X.append(vector)

                if len(X) >= 2:
                    X = np.array(X)

                    # Standardize
                    scaler = StandardScaler()
                    X_scaled = scaler.fit_transform(X)

                    # Get current artifact index
                    current_idx = artifact_ids.index(self.artifact_id)
                    current_vector = X_scaled[current_idx:current_idx+1]

                    # Calculate distances to all other artifacts
                    distances = euclidean_distances(current_vector, X_scaled)[0]

                    # Convert to similarity scores (0-100%)
                    max_dist = distances.max()
                    similarities = (1 - (distances / max_dist)) * 100 if max_dist > 0 else np.ones_like(distances) * 100

                    # Get top-5 most similar (excluding self)
                    similar_indices = np.argsort(similarities)[::-1]
                    top_5_indices = [idx for idx in similar_indices if idx != current_idx][:5]

                    top_5_ids = [artifact_ids[idx] for idx in top_5_indices]
                    top_5_sims = [similarities[idx] for idx in top_5_indices]

                    # Plot 1: Bar chart of top-5 similarities
                    ax_bar = fig.add_subplot(gs[1])
                    colors = ['#4CAF50' if s >= 80 else '#FFC107' if s >= 60 else '#FF9800' for s in top_5_sims]
                    bars = ax_bar.barh(range(len(top_5_ids)), top_5_sims, color=colors, edgecolor='black', linewidth=1)

                    ax_bar.set_yticks(range(len(top_5_ids)))
                    ax_bar.set_yticklabels([f"{aid}" for aid in top_5_ids], fontsize=9)
                    ax_bar.set_xlabel('Similarità (%)', fontsize=10)
                    ax_bar.set_title(f'Top-5 Asce Più Simili a {self.artifact_id}', fontsize=11, fontweight='bold')
                    ax_bar.set_xlim(0, 100)
                    ax_bar.grid(True, axis='x', alpha=0.3)

                    # Add value labels on bars
                    for i, (bar, sim) in enumerate(zip(bars, top_5_sims)):
                        ax_bar.text(sim + 1, i, f'{sim:.1f}%', va='center', fontsize=8, fontweight='bold')

                    # Plot 2: Radar chart comparing current artifact to most similar
                    if len(top_5_indices) > 0:
                        ax_radar = fig.add_subplot(gs[2], projection='polar')

                        # Select subset of features for radar (to avoid clutter)
                        radar_features = ['lunghezza_totale', 'larghezza_max', 'tallone_larghezza',
                                        'tagliente_larghezza', 'incavo_larghezza']
                        radar_indices = [i for i, fname in enumerate(feature_names) if fname in radar_features]

                        if len(radar_indices) > 0:
                            # Normalize to 0-1 range for radar
                            from sklearn.preprocessing import MinMaxScaler
                            radar_scaler = MinMaxScaler()
                            X_radar = radar_scaler.fit_transform(X[:, radar_indices])

                            # Current artifact
                            current_radar = X_radar[current_idx]
                            # Most similar
                            most_similar_radar = X_radar[top_5_indices[0]]

                            # Setup angles
                            angles = np.linspace(0, 2 * np.pi, len(radar_features), endpoint=False).tolist()
                            current_radar_plot = current_radar.tolist()
                            most_similar_radar_plot = most_similar_radar.tolist()

                            # Close the plot
                            angles += angles[:1]
                            current_radar_plot += current_radar_plot[:1]
                            most_similar_radar_plot += most_similar_radar_plot[:1]

                            ax_radar.plot(angles, current_radar_plot, 'o-', linewidth=2, color='red',
                                        label=f'{self.artifact_id} (corrente)')
                            ax_radar.fill(angles, current_radar_plot, alpha=0.25, color='red')

                            ax_radar.plot(angles, most_similar_radar_plot, 'o-', linewidth=2, color='blue',
                                        label=f'{top_5_ids[0]} (più simile)')
                            ax_radar.fill(angles, most_similar_radar_plot, alpha=0.15, color='blue')

                            ax_radar.set_xticks(angles[:-1])
                            ax_radar.set_xticklabels([f.replace('_', '\n') for f in radar_features], fontsize=7)
                            ax_radar.set_ylim(0, 1)
                            ax_radar.set_title('Confronto Radar - Features Chiave', fontsize=10, fontweight='bold', pad=20)
                            ax_radar.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=8)
                            ax_radar.grid(True)

                    # Text interpretation
                    ax_text = fig.add_subplot(gs[3])
                    ax_text.axis('off')

                    interpretation = self._generate_comparative_interpretation(
                        artifact_ids, top_5_ids, top_5_sims, top_5_indices,
                        X, feature_names, current_idx
                    )

                    ax_text.text(0.05, 0.95, interpretation, ha='left', va='top', fontsize=9,
                               wrap=True, family='monospace')

                else:
                    raise ValueError("Insufficient valid data")
            else:
                raise ValueError("Current artifact not found or insufficient data")

        except Exception as e:
            print(f"Warning: Comparative analysis failed ({str(e)}), using placeholder")
            ax_plot = fig.add_subplot(gs[1])
            ax_plot.axis('off')
            ax_plot.text(0.5, 0.5, f"Analisi Comparativa non disponibile\n\nMotivo: {str(e)}",
                       ha='center', va='center', fontsize=10, wrap=True,
                       bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

            ax_text = fig.add_subplot(gs[2:])
            ax_text.axis('off')

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _generate_comparative_interpretation(self, all_ids, top_5_ids, top_5_sims,
                                             top_5_indices, X, feature_names, current_idx) -> str:
        """Generate detailed comparative analysis interpretation."""
        text = "ANALISI COMPARATIVA\n\n"

        text += f"Database: {len(all_ids)} asce Savignano confrontate\n"
        text += f"Metrica: Distanza euclidea normalizzata in spazio a {len(feature_names)} dimensioni\n\n"

        text += "SPIEGAZIONE DELLA METRICA:\n"
        text += "La distanza euclidea normalizzata confronta le asce su tutte le caratteristiche\n"
        text += "morfometriche simultaneamente. Similarità 100% = identica, 0% = massima differenza.\n\n"

        text += "TOP-5 ASCE PIÙ SIMILI:\n"
        for i, (aid, sim, idx) in enumerate(zip(top_5_ids, top_5_sims, top_5_indices), 1):
            text += f"{i}. {aid}: {sim:.1f}% similarità\n"

            # Find which features are most similar/different
            current_features = X[current_idx]
            other_features = X[idx]

            feature_diffs = np.abs(current_features - other_features)
            similar_feat_idx = np.argmin(feature_diffs)
            diff_feat_idx = np.argmax(feature_diffs)

            text += f"   Più simile in: {feature_names[similar_feat_idx].replace('_', ' ')}\n"
            text += f"   Differenza in: {feature_names[diff_feat_idx].replace('_', ' ')}\n"
            text += f"   ({current_features[diff_feat_idx]:.1f} vs {other_features[diff_feat_idx]:.1f} mm)\n\n"

        text += "IMPLICAZIONI ARCHEOLOGICHE:\n"
        if top_5_sims[0] >= 85:
            text += "Similarità ELEVATA (>85%): le asce più simili potrebbero provenire\n"
            text += "dalla stessa officina o periodo produttivo. Analisi stilistica consigliata.\n"
        elif top_5_sims[0] >= 70:
            text += "Similarità MODERATA (70-85%): condivisione di tradizione tipologica,\n"
            text += "ma con variazioni individuali o cronologiche.\n"
        else:
            text += "Similarità BASSA (<70%): morfologia distintiva, possibile variante\n"
            text += "locale o cronologica significativa.\n"

        return text


def generate_comprehensive_report(mesh_path: str, features: Dict, output_dir: str,
                                  artifact_id: str, language: str = 'it') -> Dict:
    """
    Generate comprehensive archaeological report.

    Args:
        mesh_path: Path to 3D mesh file
        features: Savignano morphometric features dictionary
        output_dir: Output directory for report
        artifact_id: Artifact identifier
        language: Report language ('it' or 'en')

    Returns:
        Dictionary with path to generated PDF
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / f"{artifact_id}_comprehensive_report_{language}.pdf"

    generator = SavignanoComprehensiveReport(mesh_path, features, artifact_id, language)
    results = generator.generate_complete_report(str(pdf_path))

    return results
