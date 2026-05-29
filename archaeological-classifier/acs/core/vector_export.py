"""
Vector Export Module
====================

Exports 2D technical drawing paths as DXF files for import into CAD software.
Uses ezdxf for DXF generation with real-world scale (mm).
"""

import numpy as np
import io
from typing import List, Dict, Optional


def export_dxf(paths: Dict[str, List[np.ndarray]], artifact_id: str,
               scale_mm: bool = True) -> bytes:
    """
    Export 2D drawing paths as a DXF file.

    Args:
        paths: Dictionary mapping view names to lists of Nx2 point arrays
               e.g. {'profile': [array([[x,y], ...])], 'section_high': [...]}
        artifact_id: Artifact identifier for metadata
        scale_mm: If True, coordinates are in mm (real-world scale)

    Returns:
        bytes: DXF file content
    """
    try:
        import ezdxf
    except ImportError:
        raise ImportError(
            "ezdxf is required for DXF export. Install with: pip install ezdxf"
        )

    doc = ezdxf.new('R2010')
    doc.header['$INSUNITS'] = 4  # mm

    msp = doc.modelspace()

    x_offset = 0.0
    view_spacing = 50.0  # mm gap between views

    for view_name, polylines in paths.items():
        layer_name = f"{artifact_id}_{view_name}"
        doc.layers.add(layer_name)

        view_max_x = 0.0
        for points in polylines:
            if len(points) < 2:
                continue

            offset_points = points.copy()
            offset_points[:, 0] += x_offset

            dxf_points = [(p[0], p[1]) for p in offset_points]
            dxf_points.append(dxf_points[0])  # close loop

            msp.add_lwpolyline(dxf_points, dxfattribs={'layer': layer_name})

            local_max = offset_points[:, 0].max()
            if local_max > view_max_x:
                view_max_x = local_max

        x_offset = view_max_x + view_spacing

    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode('utf-8')


def extract_paths_from_mesh(mesh, oriented_mesh=None) -> Dict[str, List[np.ndarray]]:
    """
    Extract 2D paths from a 3D mesh for all standard archaeological views.

    Args:
        mesh: Original trimesh object
        oriented_mesh: Pre-oriented mesh (optional, will orient if not provided)

    Returns:
        Dictionary of view_name -> list of Nx2 point arrays
    """
    from acs.core.technical_drawing import TechnicalDrawingGenerator

    generator = TechnicalDrawingGenerator()
    if oriented_mesh is None:
        oriented_mesh = generator._reorient_mesh(mesh)

    paths = {}

    # Profile (side view) - project onto XZ plane
    profile_outline = generator._get_real_silhouette(
        oriented_mesh, plane_normal=[0, 1, 0], projection_axes=(0, 2)
    )
    if profile_outline is not None:
        paths['profile'] = [profile_outline]

    # Cross-sections
    bounds = oriented_mesh.bounds
    z_range = bounds[1][2] - bounds[0][2]

    for name, frac in [('section_high', 0.70), ('section_mid', 0.50), ('section_low', 0.30)]:
        z_pos = bounds[0][2] + z_range * frac
        try:
            section = oriented_mesh.section(
                plane_origin=[0, 0, z_pos], plane_normal=[0, 0, 1]
            )
            if section is not None and len(section.vertices) > 2:
                planar, _ = section.to_planar()
                section_paths = []
                for entity in planar.entities:
                    pts = np.array(planar.vertices[entity.points])
                    if len(pts) > 1:
                        section_paths.append(pts)
                if section_paths:
                    paths[name] = section_paths
        except Exception:
            continue

    # Front view
    front_outline = generator._get_real_silhouette(
        oriented_mesh, plane_normal=[0, 1, 0], projection_axes=(0, 2)
    )
    if front_outline is not None:
        paths['front_view'] = [front_outline]

    return paths
