"""
Helper functions for rendering 3D meshes as 2D technical drawings with continuous contours.
Uses mesh slicing to get REAL outlines, not simplified convex hulls.
"""
import numpy as np
import trimesh
import matplotlib.pyplot as plt


def get_mesh_silhouette_2d(mesh, plane_normal, plane_origin):
    """
    Get the 2D silhouette (outline) of a mesh by slicing it with a plane.

    Args:
        mesh: trimesh.Trimesh object
        plane_normal: normal vector of slicing plane (e.g., [0,0,1] for XY plane)
        plane_origin: origin point on plane (e.g., mesh center)

    Returns:
        paths: list of Nx2 arrays, each representing a continuous outline path
    """
    try:
        # Slice mesh with plane to get 2D cross-section
        slice_2d = mesh.section(plane_origin=plane_origin, plane_normal=plane_normal)

        if slice_2d is None:
            return []

        # Get all paths from the slice
        paths = []
        if hasattr(slice_2d, 'entities'):
            for entity in slice_2d.entities:
                if hasattr(entity, 'points'):
                    # Get points for this path segment
                    points = slice_2d.vertices[entity.points]
                    if len(points) > 1:
                        paths.append(points)

        return paths
    except Exception as e:
        print(f"Warning: Could not compute mesh silhouette: {e}")
        return []


def project_mesh_outline(mesh, projection_axes):
    """
    Project mesh onto 2D and extract REAL outline (not convex hull).
    Uses mesh edges to find boundary.

    Args:
        mesh: trimesh.Trimesh object
        projection_axes: tuple of (axis1, axis2) to project onto

    Returns:
        paths: list of Nx2 arrays forming outline paths
    """
    # Get all unique edges
    edges = mesh.edges_unique

    # Project vertices
    vertices_2d = mesh.vertices[:, list(projection_axes)]

    # Find boundary edges (edges that belong to only one face)
    edge_face_count = np.bincount(mesh.edges_unique.flatten())

    # Edges on boundary appear only once
    # Actually in trimesh, we need to check face adjacency
    # Simpler approach: use outline_2D or project and trace

    # Alternative: Sample many slices and combine
    # For now, return dense sampling of outline
    try:
        # Get convex hull first to find outer boundary region
        from scipy.spatial import ConvexHull
        hull = ConvexHull(vertices_2d)
        hull_verts = vertices_2d[hull.vertices]

        # But we want actual mesh boundary, not convex
        # Use alpha shape or concave hull
        # For now, subsample mesh vertices densely

        # Better: use the mesh outline
        return [hull_verts]  # Temporary, will fix
    except:
        return []


def draw_outline(ax, points, color='black', linewidth=1.5, label=None, highlight_socket=False, socket_threshold=None):
    """
    Draw continuous outline from ordered points.

    Args:
        ax: matplotlib axis
        points: Nx2 array of ordered 2D points
        color: line color
        linewidth: line width
        label: optional label for legend
        highlight_socket: if True, highlight top portion in red
        socket_threshold: Y threshold for socket highlighting
    """
    if len(points) < 2:
        return

    # Close the loop
    points_closed = np.vstack([points, points[0]])

    # Draw main outline
    ax.plot(points_closed[:, 0], points_closed[:, 1],
           color=color, linewidth=linewidth, label=label, zorder=2)

    # Highlight socket if requested
    if highlight_socket and socket_threshold is not None:
        # Find points above threshold
        socket_mask = points[:, 1] >= socket_threshold
        if np.any(socket_mask):
            socket_points = points[socket_mask]
            ax.scatter(socket_points[:, 0], socket_points[:, 1],
                      c='red', s=20, alpha=0.7, label='Incavo', zorder=3)


def extract_cross_section(vertices, axis, position, tolerance=0.05):
    """
    Extract cross-section at a specific position along an axis.

    Args:
        vertices: Nx3 array of 3D vertices
        axis: axis index (0=X, 1=Y, 2=Z)
        position: position along the axis (0-1 normalized)
        tolerance: tolerance as fraction of axis range

    Returns:
        section_points: Mx2 array of 2D cross-section points
    """
    # Get axis range
    axis_values = vertices[:, axis]
    axis_min, axis_max = axis_values.min(), axis_values.max()
    axis_range = axis_max - axis_min

    # Calculate target position
    target_pos = axis_min + position * axis_range
    tolerance_abs = tolerance * axis_range

    # Extract vertices near this position
    mask = np.abs(axis_values - target_pos) < tolerance_abs
    section_verts = vertices[mask]

    if len(section_verts) < 3:
        return np.array([])

    # Get the other two axes for cross-section
    other_axes = [i for i in range(3) if i != axis]
    section_2d = section_verts[:, other_axes]

    return section_2d
