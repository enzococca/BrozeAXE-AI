"""
3D Mesh Renderer
=================

Generates 2D images from 3D meshes for reports and documentation.
Uses trimesh with pyrender for high-quality offline rendering.
"""

import os
import numpy as np
from typing import Optional, Tuple, Any
import tempfile

try:
    import trimesh
    import pyrender
    from PIL import Image
    RENDERING_AVAILABLE = True
except ImportError:
    RENDERING_AVAILABLE = False
    Image = None  # Define as None when not available
    print("Warning: pyrender or PIL not installed. 3D rendering disabled.")


class MeshRenderer:
    """
    Renders 3D meshes to 2D images for documentation.
    """

    def __init__(self, width: int = 800, height: int = 600):
        """
        Initialize renderer.

        Args:
            width: Image width in pixels
            height: Image height in pixels
        """
        if not RENDERING_AVAILABLE:
            raise ImportError("pyrender and PIL are required. Install with: pip install pyrender pillow")

        self.width = width
        self.height = height

    def render_mesh_views(self,
                          mesh,
                          output_path: str,
                          views: list = None,
                          lighting: str = 'default') -> str:
        """
        Render mesh from multiple viewpoints and create composite image.

        Args:
            mesh: Trimesh object
            output_path: Path to save output image
            views: List of view angles ('front', 'side', 'top', '3quarter')
            lighting: Lighting setup ('default', 'bright', 'archaeological')

        Returns:
            Path to generated image
        """
        if views is None:
            views = ['front', 'side', 'top', '3quarter']

        # Render each view
        view_images = []
        for view in views:
            img = self._render_single_view(mesh, view, lighting)
            if img is not None:
                view_images.append(img)

        if not view_images:
            raise ValueError("No views could be rendered")

        # Create composite image
        composite = self._create_composite(view_images, views)

        # Save
        composite.save(output_path, 'PNG', dpi=(300, 300))

        return output_path

    def _render_single_view(self,
                           mesh,
                           view: str,
                           lighting: str) -> Optional[Any]:
        """
        Render mesh from single viewpoint.

        Args:
            mesh: Trimesh object
            view: View angle name
            lighting: Lighting setup

        Returns:
            PIL Image or None
        """
        try:
            # Create pyrender scene
            scene = pyrender.Scene(ambient_light=[0.1, 0.1, 0.1],
                                  bg_color=[1.0, 1.0, 1.0, 1.0])

            # Convert trimesh to pyrender mesh
            mesh_pr = pyrender.Mesh.from_trimesh(mesh, smooth=True)
            mesh_node = scene.add(mesh_pr)

            # Setup camera based on view
            camera = self._setup_camera(mesh, view)
            scene.add(camera)

            # Setup lighting
            lights = self._setup_lighting(mesh, view, lighting)
            for light in lights:
                scene.add(light)

            # Render
            renderer = pyrender.OffscreenRenderer(self.width, self.height)
            color, depth = renderer.render(scene)
            renderer.delete()

            # Convert to PIL Image
            return Image.fromarray(color)

        except Exception as e:
            print(f"Failed to render view '{view}': {e}")
            return None

    def _setup_camera(self, mesh, view: str) -> pyrender.Camera:
        """
        Setup camera position and orientation for view.

        Args:
            mesh: Trimesh object
            view: View name

        Returns:
            Pyrender camera with node
        """
        # Get mesh bounds and center
        bounds = mesh.bounds
        center = mesh.centroid
        extent = np.max(bounds[1] - bounds[0])

        # Camera distance (enough to see whole object)
        distance = extent * 2.5

        # Define camera positions for each view
        if view == 'front':
            camera_pos = center + np.array([0, 0, distance])
            target = center
        elif view == 'side':
            camera_pos = center + np.array([distance, 0, 0])
            target = center
        elif view == 'top':
            camera_pos = center + np.array([0, distance, 0])
            target = center
        elif view == '3quarter' or view == '3q':
            # 45 degree angle from front-right-top
            camera_pos = center + np.array([distance*0.7, distance*0.7, distance*0.7])
            target = center
        else:
            # Default to front
            camera_pos = center + np.array([0, 0, distance])
            target = center

        # Create camera
        camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)

        # Create camera pose (look at target)
        camera_pose = self._look_at(camera_pos, target, up=np.array([0, 1, 0]))

        return pyrender.Node(camera=camera, matrix=camera_pose)

    def _look_at(self, eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
        """
        Create look-at matrix for camera.

        Args:
            eye: Camera position
            target: Point to look at
            up: Up vector

        Returns:
            4x4 transformation matrix
        """
        forward = target - eye
        forward = forward / np.linalg.norm(forward)

        right = np.cross(forward, up)
        right = right / np.linalg.norm(right)

        up = np.cross(right, forward)

        matrix = np.eye(4)
        matrix[:3, 0] = right
        matrix[:3, 1] = up
        matrix[:3, 2] = -forward
        matrix[:3, 3] = eye

        return matrix

    def _setup_lighting(self, mesh, view: str, lighting: str) -> list:
        """
        Setup scene lighting.

        Args:
            mesh: Trimesh object
            view: View name
            lighting: Lighting preset

        Returns:
            List of pyrender lights with nodes
        """
        center = mesh.centroid
        bounds = mesh.bounds
        extent = np.max(bounds[1] - bounds[0])
        distance = extent * 3

        lights = []

        if lighting == 'bright':
            # Bright lighting for clear visibility
            intensity = 10.0

            # Key light (main)
            key_pos = center + np.array([distance, distance, distance])
            key_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=intensity)
            lights.append(pyrender.Node(light=key_light, matrix=self._translation_matrix(key_pos)))

            # Fill light
            fill_pos = center + np.array([-distance*0.5, distance*0.5, distance*0.5])
            fill_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=intensity*0.5)
            lights.append(pyrender.Node(light=fill_light, matrix=self._translation_matrix(fill_pos)))

        elif lighting == 'archaeological':
            # Soft, diffuse lighting for archaeological documentation
            intensity = 8.0

            # Multiple soft lights from different angles
            positions = [
                center + np.array([distance, distance, 0]),
                center + np.array([-distance*0.7, distance*0.7, distance*0.7]),
                center + np.array([0, distance, distance]),
            ]

            for pos in positions:
                light = pyrender.DirectionalLight(color=[1.0, 0.98, 0.95], intensity=intensity*0.6)
                lights.append(pyrender.Node(light=light, matrix=self._translation_matrix(pos)))

        else:  # default
            # Standard 3-point lighting
            intensity = 8.0

            # Key
            key_pos = center + np.array([distance*0.7, distance*0.7, distance])
            key_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=intensity)
            lights.append(pyrender.Node(light=key_light, matrix=self._translation_matrix(key_pos)))

            # Fill
            fill_pos = center + np.array([-distance*0.5, distance*0.3, distance*0.5])
            fill_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=intensity*0.4)
            lights.append(pyrender.Node(light=fill_light, matrix=self._translation_matrix(fill_pos)))

            # Back
            back_pos = center + np.array([0, distance*0.5, -distance*0.5])
            back_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=intensity*0.3)
            lights.append(pyrender.Node(light=back_light, matrix=self._translation_matrix(back_pos)))

        return lights

    def _translation_matrix(self, translation: np.ndarray) -> np.ndarray:
        """Create 4x4 translation matrix."""
        matrix = np.eye(4)
        matrix[:3, 3] = translation
        return matrix

    def _create_composite(self, images: list, view_names: list) -> Any:
        """
        Create composite image from multiple views.

        Args:
            images: List of PIL Images
            view_names: List of view names for labels

        Returns:
            Composite PIL Image
        """
        # Calculate layout (2x2 grid for 4 views, or adapt based on count)
        n_images = len(images)

        if n_images == 1:
            return images[0]
        elif n_images == 2:
            cols, rows = 2, 1
        elif n_images <= 4:
            cols, rows = 2, 2
        else:
            cols = 3
            rows = (n_images + cols - 1) // cols

        # Resize images if needed
        target_w = self.width // cols
        target_h = self.height // rows

        resized = []
        for img in images:
            resized.append(img.resize((target_w, target_h), Image.Resampling.LANCZOS))

        # Create composite
        composite_w = target_w * cols
        composite_h = target_h * rows
        composite = Image.new('RGB', (composite_w, composite_h), 'white')

        # Paste images
        for idx, img in enumerate(resized):
            col = idx % cols
            row = idx // cols
            x = col * target_w
            y = row * target_h
            composite.paste(img, (x, y))

        return composite

    def render_technical_drawing(self,
                                 mesh,
                                 output_path: str,
                                 include_dimensions: bool = True) -> str:
        """
        Generate technical drawing with orthographic projections.

        Args:
            mesh: Trimesh object
            output_path: Output path
            include_dimensions: Add dimension annotations

        Returns:
            Path to saved image
        """
        # Render orthographic views (front, side, top)
        views = ['front', 'side', 'top']
        return self.render_mesh_views(mesh, output_path, views=views, lighting='bright')


