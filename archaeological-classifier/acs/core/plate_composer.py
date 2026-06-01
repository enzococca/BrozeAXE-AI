"""
Plate Composer Module
=====================

Composes publication-ready plates (tavole) from multiple artifacts and views.
Supports configurable layouts with uniform scale, scale bars, figure numbers,
and captions following archaeological publication standards.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import io
from typing import Dict, List, Optional, Tuple
from PIL import Image


class PlateComposer:
    """Compose multi-artifact publication plates."""

    PAGE_FORMATS = {
        'A4': (210, 297),   # mm
        'A3': (297, 420),
        'letter': (216, 279),
        'single_column': (85, 200),   # typical journal single column
        'double_column': (175, 200),  # typical journal double column
    }

    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def compose_plate(self, config: Dict) -> bytes:
        """
        Compose a publication plate from configuration.

        Config structure:
        {
            'title': 'Tavola 1 - Asce a margini rialzati',
            'page_format': 'A4',        # A4, A3, letter, single_column, double_column
            'orientation': 'portrait',    # portrait or landscape
            'rows': 2,
            'cols': 2,
            'uniform_scale': True,
            'output_format': 'png',      # png, svg, pdf
            'cells': [
                {
                    'artifact_id': 'AXE_001',
                    'view': 'longitudinal_profile',  # or complete_sheet, front_view, etc.
                    'figure_number': '1a',
                    'caption': 'Ascia a margini rialzati, Savignano',
                    'row': 0,
                    'col': 0,
                },
                ...
            ]
        }

        Returns:
            bytes: Image/PDF data
        """
        title = config.get('title', 'Tavola')
        page_format = config.get('page_format', 'A4')
        orientation = config.get('orientation', 'portrait')
        rows = config.get('rows', 2)
        cols = config.get('cols', 2)
        uniform_scale = config.get('uniform_scale', True)
        output_format = config.get('output_format', 'png')
        cells = config.get('cells', [])

        page_w_mm, page_h_mm = self.PAGE_FORMATS.get(page_format, (210, 297))
        if orientation == 'landscape':
            page_w_mm, page_h_mm = page_h_mm, page_w_mm

        fig_w = page_w_mm / 25.4  # mm to inches
        fig_h = page_h_mm / 25.4

        fig = plt.figure(figsize=(fig_w, fig_h), dpi=self.dpi)

        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)

        gs = GridSpec(rows + 1, cols, figure=fig,
                      hspace=0.3, wspace=0.2,
                      left=0.05, right=0.95,
                      top=0.94, bottom=0.05,
                      height_ratios=[1] * rows + [0.08])

        for cell_config in cells:
            row = cell_config.get('row', 0)
            col = cell_config.get('col', 0)
            figure_number = cell_config.get('figure_number', '')
            caption = cell_config.get('caption', '')
            image_data = cell_config.get('image_data')

            if row >= rows or col >= cols:
                continue

            ax = fig.add_subplot(gs[row, col])

            if image_data is not None:
                try:
                    img = Image.open(io.BytesIO(image_data))
                    ax.imshow(img)
                except Exception:
                    ax.text(0.5, 0.5, 'Immagine non disponibile',
                           ha='center', va='center', transform=ax.transAxes,
                           fontsize=10, color='gray')

            ax.axis('off')

            label = ''
            if figure_number:
                label = f'Fig. {figure_number}'
            if caption:
                label = f'{label}: {caption}' if label else caption
            if label:
                ax.set_title(label, fontsize=9, pad=4, loc='left', style='italic')

        # Compute effective scale from the first cell's image.
        # The individual drawing was rendered at figsize=(12,14) inches at
        # 300 DPI with a 3cm scale bar. By comparing the original image
        # size (in mm) to the cell size on the page we get the reduction.
        scale_text = ''
        for cell_config in cells:
            image_data = cell_config.get('image_data')
            if image_data is None:
                continue
            try:
                img = Image.open(io.BytesIO(image_data))
                # Original drawing page width in mm (figsize 12 in = 304.8mm)
                orig_w_mm = (img.width / self.dpi) * 25.4
                # Cell width on the composed page
                usable_w = page_w_mm * 0.90  # 5% margin each side
                cell_w_mm = usable_w / cols
                ratio = orig_w_mm / cell_w_mm
                if ratio > 1.05:
                    # Round to a clean fraction
                    nice = round(ratio * 2) / 2  # round to nearest 0.5
                    if abs(nice - round(nice)) < 0.1:
                        scale_text = f'Scala ~1:{round(nice)}'
                    else:
                        scale_text = f'Scala ~1:{nice:.1f}'
                else:
                    scale_text = 'Scala ~1:1'
                break
            except Exception:
                pass

        # Bottom info strip (no 5cm bar — each drawing has its own 3cm bar)
        ax_scale = fig.add_subplot(gs[rows, :])
        ax_scale.axis('off')
        if scale_text:
            ax_scale.text(0.01, 0.5, scale_text,
                          transform=ax_scale.transAxes,
                          ha='left', va='center', fontsize=9,
                          fontfamily='sans-serif')

        ax_scale.text(0.99, 0.5, f'{page_format} - {self.dpi} DPI',
                     transform=ax_scale.transAxes,
                     ha='right', va='center', fontsize=7, color='gray')

        buf = io.BytesIO()
        fmt = output_format if output_format in ('png', 'svg', 'pdf') else 'png'
        plt.savefig(buf, format=fmt, dpi=self.dpi, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    def compose_plate_from_artifacts(self, artifact_views: Dict[str, Dict[str, bytes]],
                                     layout: Dict) -> bytes:
        """
        Convenience method: compose a plate from pre-generated artifact views.

        Args:
            artifact_views: {artifact_id: {view_name: image_bytes, ...}, ...}
            layout: Layout configuration (same as compose_plate config but without
                    image_data in cells — will be filled automatically)

        Returns:
            bytes: Composed plate image
        """
        config = dict(layout)
        cells = []

        for cell in config.get('cells', []):
            cell = dict(cell)
            artifact_id = cell.get('artifact_id', '')
            view = cell.get('view', 'longitudinal_profile')

            if artifact_id in artifact_views:
                views = artifact_views[artifact_id]
                if view in views:
                    cell['image_data'] = views[view]

            cells.append(cell)

        config['cells'] = cells
        return self.compose_plate(config)


_plate_composer = None


def get_plate_composer() -> PlateComposer:
    """Get or create plate composer instance."""
    global _plate_composer
    if _plate_composer is None:
        _plate_composer = PlateComposer()
    return _plate_composer
