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
        self._output_format = 'png'

    def _save_figure(self, fig) -> bytes:
        """Save figure to bytes in the current output format (png or svg)."""
        buf = io.BytesIO()
        fmt = getattr(self, '_output_format', 'png')
        try:
            fig.tight_layout()
        except Exception:
            pass
        fig.savefig(buf, format=fmt, dpi=self.dpi, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    def generate_complete_drawing(self, mesh, artifact_id: str,
                                  features: Dict = None,
                                  output_format: str = 'png') -> Dict[str, bytes]:
        """
        Generate complete technical drawing sheet with all standard views.

        Args:
            mesh: Trimesh object
            artifact_id: Artifact identifier
            features: Optional morphometric features
            output_format: 'png' or 'svg'

        Returns:
            Dictionary with image buffers for each view
        """
        requested_format = output_format if output_format in ('png', 'svg') else 'png'
        self._output_format = 'png'
        oriented_mesh = self._reorient_mesh(mesh)

        views = {}

        views['longitudinal_profile'] = self._draw_longitudinal_profile(oriented_mesh, artifact_id)
        views['cross_section_high'] = self._draw_cross_section(oriented_mesh, 'high')
        views['cross_section_mid'] = self._draw_cross_section(oriented_mesh, 'mid')
        views['cross_section_low'] = self._draw_cross_section(oriented_mesh, 'low')
        views['front_view'] = self._draw_front_view(oriented_mesh)
        views['back_view'] = self._draw_back_view(oriented_mesh)
        views['tallone_top'] = self._draw_tallone_top_view(oriented_mesh)

        views['cross_section_max'] = views['cross_section_high']
        views['cross_section_min'] = views['cross_section_low']

        self._output_format = requested_format
        views['complete_sheet'] = self._create_composite_sheet(
            oriented_mesh, artifact_id, features, views
        )

        return views

    def generate_single_view(self, mesh, artifact_id: str, view_type: str,
                             features: Dict = None,
                             output_format: str = 'png') -> bytes:
        """
        Generate a single view without rendering all the others.

        For 'complete_sheet' this still renders all sub-views (needed for
        the composite), but for any individual view it's much faster.
        """
        self._output_format = output_format if output_format in ('png', 'svg') else 'png'
        oriented_mesh = self._reorient_mesh(mesh)

        alias_map = {
            'cross_section_max': 'cross_section_high',
            'cross_section_min': 'cross_section_low',
        }
        resolved = alias_map.get(view_type, view_type)

        if resolved == 'complete_sheet':
            return self.generate_complete_drawing(
                mesh, artifact_id, features, output_format
            )['complete_sheet']

        if resolved == 'longitudinal_profile':
            return self._draw_longitudinal_profile(oriented_mesh, artifact_id)
        elif resolved in ('cross_section_high', 'cross_section_mid', 'cross_section_low'):
            section_type = resolved.replace('cross_section_', '')
            return self._draw_cross_section(oriented_mesh, section_type)
        elif resolved == 'front_view':
            return self._draw_front_view(oriented_mesh)
        elif resolved == 'back_view':
            return self._draw_back_view(oriented_mesh)
        elif resolved == 'tallone_top':
            return self._draw_tallone_top_view(oriented_mesh)
        else:
            raise ValueError(f"Invalid view type: {view_type}")

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

            # Ensure WIDTH is along X and THICKNESS along Y.
            # After aligning the long axis to Z, the wider of the two remaining
            # axes must be X (so the front view shows the broad face and the
            # profile shows the thin edge).
            ext = oriented.bounds[1] - oriented.bounds[0]
            if ext[1] > ext[0]:
                rot_z = np.eye(4)
                rot_z[:3, :3] = Rotation.from_euler('z', 90, degrees=True).as_matrix()
                oriented.apply_transform(rot_z)
        except Exception as e:
            print(f"Warning: Could not reorient mesh ({str(e)}), using original orientation")
            # Return copy as-is if reorientation fails

        return oriented

    def _get_real_silhouette(self, mesh, plane_normal, projection_axes):
        """
        Extract real mesh silhouette by projecting all vertices and computing
        the alpha shape (concave hull) to preserve concavities like incavo,
        margini, and blade curvature.

        Args:
            mesh: Trimesh object
            plane_normal: Normal of the viewing plane (e.g. [0,1,0] for side view)
            projection_axes: Tuple of (axis1, axis2) indices for 2D projection

        Returns:
            np.ndarray: Ordered 2D outline points, or None on failure
        """
        try:
            proj_ax = list(projection_axes)
            points_2d = mesh.vertices[:, proj_ax]

            if len(points_2d) < 10:
                return None

            return self._alpha_shape(points_2d)
        except Exception:
            return None

    def _draw_feature_edges(self, ax, mesh, projection_axes, angle_threshold=0.25,
                            linewidth=0.35):
        """
        Draw internal feature edges (sharp creases) projected to 2D.

        These reveal real morphological features from the 3D model that the
        outer silhouette misses — e.g. the ridges of the margini rialzati
        (flanges/alette) of a flanged axe, and the rim of the incavo (socket)
        in the tallone.

        Uses a DUAL threshold so both crisp creases (synthetic models) and the
        softer transitions typical of real 3D scans are picked up:
        - strong edges (dihedral angle > 0.5 rad ≈ 29°): solid, thicker
        - subtle edges (angle_threshold .. 0.5 rad): thinner, lighter

        Args:
            ax: Matplotlib axis
            mesh: Trimesh object
            projection_axes: (axis1, axis2) indices to project onto
            angle_threshold: Lower dihedral angle (radians) above which an edge
                             is drawn at all (~0.25 rad ≈ 14°). Lowered from 0.5
                             so real scans with smoother flange ridges still show.
            linewidth: Base line width for strong feature edges
        """
        try:
            from matplotlib.collections import LineCollection

            proj = list(projection_axes)
            angles = mesh.face_adjacency_angles
            edges = mesh.face_adjacency_edges

            if angles is None or len(angles) == 0:
                return

            verts_2d = mesh.vertices[:, proj]

            strong_threshold = 0.5
            strong_mask = angles > strong_threshold
            subtle_mask = (angles > angle_threshold) & (angles <= strong_threshold)

            strong_edges = edges[strong_mask]
            subtle_edges = edges[subtle_mask]

            # Subtle edges first (under the strong ones), lighter and thinner
            if len(subtle_edges) > 0:
                segments = verts_2d[subtle_edges]
                lc = LineCollection(segments, colors='black',
                                    linewidths=linewidth * 0.55,
                                    alpha=0.45, zorder=2)
                ax.add_collection(lc)

            if len(strong_edges) > 0:
                segments = verts_2d[strong_edges]
                lc = LineCollection(segments, colors='black',
                                    linewidths=linewidth, alpha=0.85, zorder=2)
                ax.add_collection(lc)
        except Exception as e:
            print(f"Warning: Could not draw feature edges ({str(e)})")

    def _alpha_shape(self, points, alpha_factor=0.3):
        """
        Compute alpha shape (concave hull) of 2D points.

        Uses Delaunay triangulation and removes triangles with circumradius
        larger than 1/alpha.

        Args:
            points: Nx2 array of 2D points
            alpha_factor: Controls concavity (0=convex, higher=more concave).
                         Specified as fraction of bounding box diagonal.

        Returns:
            np.ndarray: Ordered boundary points, or None on failure
        """
        from scipy.spatial import Delaunay
        from collections import defaultdict

        points = np.array(points)
        if len(points) < 4:
            return None

        bbox_diag = np.linalg.norm(points.max(axis=0) - points.min(axis=0))
        alpha = alpha_factor / bbox_diag if bbox_diag > 0 else 1.0

        tri = Delaunay(points)

        boundary_edges = defaultdict(int)

        for simplex in tri.simplices:
            a, b, c = points[simplex[0]], points[simplex[1]], points[simplex[2]]

            ab = np.linalg.norm(b - a)
            bc = np.linalg.norm(c - b)
            ca = np.linalg.norm(a - c)

            s = (ab + bc + ca) / 2.0
            area = max(s * (s - ab) * (s - bc) * (s - ca), 0)
            area = np.sqrt(area)

            if area > 0:
                circumradius = (ab * bc * ca) / (4.0 * area)
            else:
                circumradius = float('inf')

            if circumradius < 1.0 / alpha:
                for edge in [(simplex[0], simplex[1]),
                             (simplex[1], simplex[2]),
                             (simplex[2], simplex[0])]:
                    e = tuple(sorted(edge))
                    boundary_edges[e] += 1

        border = [e for e, count in boundary_edges.items() if count == 1]

        if not border:
            return None

        adjacency = defaultdict(list)
        for i, j in border:
            adjacency[i].append(j)
            adjacency[j].append(i)

        ordered = [border[0][0]]
        visited = {border[0][0]}
        current = border[0][0]

        while True:
            found_next = False
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    ordered.append(neighbor)
                    visited.add(neighbor)
                    current = neighbor
                    found_next = True
                    break
            if not found_next:
                break

        if len(ordered) < 3:
            return None

        return points[ordered]

    def _draw_longitudinal_profile(self, mesh, artifact_id: str) -> bytes:
        """
        Draw longitudinal profile (side view) with STIPPLING for shadows.

        Uses real mesh silhouette (not convex hull) to preserve concavities
        like incavo, margini, and blade curvature.
        """
        fig, ax = plt.subplots(figsize=(5, 8), dpi=self.dpi)

        try:
            # Profile = SIDE view: look along X, project onto Y-Z plane
            # (thickness x length) so the thin edge and the flanges show.
            vertices_3d = mesh.vertices
            vertices_2d = vertices_3d[:, [1, 2]]  # Y (thickness) and Z (length)

            outline = self._get_real_silhouette(mesh, plane_normal=[1, 0, 0], projection_axes=(1, 2))

            if outline is None or len(outline) <= 2:
                from scipy.spatial import ConvexHull
                hull = ConvexHull(vertices_2d)
                outline = vertices_2d[hull.vertices]

            outline_closed = np.vstack([outline, outline[0]])
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=0.8, solid_capstyle='round')
            # Internal feature edges from the 3D model (flange ridges, etc.)
            self._draw_feature_edges(ax, mesh, projection_axes=(1, 2))
            self._add_stippling_shading(ax, mesh, vertices_2d, outline, view='side')

        except Exception as e:
            print(f"Warning: Could not create longitudinal profile ({str(e)})")
            ax.text(0.5, 0.5, 'Profile unavailable', ha='center', va='center',
                   transform=ax.transAxes)

        ax.set_title(f'{artifact_id} - Profilo Longitudinale',
                    fontsize=10, pad=10)
        ax.set_aspect('equal')
        # Scale bar placed BELOW the drawing (no overlap)
        self._add_scale_bar(ax)
        ax.axis('off')

        return self._save_figure(fig)

    def _draw_cross_section(self, mesh, section_type: str = 'mid',
                            position: float = None) -> bytes:
        """
        Draw cross-section at specific height with STIPPLING.

        Args:
            mesh: Trimesh object
            section_type: 'high' (70%), 'mid' (50%), or 'low' (30%) along Z axis
            position: Optional explicit normalized position (0-1) along Z axis
        """
        fig, ax = plt.subplots(figsize=(3.5, 3.5), dpi=self.dpi)

        bounds = mesh.bounds
        z_range = bounds[1][2] - bounds[0][2]

        if position is not None:
            z_pos = bounds[0][2] + z_range * position
            title = f"Sez. {position:.0%}"
        elif section_type == 'high':
            z_pos = bounds[0][2] + z_range * 0.70
            title = "Sez. Alta"
        elif section_type == 'mid':
            z_pos = bounds[0][2] + z_range * 0.50
            title = "Sez. Media"
        else:
            z_pos = bounds[0][2] + z_range * 0.30
            title = "Sez. Bassa"

        try:
            section = mesh.section(plane_origin=[0, 0, z_pos],
                                   plane_normal=[0, 0, 1])

            if section is not None and len(section.vertices) > 2:
                planar, _ = section.to_planar()
                vertices_2d = np.array(planar.vertices)

                # Outline of the cut, then uniform stippling for the solid
                section_polys = []
                for entity in planar.entities:
                    pts = vertices_2d[entity.points]
                    if len(pts) > 1:
                        pts_closed = np.vstack([pts, pts[0]])
                        ax.plot(pts_closed[:, 0], pts_closed[:, 1],
                               'k-', linewidth=0.8, solid_capstyle='round')
                    if len(pts) > 2:
                        section_polys.append(pts)

                if section_polys:
                    self._stipple_section(ax, section_polys)
            else:
                raise ValueError("Mesh section returned no geometry")

        except Exception as e:
            print(f"Warning: Real section failed ({str(e)}), falling back to vertex band")
            try:
                from scipy.spatial import ConvexHull
                z_band = 5.0
                mask = np.abs(mesh.vertices[:, 2] - z_pos) < z_band
                nearby_vertices = mesh.vertices[mask]

                if len(nearby_vertices) > 3:
                    vertices_2d = nearby_vertices[:, :2]
                    hull = ConvexHull(vertices_2d)
                    outline = vertices_2d[hull.vertices]
                    outline_closed = np.vstack([outline, outline[0]])
                    ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                           'k-', linewidth=0.8, solid_capstyle='round')
                    self._stipple_section(ax, [outline])
                else:
                    ax.text(0.5, 0.5, 'Section unavailable', ha='center', va='center',
                           transform=ax.transAxes)
            except Exception as e2:
                ax.text(0.5, 0.5, 'Section unavailable', ha='center', va='center',
                       transform=ax.transAxes)

        ax.set_title(title, fontsize=10, pad=10)
        ax.set_aspect('equal')
        ax.axis('off')

        return self._save_figure(fig)

    def _draw_front_view(self, mesh) -> bytes:
        """Draw front view (looking down Y axis) with STIPPLING."""
        fig, ax = plt.subplots(figsize=(4, 8), dpi=self.dpi)

        vertices_2d = mesh.vertices[:, [0, 2]]  # X, Z coordinates

        try:
            outline = self._get_real_silhouette(mesh, plane_normal=[0, 1, 0], projection_axes=(0, 2))

            if outline is None or len(outline) <= 2:
                from scipy.spatial import ConvexHull
                hull = ConvexHull(vertices_2d)
                outline = vertices_2d[hull.vertices]

            outline_closed = np.vstack([outline, outline[0]])
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=0.8, solid_capstyle='round')
            # Internal feature edges (flange/margin ridges) projected from 3D
            self._draw_feature_edges(ax, mesh, projection_axes=(0, 2))
            self._add_stippling_shading(ax, mesh, vertices_2d, outline, view='front')

        except Exception as e:
            print(f"Warning: Could not compute outline ({str(e)}), using bounding box")
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

        return self._save_figure(fig)

    def _draw_back_view(self, mesh) -> bytes:
        """Draw back view (opposite of front) with STIPPLING."""
        fig, ax = plt.subplots(figsize=(4, 8), dpi=self.dpi)

        import trimesh as _trimesh
        flipped = mesh.copy()
        flipped.vertices[:, 0] = -flipped.vertices[:, 0]
        flipped.invert()

        vertices_2d = flipped.vertices[:, [0, 2]]

        try:
            outline = self._get_real_silhouette(flipped, plane_normal=[0, 1, 0], projection_axes=(0, 2))

            if outline is None or len(outline) <= 2:
                from scipy.spatial import ConvexHull
                hull = ConvexHull(vertices_2d)
                outline = vertices_2d[hull.vertices]

            outline_closed = np.vstack([outline, outline[0]])
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=0.8, solid_capstyle='round')
            self._draw_feature_edges(ax, flipped, projection_axes=(0, 2))
            self._add_stippling_shading(ax, flipped, vertices_2d, outline, view='back')

        except Exception as e:
            print(f"Warning: Could not compute outline ({str(e)}), using bounding box")
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

        return self._save_figure(fig)

    def _draw_tallone_top_view(self, mesh) -> bytes:
        """
        Draw the tallone (butt end) seen from above (top-down).

        Looks down the Z axis at the upper part of the axe (the butt), projecting
        onto the X-Y plane (width x thickness). This reveals the incavo (socket)
        as a concavity and the alette/margini rialzati as raised rims, exactly as
        in Cataruzza-style archaeological plates where the butt section is drawn
        above the front view.
        """
        fig, ax = plt.subplots(figsize=(4, 3), dpi=self.dpi)

        try:
            bounds = mesh.bounds
            z_min, z_max = bounds[0][2], bounds[1][2]
            z_range = z_max - z_min

            # Upper 15% = the tallone (butt) region
            band_threshold = z_min + z_range * 0.85
            butt_mask = mesh.vertices[:, 2] >= band_threshold
            butt_vertices = mesh.vertices[butt_mask]

            if len(butt_vertices) < 10:
                # Fall back to the upper third if the very top is too sparse
                band_threshold = z_min + z_range * 0.67
                butt_mask = mesh.vertices[:, 2] >= band_threshold
                butt_vertices = mesh.vertices[butt_mask]

            vertices_2d = butt_vertices[:, [0, 1]]  # X (width), Y (thickness)

            outline = self._alpha_shape(vertices_2d)
            if outline is None or len(outline) <= 2:
                from scipy.spatial import ConvexHull
                hull = ConvexHull(vertices_2d)
                outline = vertices_2d[hull.vertices]

            outline_closed = np.vstack([outline, outline[0]])
            ax.plot(outline_closed[:, 0], outline_closed[:, 1],
                   'k-', linewidth=0.8, solid_capstyle='round')

            # Build a sub-mesh of the butt so feature edges (incavo rim,
            # flange ridges) project onto the X-Y plane.
            try:
                import trimesh as _trimesh
                face_mask = butt_mask[mesh.faces].all(axis=1)
                if face_mask.any():
                    butt_mesh = _trimesh.Trimesh(
                        vertices=mesh.vertices,
                        faces=mesh.faces[face_mask],
                        process=False
                    )
                    self._draw_feature_edges(ax, butt_mesh,
                                             projection_axes=(0, 1))
            except Exception as fe:
                print(f"Warning: tallone feature edges failed ({str(fe)})")

            self._add_stippling_shading(ax, mesh, vertices_2d, outline,
                                        view='front')

        except Exception as e:
            print(f"Warning: Could not create tallone top view ({str(e)})")
            ax.text(0.5, 0.5, 'Tallone view unavailable', ha='center',
                   va='center', transform=ax.transAxes)

        ax.set_title('Sezione Tallone (dall\'alto)', fontsize=10, pad=10)
        ax.set_aspect('equal')
        ax.axis('off')

        return self._save_figure(fig)

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

    def _stipple_section(self, ax, polygons):
        """
        Uniform stippling for a cross-section (the solid cut), handling one or
        more disjoint polygons. Even coverage = archaeological section convention.
        """
        from matplotlib.path import Path

        polys = [np.asarray(p) for p in polygons if p is not None and len(p) >= 3]
        if not polys:
            return

        all_pts = np.vstack(polys)
        min_x, min_y = all_pts.min(axis=0)
        max_x, max_y = all_pts.max(axis=0)
        width = max_x - min_x
        height = max_y - min_y
        if width <= 0 or height <= 0:
            return

        verts = []
        codes = []
        for p in polys:
            pc = np.vstack([p, p[0]])
            verts.extend(pc.tolist())
            codes.append(Path.MOVETO)
            codes.extend([Path.LINETO] * (len(pc) - 2))
            codes.append(Path.CLOSEPOLY)
        path = Path(verts, codes)

        rng = np.random.default_rng(7)
        n = int(np.clip(width * height * 8.0, 4000, 80000))
        cx = rng.uniform(min_x, max_x, n)
        cy = rng.uniform(min_y, max_y, n)
        pts = np.column_stack([cx, cy])
        inside = path.contains_points(pts)
        pts = pts[inside]
        if len(pts) == 0:
            return

        accept = rng.random(len(pts)) < 0.5
        dots = pts[accept]
        if len(dots) == 0:
            return
        sizes = rng.uniform(0.3, 0.9, len(dots))
        ax.scatter(dots[:, 0], dots[:, 1], s=sizes, c='black',
                   marker='.', linewidths=0, alpha=0.9, zorder=1)

    def _add_stippling_shading(self, ax, mesh, vertices_2d: np.ndarray,
                              outline: np.ndarray, view: str = 'side'):
        """
        Add hand-drawn style STIPPLING (puntinato) to render volume.

        Mimics manual archaeological stippling rather than a digital grid:
        - Dots placed at irregular (Poisson-like) positions, not on a grid.
        - Density follows the rounded volume: light from the upper-left, so the
          lit (left) side stays clean and the shadow (right) side / edges get
          denser dots. This gives the object a three-dimensional read.
        - Dot size varies slightly, as with a real pen.

        The whole thing is vectorised, so it is both faster and more organic
        than the previous per-cell loop.

        Args:
            ax: Matplotlib axis
            mesh: Original 3D mesh (unused now; kept for signature compatibility)
            vertices_2d: 2D projected vertices
            outline: Ordered outline vertices
            view: 'side', 'front', or 'back'
        """
        from matplotlib.path import Path

        if outline is None or len(outline) < 3:
            return

        outline = np.asarray(outline)
        path = Path(np.vstack([outline, outline[0]]))

        min_x, min_y = outline.min(axis=0)
        max_x, max_y = outline.max(axis=0)
        width = max_x - min_x
        height = max_y - min_y
        if width <= 0 or height <= 0:
            return

        rng = np.random.default_rng(1234)  # reproducible, but irregular

        # Candidate points scale with area (density ~ a few dots per mm^2)
        area = width * height
        n_candidates = int(np.clip(area * 6.0, 4000, 80000))
        cx = rng.uniform(min_x, max_x, n_candidates)
        cy = rng.uniform(min_y, max_y, n_candidates)
        pts = np.column_stack([cx, cy])

        inside = path.contains_points(pts)
        pts = pts[inside]
        if len(pts) == 0:
            return

        # Per-row local centre and half-width (to normalise the form across width)
        nbins = 200
        rel_y = (pts[:, 1] - min_y) / height
        bin_idx = np.clip((rel_y * (nbins - 1)).astype(int), 0, nbins - 1)

        left = np.full(nbins, np.nan)
        right = np.full(nbins, np.nan)
        order = np.argsort(bin_idx)
        sb = bin_idx[order]
        sx = pts[order, 0]
        # first/last occurrence per bin give min/max x quickly
        uniq, start = np.unique(sb, return_index=True)
        for k, b in enumerate(uniq):
            end = start[k + 1] if k + 1 < len(start) else len(sb)
            seg = sx[start[k]:end]
            left[b] = seg.min()
            right[b] = seg.max()

        idx_all = np.arange(nbins)
        valid = ~np.isnan(left)
        if valid.sum() < 2:
            center_arr = np.full(nbins, (min_x + max_x) / 2.0)
            half_arr = np.full(nbins, width / 2.0)
        else:
            center = (left + right) / 2.0
            half = (right - left) / 2.0
            center_arr = np.interp(idx_all, idx_all[valid], center[valid])
            half_arr = np.interp(idx_all, idx_all[valid], half[valid])
        half_arr = np.maximum(half_arr, width * 0.02)

        # u in [-1, 1]: horizontal position across the local width
        u = (pts[:, 0] - center_arr[bin_idx]) / half_arr[bin_idx]
        u = np.clip(u, -1.0, 1.0)

        # Rounded-volume shading, light from the upper-left:
        # treat the cross-section as a cylinder; brightness ~ cos(theta - light)
        theta = np.arcsin(u)
        light_theta = -0.7  # light comes from the left
        brightness = np.cos(theta - light_theta)
        b_min, b_max = brightness.min(), brightness.max()
        if b_max > b_min:
            brightness = (brightness - b_min) / (b_max - b_min)
        shadow = 1.0 - brightness

        # Extra darkening along the shadow-side edge only (keeps lit edge clean)
        edge_shadow = np.where(u > 0, u * u, 0.0)

        if view == 'section':
            # A cut surface: even, uniform stippling (indicates solid metal),
            # no directional light — archaeological section convention.
            density = np.full(len(pts), 0.45)
        else:
            # Lit rounded face: clean highlight (left), dense shadow (right)
            density = 0.04 + 0.55 * shadow + 0.18 * edge_shadow
        density = np.clip(density, 0.0, 0.92)

        accept = rng.random(len(pts)) < density
        dots = pts[accept]
        if len(dots) == 0:
            return

        sizes = rng.uniform(0.3, 1.0, len(dots))
        ax.scatter(dots[:, 0], dots[:, 1], s=sizes, c='black',
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

        The bar is placed BELOW the drawing (the y-limits are extended to make
        room) so it never overlaps the object.
        """
        ax.autoscale_view()
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        x_center = (xlim[0] + xlim[1]) / 2
        x_start = x_center - length_mm / 2
        x_end = x_center + length_mm / 2

        span = ylim[1] - ylim[0]
        drawing_bottom = ylim[0]
        gap = span * 0.06
        bar_y = drawing_bottom - gap

        # Extend the axis downward so the bar and label sit in clear space
        ax.set_ylim(bar_y - span * 0.10, ylim[1])

        ax.plot([x_start, x_end], [bar_y, bar_y],
               'k-', linewidth=4, solid_capstyle='butt')
        ax.text(x_center, bar_y - span * 0.025, '3 cm',
               ha='center', va='top', fontsize=9, fontfamily='sans-serif')

    def _create_composite_sheet(self, mesh, artifact_id: str,
                                features: Dict, views: Dict) -> bytes:
        """
        Create complete professional composite sheet - CATARUZZA-STYLE LAYOUT.

        Layout (tavola archeologica stile Cataruzza):
        - In alto (sopra la frontale): sezione del tallone vista dall'alto
        - Centro sinistra: VISTA FRONTALE (principale, grande)
        - Centro destra: sezione trasversale al punto più largo
        - In basso sinistra: profilo longitudinale (vista laterale)
        - In basso destra: pannello info (ID, misure)
        """
        fig = plt.figure(figsize=(11, 14), dpi=self.dpi)  # A4 proportions

        # Title
        fig.suptitle(f'Documentazione Tecnica - {artifact_id}',
                    fontsize=14, fontweight='bold', y=0.98)

        # Cataruzza grid: 3 rows x 2 cols
        #   row 0: tallone dall'alto (sopra la frontale)
        #   row 1: frontale (grande) + sezione trasversale
        #   row 2: profilo laterale + info panel
        gs = fig.add_gridspec(3, 2, hspace=0.22, wspace=0.25,
                             left=0.05, right=0.95, top=0.94, bottom=0.05,
                             height_ratios=[1.1, 3.2, 2.2],
                             width_ratios=[1.4, 1.0])

        # Sub-view PNGs already carry their own titles; the composite only
        # arranges them so we don't double-title each panel.

        # SOPRA LA FRONTALE: sezione del tallone vista dall'alto
        if 'tallone_top' in views:
            ax_tallone = fig.add_subplot(gs[0, 0])
            self._plot_image_in_axis(ax_tallone, views['tallone_top'])

        # CENTRO SINISTRA: vista frontale (PRINCIPALE - grande)
        ax_front = fig.add_subplot(gs[1, 0])
        self._plot_image_in_axis(ax_front, views['front_view'])

        # CENTRO DESTRA: sezione trasversale al punto più largo (affianco)
        ax_section = fig.add_subplot(gs[1, 1])
        self._plot_image_in_axis(ax_section, views['cross_section_high'])

        # BASSO SINISTRA: profilo longitudinale (vista laterale)
        ax_long = fig.add_subplot(gs[2, 0])
        self._plot_image_in_axis(ax_long, views['longitudinal_profile'])

        # BASSO DESTRA: pannello info
        ax_info = fig.add_subplot(gs[2, 1])
        ax_info.axis('off')
        self._add_info_panel(ax_info, artifact_id, features)

        return self._save_figure(fig)

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