# Global instance
_renderer = None


def _render_matplotlib_fallback(mesh, output_path: str) -> str:
    """
    Optimized fallback renderer using matplotlib for 3D visualization.
    Used when pyrender is unavailable or fails.

    Args:
        mesh: Trimesh object
        output_path: Path to save the rendered image

    Returns:
        Path to saved image
    """
    import time
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    start = time.time()
    print(f"[MATPLOTLIB] Starting render...")

    # Simplify mesh if it has too many faces (optimization)
    original_faces = len(mesh.faces)
    if original_faces > 5000:
        print(f"[MATPLOTLIB] Simplifying mesh ({original_faces} faces -> ~2500 faces)...")
        simplify_start = time.time()
        try:
            # Simplify to approximately 2500 faces for faster rendering
            mesh = mesh.simplify_quadric_decimation(2500)
            print(f"[MATPLOTLIB] Simplified to {len(mesh.faces)} faces ({time.time() - simplify_start:.2f}s)")
        except Exception as e:
            print(f"[MATPLOTLIB] Simplification failed, using original mesh: {e}")

    # Reduced figure size for faster rendering (10x7.5 instead of 12x9)
    fig = plt.figure(figsize=(10, 7.5))
    print(f"[MATPLOTLIB] Creating 4 views...")

    # Create 4 subplots for different views
    views = [
        (1, 'Front View', (0, 0)),
        (2, 'Side View', (90, 0)),
        (3, 'Top View', (0, 90)),
        (4, '3/4 View', (45, 45))
    ]

    for idx, title, (azim, elev) in views:
        view_start = time.time()
        ax = fig.add_subplot(2, 2, idx, projection='3d')

        # Create mesh collection with no edges for faster rendering
        mesh_collection = Poly3DCollection(
            mesh.vertices[mesh.faces],
            alpha=0.95,
            facecolor='#D4A76A',  # Bronze color
            edgecolor='none',  # No edges = faster rendering
            linewidths=0
        )
        ax.add_collection3d(mesh_collection)

        # Set limits
        scale = np.ptp(mesh.bounds, axis=0).max() / 2
        center = mesh.centroid
        ax.set_xlim(center[0] - scale, center[0] + scale)
        ax.set_ylim(center[1] - scale, center[1] + scale)
        ax.set_zlim(center[2] - scale, center[2] + scale)

        # Set view angle
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title, fontsize=9, pad=3)

        # Minimal axes for faster rendering
        ax.set_axis_off()  # Hide axes completely for speed

        print(f"[MATPLOTLIB] {title}: {time.time() - view_start:.2f}s")

    print(f"[MATPLOTLIB] Saving image...")
    save_start = time.time()
    plt.tight_layout(pad=0.5)
    # Reduced DPI from 150 to 120 for faster save
    plt.savefig(output_path, dpi=120, bbox_inches='tight', facecolor='white')
    print(f"[MATPLOTLIB] Save complete: {time.time() - save_start:.2f}s")
    plt.close()

    total = time.time() - start
    print(f"[MATPLOTLIB] Total rendering time: {total:.2f}s")

    return output_path


