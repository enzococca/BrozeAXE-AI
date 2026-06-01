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
            # The composite draws every panel DIRECTLY from the mesh, so we do
            # NOT need to pre-render the individual sub-view PNGs (that would
            # double the work and can blow the request timeout on heavy scans).
            return self._create_composite_sheet(
                oriented_mesh, artifact_id, features, {}
            )

        if resolved == 'render_3d':
            # Only the 3D mesh rendered as a raster image (multi-view).
            return self._render_3d_only(oriented_mesh, artifact_id)

        if resolved == 'complete_sheet_3d':
            # The technical drawing plate WITH the 3D render attached below it.
            return self._create_composite_sheet_with_3d(
                oriented_mesh, artifact_id, features
            )

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

    def _vertex_colors(self, m):
        """
        Per-vertex RGB from the mesh's real texture / vertex colours, or None.

        Bakes a UV texture down to vertex colours via TextureVisuals.to_color()
        when present, else uses ColorVisuals.vertex_colors. A variance check
        rejects trimesh's uniform default grey for untextured meshes so plain
        geometry stays bronze while real textured scans keep their colour.
        """
        try:
            vis = getattr(m, 'visual', None)
            if vis is None:
                return None
            vc = None
            if 'Texture' in type(vis).__name__ and hasattr(vis, 'to_color'):
                try:
                    vc = vis.to_color().vertex_colors
                except Exception:
                    vc = None
            if vc is None:
                vc = getattr(vis, 'vertex_colors', None)
            if vc is not None and len(vc) == len(m.vertices):
                arr = np.asarray(vc)[:, :3].astype(float)
                var = arr.std()
                if var > 2.0:
                    return arr.astype(np.uint8)
                print(f"[vertex_colors] rejected: std={var:.1f} (uniform)")
        except Exception as e:
            print(f"Warning: vertex-colour extraction failed ({e})")
        return None

    def _render_mesh_view_pil(self, m, view_ax, proj_axes, ppm,
                              face_colors, base_rgb, light_dir):
        """Rasterize one orthographic view of the mesh to a PIL image at a
        fixed scale (``ppm`` pixels-per-mm), with painter's-algorithm depth
        sorting and per-face Lambertian shading."""
        from PIL import ImageDraw

        ax0, ax1 = proj_axes
        tris_2d = m.vertices[m.faces][:, :, [ax0, ax1]]
        flat = tris_2d.reshape(-1, 2)
        mn = flat.min(axis=0)
        span = flat.max(axis=0) - mn
        span[span == 0] = 1.0

        W = max(8, int(span[0] * ppm))
        H = max(8, int(span[1] * ppm))
        img = Image.new('RGB', (W, H), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        depths = m.vertices[m.faces][:, :, view_ax].mean(axis=1)
        order = np.argsort(depths)
        P = (tris_2d - mn) * ppm
        normals = m.face_normals

        for fi in order:
            n = normals[fi]
            brightness = 0.35 + 0.65 * float(abs(np.dot(n, light_dir)))
            bc = (face_colors[fi].astype(float) if face_colors is not None
                  else base_rgb.astype(float))
            c = np.clip(bc * brightness, 0, 255).astype(int)
            color = (int(c[0]), int(c[1]), int(c[2]))
            draw.polygon([tuple(p) for p in P[fi]], fill=color, outline=color)

        return img.transpose(Image.FLIP_TOP_BOTTOM)

    def _render_section_pil(self, mesh, ppm, base_rgb):
        """Render the transverse cross-section (mid length) as a filled
        bronze PIL image at scale ``ppm``, mirroring the drawing's Sezione
        Trasversale. Returns None if the section can't be computed."""
        from PIL import ImageDraw
        try:
            b = mesh.bounds
            z_mid = b[0][2] + (b[1][2] - b[0][2]) * 0.5
            sec = mesh.section(plane_origin=[0, 0, z_mid],
                               plane_normal=[0, 0, 1])
            if sec is None:
                return None
            planar, _ = sec.to_planar()
            sv = np.array(planar.vertices)
            polys = [sv[e.points] for e in planar.entities
                     if len(e.points) > 2]
            if not polys:
                return None
            allpts = np.vstack(polys)
            mn = allpts.min(axis=0)
            span = allpts.max(axis=0) - mn
            span[span == 0] = 1.0
            W = max(8, int(span[0] * ppm))
            H = max(8, int(span[1] * ppm))
            img = Image.new('RGB', (W, H), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            fill = (int(base_rgb[0]), int(base_rgb[1]), int(base_rgb[2]))
            for p in polys:
                pix = (p - mn) * ppm
                draw.polygon([tuple(q) for q in pix], fill=fill,
                             outline=(90, 80, 55))
            return img.transpose(Image.FLIP_TOP_BOTTOM)
        except Exception as e:
            print(f"Warning: section render failed ({e})")
            return None

    def _render_3d_layout_pil(self, mesh, include_section=True):
        """
        Fast rasterized 3D render laid out to MIRROR the drawing plate, at the
        SAME scale across panels:

            Row 0: Sezione Trasversale (cross-section)  [if include_section]
            Row 1: Vista Frontale (along Y) | Profilo Longitudinale (along X)

        All panels share one pixels-per-mm scale, so Vista Frontale and Profilo
        print at exactly the same length (as in the drawing) and the section is
        proportionate. When ``include_section`` is False the section panel is
        omitted (used in the drawing+3D combined export, where the drawing plate
        already shows the section). Uses PIL polygon rasterization (C-speed) so
        even 200k-face scans render in < 2 s. Vertex colours/texture are used
        when present; otherwise a bronze default.
        """
        try:
            from PIL import ImageDraw, ImageFont

            # Bake real colours from the FULL mesh BEFORE decimating —
            # simplify_quadric_decimation discards the texture/UV visual, so we
            # must capture colours first and then remap them onto the decimated
            # vertices by nearest neighbour. (This is why the texture used to
            # disappear from the render.)
            full_colors = self._vertex_colors(mesh)

            m = mesh
            if len(m.faces) > 12000:
                try:
                    m = m.simplify_quadric_decimation(10000)
                except Exception:
                    pass

            base_rgb = np.array([200, 184, 138], dtype=np.uint8)  # bronze
            vert_colors = full_colors
            if full_colors is not None and len(m.vertices) != len(mesh.vertices):
                try:
                    from scipy.spatial import cKDTree
                    _, idx = cKDTree(mesh.vertices).query(m.vertices)
                    vert_colors = full_colors[idx]
                except Exception:
                    vert_colors = None
            face_colors = (vert_colors[m.faces].mean(axis=1).astype(np.uint8)
                           if vert_colors is not None else None)
            if face_colors is None:
                print("[3D RENDER] no texture/vertex colours -> bronze")
            else:
                print("[3D RENDER] using real surface colour")

            ext = m.bounds[1] - m.bounds[0]
            z_ext = max(ext[2], 1e-6)
            ppm = 640.0 / z_ext  # length (Z) -> ~640 px in front & profile

            def light(v):
                v = np.asarray(v, float)
                return v / np.linalg.norm(v)

            front_img = self._render_mesh_view_pil(
                m, 1, (0, 2), ppm, face_colors, base_rgb,
                light([0.3, 1.0, 0.3]))
            prof_img = self._render_mesh_view_pil(
                m, 0, (1, 2), ppm, face_colors, base_rgb,
                light([1.0, -0.3, 0.3]))
            sec_img = (self._render_section_pil(m, ppm, base_rgb)
                       if include_section else None)

            # Compose in PIL so the true relative sizes are preserved.
            margin, gap_col, title_h, gap_row = 40, 100, 32, 60
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 22)
            except Exception:
                font = ImageFont.load_default()

            scratch = ImageDraw.Draw(Image.new('RGB', (1, 1)))

            def text_w(s):
                tb = scratch.textbbox((0, 0), s, font=font)
                return tb[2] - tb[0]

            left_x = margin
            right_x = margin + front_img.width + gap_col
            if sec_img is not None:
                sec_y = margin + title_h
                row_y = sec_y + sec_img.height + gap_row
            else:
                sec_y = margin
                row_y = margin
            front_y = row_y + title_h

            # Canvas must fit each panel AND its (possibly wider) title.
            prof_block = max(prof_img.width, text_w('Profilo Longitudinale'))
            front_block = max(front_img.width, text_w('Vista Frontale'),
                              sec_img.width if sec_img is not None else 0,
                              text_w('Sezione Trasversale'))
            right_x = margin + front_block + gap_col
            canvas_w = right_x + prof_block + margin
            canvas_h = front_y + front_img.height + margin
            canvas = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
            draw = ImageDraw.Draw(canvas)

            def titled(title, img, x, y, title_y):
                cx = x + img.width // 2 - text_w(title) // 2
                draw.text((max(2, cx), title_y), title, fill=(0, 0, 0),
                          font=font)
                canvas.paste(img, (x, y))

            if sec_img is not None:
                titled('Sezione Trasversale', sec_img, left_x, sec_y, margin)
            titled('Vista Frontale', front_img, left_x, front_y, row_y)
            titled('Profilo Longitudinale', prof_img, right_x, front_y, row_y)

            return canvas
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Warning: 3D layout render failed ({e})")
            return None

    def _placeholder_png(self, message: str) -> bytes:
        """Render a simple 'not available' placeholder as PNG bytes."""
        fig, ax = plt.subplots(figsize=(6, 4), dpi=self.dpi)
        ax.text(0.5, 0.5, message, ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.axis('off')
        prev = self._output_format
        self._output_format = 'png'
        try:
            return self._save_figure(fig)
        finally:
            self._output_format = prev

    def _render_3d_only(self, mesh, artifact_id: str) -> bytes:
        """Return just the 3D render (drawing-style layout) as PNG bytes."""
        img = self._render_3d_layout_pil(mesh)
        if img is None:
            return self._placeholder_png('Render 3D non disponibile')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf.getvalue()

    def _create_composite_sheet_with_3d(self, mesh, artifact_id: str,
                                        features: Dict) -> bytes:
        """
        Build the technical drawing plate and the 3D render SIDE BY SIDE, at the
        same height (proportional), as a single PNG. The 3D render here omits
        the cross-section (the drawing plate already shows it) — it only carries
        Vista Frontale + Profilo. Falls back to the plain drawing plate if the
        3D render is unavailable, so the request never fails.
        """
        prev = self._output_format
        self._output_format = 'png'
        try:
            drawing_png = self._create_composite_sheet(
                mesh, artifact_id, features, {})
        finally:
            self._output_format = prev

        render_img = self._render_3d_layout_pil(mesh, include_section=False)
        if render_img is None:
            return drawing_png

        try:
            drawing_img = Image.open(io.BytesIO(drawing_png)).convert('RGB')

            # The drawing plate reserves vertical room for the section, scale
            # bar, info strip and title, so the axe occupies roughly 55-60%
            # of the image height. Scale the 3D render down to match.
            target_h = int(drawing_img.height * 0.58)
            r_scale = target_h / render_img.height
            render_resized = render_img.resize(
                (max(1, int(render_img.width * r_scale)), target_h))

            gap = max(20, int(drawing_img.width * 0.03))
            total_w = drawing_img.width + gap + render_resized.width
            combined = Image.new('RGB', (total_w, drawing_img.height), 'white')
            combined.paste(drawing_img, (0, 0))
            # Top-align the 3D with the drawing so both sit on the same line.
            combined.paste(render_resized, (drawing_img.width + gap, 0))

            buf = io.BytesIO()
            combined.save(buf, format='PNG')
            buf.seek(0)
            return buf.getvalue()
        except Exception as e:
            print(f"Warning: could not combine drawing with 3D render ({e})")
            return drawing_png

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

            # Ensure TALLONE up, TAGLIENTE down. The cutting edge (tagliente)
            # is the wider, flared end; the butt (tallone) is narrower. Compare
            # the X-width near each end and, if the wider end is at the top,
            # flip 180° about X so the blade points DOWN — the standard
            # archaeological orientation used in the plate.
            v = oriented.vertices
            z = v[:, 2]
            z_min, z_max = z.min(), z.max()
            z_rng = max(z_max - z_min, 1e-9)
            top = v[z > z_max - 0.18 * z_rng]
            bot = v[z < z_min + 0.18 * z_rng]
            if len(top) >= 3 and len(bot) >= 3:
                top_w = top[:, 0].max() - top[:, 0].min()
                bot_w = bot[:, 0].max() - bot[:, 0].min()
                if top_w > bot_w:  # wide blade is up -> flip it down
                    flip = np.eye(4)
                    flip[:3, :3] = Rotation.from_euler('x', 180, degrees=True).as_matrix()
                    oriented.apply_transform(flip)
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

    def _draw_occluding_contours(self, ax, mesh, view_axis, projection_axes,
                                 linewidth=0.5, alpha=0.9):
        """
        Draw occluding-contour (fold) lines for an orthographic view.

        For a parallel projection along ``view_axis``, an edge sits on a fold/
        silhouette when its two adjacent faces have face-normal components of
        OPPOSITE sign along that axis (one faces the viewer, the other faces
        away). Unlike dihedral-angle feature edges, this captures the SMOOTH
        folds typical of a 3D scan, so it reliably reveals the crests of the
        margini rialzati (alette) and the rim of the incavo (the U-notch /
        socket at the tallone) — exactly the features that are invisible when
        only the outer silhouette is drawn.

        Args:
            ax: Matplotlib axis
            mesh: Trimesh object
            view_axis: 0=X, 1=Y, 2=Z — the direction the view looks along
            projection_axes: (axis1, axis2) indices to project the edges onto
            linewidth: Line width for the contour lines
            alpha: Line opacity
        """
        try:
            from matplotlib.collections import LineCollection

            adjacency = mesh.face_adjacency          # (M, 2) face-index pairs
            adj_edges = mesh.face_adjacency_edges     # (M, 2) vertex-index pairs
            if adjacency is None or len(adjacency) == 0:
                return

            normals = mesh.face_normals
            n0 = normals[adjacency[:, 0], view_axis]
            n1 = normals[adjacency[:, 1], view_axis]

            # Fold edges: the two faces look in opposite directions along the
            # view axis. A small deadband ignores near-tangent noise.
            eps = 1e-3
            fold_mask = (((n0 > eps) & (n1 < -eps)) |
                         ((n0 < -eps) & (n1 > eps)))
            fold_edges = adj_edges[fold_mask]
            if len(fold_edges) == 0:
                return

            proj = list(projection_axes)
            verts_2d = mesh.vertices[:, proj]
            segments = verts_2d[fold_edges]
            lc = LineCollection(segments, colors='black',
                                linewidths=linewidth, alpha=alpha, zorder=3)
            ax.add_collection(lc)
        except Exception as e:
            print(f"Warning: Could not draw occluding contours ({str(e)})")

    def _silhouette_mask(self, mesh, projection_axes, res=700, face_cap=80000):
        """
        Rasterize the projected mesh triangles into a coverage mask.

        Returns (mask, xs, ys) where ``mask`` is an HxW float array (1 inside
        the projected object, 0 outside) and ``xs``/``ys`` are the mm
        coordinates of the columns/rows.  Because it fills the actual
        triangles, the mask faithfully captures concavities (the incavo /
        butt notch), holes and broken parts — features a convex/alpha hull
        smooths away.
        """
        try:
            from PIL import Image, ImageDraw

            faces = mesh.faces
            if len(faces) > face_cap:
                idx = np.random.default_rng(0).choice(
                    len(faces), face_cap, replace=False)
                faces = faces[idx]

            proj = list(projection_axes)
            tris = mesh.vertices[faces][:, :, proj]
            flat = tris.reshape(-1, 2)
            mn = flat.min(axis=0)
            mx = flat.max(axis=0)
            span = mx - mn
            span[span == 0] = 1.0

            # Floor the short axis at 200px so elongated projections (e.g. the
            # longitudinal profile: ~15 mm thick × ~160 mm long) don't end up
            # with a sub-pixel-thin coverage band that leaves gaps in the
            # rasterized outline.
            min_dim = 200
            if span[0] >= span[1]:
                W = res
                H = max(min_dim, int(res * span[1] / span[0]))
            else:
                H = res
                W = max(min_dim, int(res * span[0] / span[1]))
            sx = (W - 1) / span[0]
            sy = (H - 1) / span[1]

            img = Image.new('1', (W, H), 0)
            draw = ImageDraw.Draw(img)
            P = (tris - mn) * np.array([sx, sy])
            for tri in P:
                draw.polygon([tuple(p) for p in tri], fill=1)

            mask = np.asarray(img, dtype=float)
            xs = mn[0] + np.arange(W) / sx
            ys = mn[1] + np.arange(H) / sy
            return mask, xs, ys
        except Exception as e:
            print(f"Warning: silhouette raster failed ({e})")
            return None, None, None

    def _draw_real_outline(self, ax, mesh, projection_axes, res=700,
                           linewidth=0.9):
        """
        Draw the faithful projected outline straight from the 3D mesh.

        Rasterizes the triangles (``_silhouette_mask``) and contours the
        coverage at 0.5, so the drawn outline reflects the REAL shape —
        including the incavo concavity, holes and any broken parts — instead
        of a smoothed hull. Returns the largest outline polygon (for use as
        the stippling boundary), or None on failure.
        """
        try:
            from scipy.ndimage import (gaussian_filter, binary_fill_holes,
                                       binary_closing, label)

            mask, xs, ys = self._silhouette_mask(mesh, projection_axes, res)
            if mask is None:
                return None

            # Triangle rasterization (plus the random face subsampling in
            # _silhouette_mask) leaves a peppering of 1-2 px pinholes inside
            # the silhouette. Contouring at 0.5 would trace a closed loop
            # around every one of them -> the scattered "polygon" blobs.
            # Close the speckle and fill interior holes so only the TRUE
            # outline survives; then re-open the genuinely large holes
            # (real broken-through parts) so those stay faithful.
            solid = binary_closing(mask > 0.5, iterations=2)
            filled = binary_fill_holes(solid)
            holes = filled & ~solid
            lab, n = label(holes)
            if n > 0:
                area = float(filled.sum())
                sizes = np.bincount(lab.ravel())
                big = np.zeros_like(filled)
                for i in range(1, n + 1):
                    # keep holes bigger than 0.4% of the object's area
                    if sizes[i] > area * 0.004:
                        big |= (lab == i)
                clean = filled & ~big
            else:
                clean = filled

            Xg, Yg = np.meshgrid(xs, ys)
            cs = ax.contour(Xg, Yg, gaussian_filter(clean.astype(float), 1.2),
                            levels=[0.5], colors='black',
                            linewidths=linewidth, zorder=4)
            segs = cs.allsegs[0] if cs.allsegs else []
            if not segs:
                return None
            return max(segs, key=len)
        except Exception as e:
            print(f"Warning: real outline failed ({e})")
            return None

    def _draw_alette_lines(self, ax, mesh, projection_axes=(0, 2),
                           depth_axis=1, linewidth=0.6):
        """
        Mark the inner edge of each aletta by OFFSETTING the silhouette
        inward by the actual aletta width measured from real cross-sections.

        1. Sample the silhouette (left/right edges) at many Z heights.
        2. Take real cross-sections at several Z heights and measure
           the aletta width (where Y-extent exceeds the central baseline).
        3. Offset the silhouette inward by the measured width.
        4. Smooth and draw.
        """
        try:
            from scipy.ndimage import gaussian_filter1d

            a0, a1 = list(projection_axes)
            v = mesh.vertices
            bounds = mesh.bounds
            z_min, z_max = bounds[0][2], bounds[1][2]
            z_range = z_max - z_min
            if z_range < 1:
                return

            # --- Step 1: silhouette (left/right X at each Z) ---
            n_rows = 200
            z_vals = np.linspace(z_min + z_range * 0.02,
                                 z_max - z_range * 0.02, n_rows)
            band = z_range / n_rows * 1.5
            left_x = np.full(n_rows, np.nan)
            right_x = np.full(n_rows, np.nan)
            for k, z in enumerate(z_vals):
                mask = np.abs(v[:, a1] - z) < band
                if mask.sum() < 3:
                    continue
                xs = v[mask, a0]
                left_x[k] = xs.min()
                right_x[k] = xs.max()

            valid = ~np.isnan(left_x) & ~np.isnan(right_x)
            if valid.sum() < 20:
                return
            idx = np.arange(n_rows)
            left_x = np.interp(idx, idx[valid], left_x[valid])
            right_x = np.interp(idx, idx[valid], right_x[valid])

            # --- Step 2: measure aletta width from cross-sections ---
            offsets = []
            z_meas = []
            for frac in np.linspace(0.20, 0.85, 10):
                z_pos = z_min + frac * z_range
                try:
                    sec = mesh.section(
                        plane_origin=[0, 0, z_pos],
                        plane_normal=[0, 0, 1])
                    if sec is None or len(sec.vertices) < 6:
                        continue
                    sv = sec.vertices
                    sx = sv[:, 0]
                    sy = sv[:, 1]
                    total_w = sx.max() - sx.min()
                    if total_w < 1:
                        continue

                    # Bin the section and compute Y-extent per X bin
                    n_bins = 30
                    xb = np.linspace(sx.min(), sx.max(), n_bins + 1)
                    y_ext = np.zeros(n_bins)
                    for b in range(n_bins):
                        m = (sx >= xb[b]) & (sx < xb[b + 1])
                        if m.sum() >= 2:
                            y_ext[b] = sy[m].max() - sy[m].min()

                    # Central zone baseline (middle 30%)
                    cb = y_ext[n_bins // 3: 2 * n_bins // 3]
                    cb = cb[cb > 0]
                    if len(cb) < 2:
                        continue
                    center_y = np.median(cb)
                    max_y = y_ext.max()
                    if max_y - center_y < 0.3:
                        continue
                    thr = center_y + 0.40 * (max_y - center_y)

                    # Left aletta width: from left edge, walk right
                    # until Y-extent drops below threshold
                    lw = 0
                    for b in range(n_bins):
                        if y_ext[b] > 0 and y_ext[b] < thr:
                            lw = xb[b] - sx.min()
                            break
                    # Right aletta width: from right edge, walk left
                    rw = 0
                    for b in range(n_bins - 1, -1, -1):
                        if y_ext[b] > 0 and y_ext[b] < thr:
                            rw = sx.max() - xb[b + 1]
                            break

                    w = (lw + rw) / 2.0
                    if 0.5 < w < total_w * 0.35:
                        offsets.append(w)
                        z_meas.append(z_pos)
                except Exception:
                    continue

            # Fallback: 10% of average width
            if len(offsets) < 2:
                avg_width = (right_x - left_x).mean()
                offset_arr = np.full(n_rows, avg_width * 0.10)
            else:
                offset_arr = np.interp(z_vals, z_meas, offsets)
                offset_arr = gaussian_filter1d(offset_arr, 10)

            # --- Step 3: taper so lines merge into the silhouette
            #     BEFORE the tallone (top) and BEFORE the tagliente (bottom).
            z_frac = (z_vals - z_min) / z_range
            taper = np.ones_like(z_frac)
            # Bottom: fade offset 0→1 between 12% and 28%
            bot = z_frac < 0.28
            taper[bot] = np.clip((z_frac[bot] - 0.12) / 0.16, 0, 1)
            # Top: fade offset 1→0 between 78% and 92%
            top = z_frac > 0.78
            taper[top] = np.clip((0.92 - z_frac[top]) / 0.14, 0, 1)
            offset_arr *= taper

            # --- Step 4: offset lines ---
            left_line = left_x + offset_arr
            right_line = right_x - offset_arr

            left_line = gaussian_filter1d(left_line, 6)
            right_line = gaussian_filter1d(right_line, 6)

            # Only draw the middle section where offset > 0.5 mm
            draw_mask = offset_arr > 0.5
            if draw_mask.sum() < 10:
                return
            for line_x in (left_line, right_line):
                ax.plot(line_x[draw_mask], z_vals[draw_mask], 'k-',
                        linewidth=max(linewidth, 0.7),
                        alpha=0.90, zorder=3)
        except Exception as e:
            print(f"Warning: alette lines failed ({e})")

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

            # Faithful outline straight from the 3D projection
            outline = self._draw_real_outline(ax, mesh, (1, 2))
            if outline is None or len(outline) <= 2:
                outline = self._get_real_silhouette(
                    mesh, plane_normal=[1, 0, 0], projection_axes=(1, 2))
                if outline is None or len(outline) <= 2:
                    from scipy.spatial import ConvexHull
                    outline = vertices_2d[ConvexHull(vertices_2d).vertices]
                ax.plot(*np.vstack([outline, outline[0]]).T,
                       'k-', linewidth=0.8, solid_capstyle='round')
            # No stippling on the profile — only front/back views are stippled.

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

                # Sections are not stippled — only front/back views are.
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
            # Faithful outline straight from the 3D projection (incavo, holes)
            outline = self._draw_real_outline(ax, mesh, (0, 2))
            if outline is None or len(outline) <= 2:
                outline = self._get_real_silhouette(
                    mesh, plane_normal=[0, 1, 0], projection_axes=(0, 2))
                if outline is None or len(outline) <= 2:
                    from scipy.spatial import ConvexHull
                    outline = vertices_2d[ConvexHull(vertices_2d).vertices]
                ax.plot(*np.vstack([outline, outline[0]]).T,
                       'k-', linewidth=0.8, solid_capstyle='round')
            # Relief-driven stippling renders the alette faithfully — no
            # stylised ridge lines (they misrepresented the real margins).
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
            outline = self._draw_real_outline(ax, flipped, (0, 2))
            if outline is None or len(outline) <= 2:
                outline = self._get_real_silhouette(
                    flipped, plane_normal=[0, 1, 0], projection_axes=(0, 2))
                if outline is None or len(outline) <= 2:
                    from scipy.spatial import ConvexHull
                    outline = vertices_2d[ConvexHull(vertices_2d).vertices]
                ax.plot(*np.vstack([outline, outline[0]]).T,
                       'k-', linewidth=0.8, solid_capstyle='round')
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

        Uses a real mesh.section() at ~90% Z height to capture the EXACT
        cross-section outline including the incavo (socket concavity) and
        the alette/margini rialzati as convex bumps. Falls back to alpha-
        shape vertex projection if slicing fails.
        """
        fig, ax = plt.subplots(figsize=(4, 3), dpi=self.dpi)

        try:
            bounds = mesh.bounds
            z_min, z_max = bounds[0][2], bounds[1][2]
            z_range = z_max - z_min

            section_drawn = False
            # Try real cross-section at several heights near the top
            for frac in (0.95, 0.92, 0.88, 0.84):
                try:
                    z_pos = z_min + z_range * frac
                    sec = mesh.section(plane_origin=[0, 0, z_pos],
                                       plane_normal=[0, 0, 1])
                    if sec is not None and len(sec.vertices) > 2:
                        planar, _ = sec.to_planar()
                        sv = np.array(planar.vertices)
                        polys = []
                        for ent in planar.entities:
                            pts = sv[ent.points]
                            if len(pts) > 1:
                                ax.plot(*np.vstack([pts, pts[0]]).T,
                                       'k-', linewidth=0.8,
                                       solid_capstyle='round')
                            if len(pts) > 2:
                                polys.append(pts)
                        # Tallone/section view is not stippled.
                        section_drawn = True
                        break
                except Exception:
                    continue

            if not section_drawn:
                # Fallback: project top-band vertices with aggressive concavity
                band_z = z_min + z_range * 0.85
                butt_mask = mesh.vertices[:, 2] >= band_z
                butt_verts = mesh.vertices[butt_mask]
                if len(butt_verts) < 10:
                    band_z = z_min + z_range * 0.67
                    butt_mask = mesh.vertices[:, 2] >= band_z
                    butt_verts = mesh.vertices[butt_mask]
                verts_2d = butt_verts[:, [0, 1]]
                outline = self._alpha_shape(verts_2d, alpha_factor=0.8)
                if outline is None or len(outline) <= 2:
                    from scipy.spatial import ConvexHull
                    outline = verts_2d[ConvexHull(verts_2d).vertices]
                ax.plot(*np.vstack([outline, outline[0]]).T,
                       'k-', linewidth=0.8, solid_capstyle='round')
                # Tallone/section view is not stippled.

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

    def _relief_density(self, mesh, projection_axes, depth_axis,
                        pts, nu=140, nw=360):
        """
        Per-point STIPPLE DENSITY from the real 3D relief, following the
        archaeological convention: stipple the curved/sloped surfaces (the
        margini rialzati / alette and the rounded edges) for shadow and depth,
        and leave the flat central face WHITE.

        Builds the front-surface height map H(u, w), takes the gradient slope
        magnitude (flat = 0, steep = 1 after normalisation) and a directional
        shadow term, then combines them: dense where the surface slopes (the
        alette), sparse where it is flat (the centre). Returns a density in
        [0, 1] for each point, or None if no usable relief exists.
        """
        try:
            from scipy.interpolate import griddata
            from scipy.ndimage import gaussian_filter

            a0, a1 = list(projection_axes)
            v = mesh.vertices
            n = mesh.vertex_normals
            front = v[n[:, depth_axis] > 0.1]
            if len(front) < 80:
                return None

            u_min, u_max = v[:, a0].min(), v[:, a0].max()
            w_min, w_max = v[:, a1].min(), v[:, a1].max()
            us = np.linspace(u_min, u_max, nu)
            ws = np.linspace(w_min, w_max, nw)
            Ug, Wg = np.meshgrid(us, ws)

            H = griddata(front[:, [a0, a1]], front[:, depth_axis],
                         (Ug, Wg), method='linear')
            if not np.isfinite(np.nanmax(H)):
                return None
            H = np.nan_to_num(H, nan=np.nanmin(H))
            H = gaussian_filter(H, 1.3)

            du = (u_max - u_min) / max(nu - 1, 1)
            dw = (w_max - w_min) / max(nw - 1, 1)
            dHdw, dHdu = np.gradient(H, dw, du)
            slope = np.sqrt(dHdu ** 2 + dHdw ** 2)
            # Normalise by a high percentile so steep margin walls saturate and
            # the flat central face stays near zero (white).
            ref = np.percentile(slope, 88)
            if ref <= 1e-6:
                return None
            snorm = gaussian_filter(np.clip(slope / ref, 0.0, 1.0), 1.0)

            # Directional shadow: light purely from the LEFT.
            # Left-facing slopes → lit → clean white.
            # Right-facing slopes → shadow → dense stippling.
            norm = np.sqrt(dHdu ** 2 + dHdw ** 2 + 1.0)
            lu, lw, ld = -0.92, 0.0, 0.25
            ln = np.sqrt(lu * lu + lw * lw + ld * ld)
            bright = np.clip((-dHdu * lu - dHdw * lw + ld) / (norm * ln), 0, 1)
            shadow = 1.0 - bright

            # Hard gate: lit side (shadow < 0.35) gets zero stippling.
            shadow_gate = np.where(shadow > 0.35, shadow, 0.0)
            density = 0.01 + 0.90 * snorm * shadow_gate

            ui = np.clip(((pts[:, 0] - u_min) / max(u_max - u_min, 1e-6)
                          * (nu - 1)).astype(int), 0, nu - 1)
            wi = np.clip(((pts[:, 1] - w_min) / max(w_max - w_min, 1e-6)
                          * (nw - 1)).astype(int), 0, nw - 1)
            return np.clip(density[wi, ui], 0.0, 0.92)
        except Exception as e:
            print(f"Warning: relief density failed ({e})")
            return None

    def _add_stippling_shading(self, ax, mesh, vertices_2d: np.ndarray,
                              outline: np.ndarray, view: str = 'side',
                              projection_axes=None, depth_axis=None):
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

        # Resolve projection/depth axes from the view if not given explicitly.
        if projection_axes is None or depth_axis is None:
            if view in ('front', 'back'):
                projection_axes, depth_axis = (0, 2), 1
            elif view == 'side':
                projection_axes, depth_axis = (1, 2), 0

        relief_density = None
        if view in ('front', 'back', 'side') and projection_axes is not None:
            relief_density = self._relief_density(
                mesh, projection_axes, depth_axis, pts)

        if view == 'section':
            # A cut surface: even, uniform stippling (indicates solid metal),
            # no directional light — archaeological section convention.
            density = np.full(len(pts), 0.45)
        elif relief_density is not None:
            # Drive the stippling from the REAL 3D relief: dense on the curved
            # margins (alette) and rounded edges, ~white on the flat centre.
            density = relief_density
        else:
            # Fallback: lit rounded face (clean highlight left, dense shadow right)
            density = 0.04 + 0.55 * shadow + 0.18 * edge_shadow
        density = np.clip(density, 0.0, 0.95)

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

        Draws each view DIRECTLY into the composite figure (not embedding
        pre-rendered PNGs) so that all views share proportional mm-based
        coordinates and the result looks like a real archaeological plate.

        Layout (orthographic plate, Cataruzza-style):
        - Row 0: VISTA FRONTALE | SEZIONE TRASVERSALE (centered) | PROFILO
                 (front & profile at the SAME length; section hatched, placed
                  at mid-height between the two — as in published plates)
        - Row 1: info strip (scale bar drawn inside the front view)
        """
        from matplotlib.patches import Polygon as _MplPolygon

        fig = plt.figure(figsize=(12, 14), dpi=self.dpi)
        fig.suptitle(f'Documentazione Tecnica - {artifact_id}',
                    fontsize=14, fontweight='bold', y=0.98)

        bounds = mesh.bounds
        x_ext = bounds[1][0] - bounds[0][0]
        y_ext = bounds[1][1] - bounds[0][1]
        z_ext = bounds[1][2] - bounds[0][2]
        z_min, z_max = bounds[0][2], bounds[1][2]
        z_mid = 0.5 * (z_min + z_max)

        pad = z_ext * 0.03
        bar_room = z_ext * 0.12
        y_lo, y_hi = z_min - pad - bar_room, z_max + pad
        h_main = y_hi - y_lo
        h_bottom = z_ext * 0.16

        gs = fig.add_gridspec(2, 1, hspace=0.04,
                             left=0.04, right=0.96, top=0.94, bottom=0.04,
                             height_ratios=[h_main, h_bottom])

        # ALL three views share ONE axis (one coordinate system), so front,
        # section and profile are guaranteed to be at the SAME mm scale.
        ax = fig.add_subplot(gs[0, 0])
        ax.set_aspect('equal')
        ax.axis('off')

        # -- Vista Frontale (native X-Z coords) --
        front_2d = mesh.vertices[:, [0, 2]]
        fout = None
        try:
            fout = self._draw_real_outline(ax, mesh, (0, 2))
            if fout is None or len(fout) <= 2:
                fout = self._get_real_silhouette(mesh, [0, 1, 0], (0, 2))
                if fout is None or len(fout) <= 2:
                    from scipy.spatial import ConvexHull
                    fout = front_2d[ConvexHull(front_2d).vertices]
                ax.plot(*np.vstack([fout, fout[0]]).T,
                        'k-', linewidth=0.8, solid_capstyle='round')
            self._draw_alette_lines(ax, mesh, projection_axes=(0, 2),
                                    depth_axis=1)
            self._add_stippling_shading(ax, mesh, front_2d, fout, 'front')
        except Exception as e:
            print(f"Warning: front view render failed ({e})")
        fout = np.asarray(fout) if fout is not None else front_2d
        fx_min, fx_max = fout[:, 0].min(), fout[:, 0].max()
        gap = max(x_ext * 0.5, 18)

        # -- Sezione Trasversale (HATCHED), centered at mid-height, to the
        #    right of the front view, at the SAME scale --
        sec_right = fx_max + gap
        try:
            sec = mesh.section(plane_origin=[0, 0, z_mid],
                               plane_normal=[0, 0, 1])
            polys = []
            if sec is not None and len(sec.vertices) > 2:
                planar, _ = sec.to_planar()
                sv = np.array(planar.vertices)
                for ent in planar.entities:
                    pts = sv[ent.points]
                    if len(pts) > 2:
                        polys.append(pts)
            if not polys:
                raise ValueError("Section returned no geometry")
            allp = np.vstack(polys)
            scx = 0.5 * (allp[:, 0].min() + allp[:, 0].max())
            secw = allp[:, 0].max() - allp[:, 0].min()
            sec_center = fx_max + gap + secw / 2
            for p in polys:
                q = p.copy()
                q[:, 0] += (sec_center - scx)
                q[:, 1] += z_mid
                ax.add_patch(_MplPolygon(
                    q, closed=True, facecolor='none', edgecolor='black',
                    linewidth=0.9, hatch='////'))
            ax.text(sec_center, z_mid + secw * 0.5 + 6, 'Sezione Trasversale',
                    ha='center', va='bottom', fontsize=9)
            sec_right = fx_max + gap + secw
        except Exception as e:
            print(f"Warning: section render failed ({e})")

        # -- Profilo Longitudinale, to the right of the section, same scale --
        prof_2d = mesh.vertices[:, [1, 2]]
        try:
            tmpf = plt.figure()
            tmpax = tmpf.add_subplot(111)
            pout = self._draw_real_outline(tmpax, mesh, (1, 2))
            plt.close(tmpf)
            if pout is None or len(pout) <= 2:
                pout = self._get_real_silhouette(mesh, [1, 0, 0], (1, 2))
                if pout is None or len(pout) <= 2:
                    from scipy.spatial import ConvexHull
                    pout = prof_2d[ConvexHull(prof_2d).vertices]
            pout = np.asarray(pout)
            prof_off = sec_right + gap - pout[:, 0].min()
            pp = pout.copy()
            pp[:, 0] += prof_off
            ax.plot(*np.vstack([pp, pp[0]]).T, 'k-', linewidth=0.8,
                    solid_capstyle='round')
            prof_cx = prof_off + 0.5 * (pout[:, 0].min() + pout[:, 0].max())
        except Exception as e:
            print(f"Warning: profile render failed ({e})")
            prof_cx = sec_right + gap

        # Titles for front & profile (data coords, above the object).
        ax.text(0.5 * (fx_min + fx_max), z_max + pad * 1.5, 'Vista Frontale',
                ha='center', va='bottom', fontsize=10)
        ax.text(prof_cx, z_max + pad * 1.5, 'Profilo Longitudinale',
                ha='center', va='bottom', fontsize=9)

        # 3 cm scale bar under the front view.
        xc = 0.5 * (fx_min + fx_max)
        by = z_min - pad - bar_room * 0.5
        ax.plot([xc - 15, xc + 15], [by, by], 'k-', linewidth=4,
                solid_capstyle='butt')
        ax.text(xc, by - z_ext * 0.025, '3 cm', ha='center', va='top',
                fontsize=9)

        ax.set_ylim(y_lo, y_hi)

        # -- Info strip --
        ax_info = fig.add_subplot(gs[1, 0])
        ax_info.axis('off')
        self._add_info_strip(ax_info, artifact_id, features)

        return self._save_figure(fig)

    def _plot_image_in_axis(self, ax, image_bytes: bytes):
        """Plot image from bytes in axis."""
        img = Image.open(io.BytesIO(image_bytes))
        ax.imshow(img)
        ax.axis('off')

    def _add_info_strip(self, ax, artifact_id: str, features: Dict):
        """Add a clean horizontal info strip at the bottom of the plate."""
        parts = [f"ID: {artifact_id}"]
        if features:
            if 'length' in features:
                parts.append(f"L: {features['length']:.1f} mm")
            if 'width' in features:
                parts.append(f"W: {features['width']:.1f} mm")
            if 'height' in features:
                parts.append(f"H: {features['height']:.1f} mm")
            if 'volume' in features:
                parts.append(f"Vol: {features['volume']:.0f} mm³")
            if 'surface_area' in features:
                parts.append(f"Sup: {features['surface_area']:.0f} mm²")
            if 'compactness' in features:
                parts.append(f"Comp: {features['compactness']:.3f}")

        line = "  │  ".join(parts)
        ax.text(0.5, 0.5, line, transform=ax.transAxes,
               fontsize=8, ha='center', va='center', fontfamily='sans-serif',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
                         edgecolor='#cccccc', linewidth=0.5))

    def _add_info_panel(self, ax, artifact_id: str, features: Dict):
        """Add information panel with measurements and metadata (legacy)."""
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