def get_mesh_renderer(width: int = 800, height: int = 600) -> MeshRenderer:
    """Get or create global mesh renderer."""
    global _renderer
    if _renderer is None:
        _renderer = MeshRenderer(width, height)
    return _renderer


def render_artifact_image(mesh, artifact_id: str, output_dir: str = '/tmp') -> Optional[str]:
    """
    Convenience function to render artifact image.

    Args:
        mesh: Trimesh object
        artifact_id: Artifact identifier
        output_dir: Directory to save image

    Returns:
        Path to saved image, or None if rendering failed
    """
    import time
    start = time.time()

    # Check if image is already cached
    output_path = os.path.join(output_dir, f"render_{artifact_id}.png")
    if os.path.exists(output_path):
        elapsed = time.time() - start
        print(f"[3D RENDER] {artifact_id} - Using cached render ({elapsed:.2f}s)")
        return output_path

    try:
        print(f"[3D RENDER] {artifact_id} - Attempting pyrender...")
        renderer = get_mesh_renderer()
        result = renderer.render_mesh_views(mesh, output_path, lighting='archaeological')
        elapsed = time.time() - start
        print(f"[3D RENDER] {artifact_id} - ✓ Pyrender success ({elapsed:.2f}s)")
        return result
    except Exception as e:
        print(f"[3D RENDER] {artifact_id} - Pyrender failed: {e}")
        print(f"[3D RENDER] {artifact_id} - Attempting matplotlib fallback...")
        try:
            result = _render_matplotlib_fallback(mesh, output_path)
            elapsed = time.time() - start
            print(f"[3D RENDER] {artifact_id} - ✓ Matplotlib fallback success ({elapsed:.2f}s)")
            return result
        except Exception as e2:
            elapsed = time.time() - start
            print(f"[3D RENDER] {artifact_id} - ✗ Both renderers failed ({elapsed:.2f}s): {e2}")
            return None
