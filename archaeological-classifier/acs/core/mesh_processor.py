"""
Mesh Processor Module
====================

Handles loading, processing, and feature extraction from 3D mesh files.
Supports OBJ, PLY, STL formats.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from pathlib import Path
import json
import os


class MeshProcessor:
    """Process and extract features from 3D mesh files."""

    SUPPORTED_FORMATS = ['.obj', '.ply', '.stl']

    def __init__(self):
        """Initialize mesh processor."""
        self.meshes: Dict[str, 'Mesh'] = {}
        self.mesh_paths: Dict[str, str] = {}  # Track file paths for persistence

    def load_mesh(self, filepath: str, artifact_id: Optional[str] = None) -> Dict:
        """
        Load a 3D mesh file and extract basic features.

        Args:
            filepath: Path to mesh file
            artifact_id: Optional ID for the artifact

        Returns:
            Dictionary with mesh features
        """
        try:
            import trimesh
        except ImportError:
            raise ImportError(
                "trimesh is required for mesh processing. "
                "Install with: pip install trimesh"
            )

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Mesh file not found: {filepath}")

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Load mesh
        mesh = trimesh.load(filepath)

        # Generate ID if not provided
        if artifact_id is None:
            artifact_id = path.stem

        # Store mesh and path
        self.meshes[artifact_id] = mesh
        self.mesh_paths[artifact_id] = str(filepath)

        # Extract features
        features = self._extract_features(mesh, artifact_id)

        return features

    def reload_from_database(self, db) -> Dict[str, int]:
        """
        Reload all meshes from database on startup.

        Args:
            db: Database instance

        Returns:
            Dictionary with reload statistics
        """
        artifacts = db.get_all_artifacts()

        stats = {
            'total': len(artifacts),
            'loaded': 0,
            'failed': 0,
            'errors': []
        }

        for artifact in artifacts:
            artifact_id = artifact['artifact_id']
            mesh_path = artifact['mesh_path']

            # Skip if no path stored
            if not mesh_path:
                continue

            # Check if file still exists
            if not os.path.exists(mesh_path):
                stats['failed'] += 1
                stats['errors'].append(f"{artifact_id}: File not found at {mesh_path}")
                continue

            try:
                # Reload mesh silently (already in database, just restore to memory)
                import trimesh
                mesh = trimesh.load(mesh_path)
                self.meshes[artifact_id] = mesh
                self.mesh_paths[artifact_id] = mesh_path
                stats['loaded'] += 1
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"{artifact_id}: {str(e)}")

        return stats

    def _extract_features(self, mesh, artifact_id: str) -> Dict:
        """Extract geometric features from mesh."""

        # Basic geometric properties
        features = {
            'id': artifact_id,
            'volume': float(mesh.volume),
            'surface_area': float(mesh.area),
            'centroid': mesh.centroid.tolist(),
            'bounds': mesh.bounds.tolist(),
        }

        # Bounding box dimensions
        bbox = mesh.bounding_box_oriented
        dimensions = bbox.primitive.extents
        features['length'] = float(max(dimensions))
        features['width'] = float(sorted(dimensions)[-2])
        features['thickness'] = float(min(dimensions))

        # Calculate dimensional ratios (important for classification)
        if features['width'] > 0:
            features['length_width_ratio'] = features['length'] / features['width']
        else:
            features['length_width_ratio'] = 0.0

        if features['thickness'] > 0:
            features['length_thickness_ratio'] = features['length'] / features['thickness']
            features['width_thickness_ratio'] = features['width'] / features['thickness']
        else:
            features['length_thickness_ratio'] = 0.0
            features['width_thickness_ratio'] = 0.0

        # Principal axes and moments of inertia
        features['principal_axes'] = mesh.principal_inertia_components.tolist()
        features['inertia'] = mesh.moment_inertia.tolist()

        # Convexity
        convex_hull = mesh.convex_hull
        features['convex_volume'] = float(convex_hull.volume)
        features['convexity'] = float(mesh.volume / convex_hull.volume)

        # Vertex and face counts
        features['n_vertices'] = len(mesh.vertices)
        features['n_faces'] = len(mesh.faces)

        # Extract profiles for EFA analysis
        features['profiles'] = self._extract_profiles(mesh)

        return features

    def _extract_profiles(self, mesh) -> Dict[str, List]:
        """Extract 2D profiles from mesh for morphometric analysis."""
        import trimesh

        profiles = {}

        # XY plane (top view)
        xy_profile = self._extract_planar_profile(mesh, plane='xy')
        if xy_profile is not None:
            profiles['xy'] = xy_profile

        # XZ plane (side view)
        xz_profile = self._extract_planar_profile(mesh, plane='xz')
        if xz_profile is not None:
            profiles['xz'] = xz_profile

        # YZ plane (front view)
        yz_profile = self._extract_planar_profile(mesh, plane='yz')
        if yz_profile is not None:
            profiles['yz'] = yz_profile

        return profiles

    def _extract_planar_profile(self, mesh, plane: str = 'xy') -> Optional[List]:
        """Extract 2D outline from a planar slice."""
        import trimesh

        # Get mesh bounds
        bounds = mesh.bounds
        center = (bounds[0] + bounds[1]) / 2

        # Define slice plane
        if plane == 'xy':
            plane_origin = [center[0], center[1], center[2]]
            plane_normal = [0, 0, 1]
        elif plane == 'xz':
            plane_origin = [center[0], center[1], center[2]]
            plane_normal = [0, 1, 0]
        elif plane == 'yz':
            plane_origin = [center[0], center[1], center[2]]
            plane_normal = [1, 0, 0]
        else:
            return None

        # Get slice
        try:
            slice_2d = mesh.section(
                plane_origin=plane_origin,
                plane_normal=plane_normal
            )

            if slice_2d is None:
                return None

            # Get 2D path
            path_2d, _ = slice_2d.to_planar()

            # Extract vertices
            if hasattr(path_2d, 'vertices'):
                return path_2d.vertices.tolist()

        except Exception:
            return None

        return None

    def batch_process(self, filepaths: List[str]) -> List[Dict]:
        """
        Process multiple mesh files in batch.

        Args:
            filepaths: List of paths to mesh files

        Returns:
            List of feature dictionaries
        """
        results = []

        for filepath in filepaths:
            try:
                features = self.load_mesh(filepath)
                results.append({
                    'status': 'success',
                    'filepath': filepath,
                    'features': features
                })
            except Exception as e:
                results.append({
                    'status': 'error',
                    'filepath': filepath,
                    'error': str(e)
                })

        return results

    def compute_distance(
        self,
        id1: str,
        id2: str,
        method: str = 'hausdorff'
    ) -> float:
        """
        Compute distance between two meshes.

        Args:
            id1: First artifact ID
            id2: Second artifact ID
            method: Distance method ('hausdorff', 'chamfer')

        Returns:
            Distance value
        """
        if id1 not in self.meshes or id2 not in self.meshes:
            raise ValueError("Both meshes must be loaded first")

        mesh1 = self.meshes[id1]
        mesh2 = self.meshes[id2]

        if method == 'hausdorff':
            # Sample points from both meshes
            points1 = mesh1.sample(1000)
            points2 = mesh2.sample(1000)

            # Compute Hausdorff distance
            from scipy.spatial.distance import directed_hausdorff
            dist1 = directed_hausdorff(points1, points2)[0]
            dist2 = directed_hausdorff(points2, points1)[0]
            return float(max(dist1, dist2))

        elif method == 'chamfer':
            # Sample points
            points1 = mesh1.sample(1000)
            points2 = mesh2.sample(1000)

            # Compute Chamfer distance
            from scipy.spatial import cKDTree
            tree1 = cKDTree(points1)
            tree2 = cKDTree(points2)

            dist1 = np.mean(tree2.query(points1)[0])
            dist2 = np.mean(tree1.query(points2)[0])

            return float((dist1 + dist2) / 2)

        else:
            raise ValueError(f"Unknown distance method: {method}")

    def export_features(self, filepath: str, format: str = 'json'):
        """
        Export all extracted features to file.

        Args:
            filepath: Output file path
            format: Export format ('json', 'csv')
        """
        features_list = []

        for artifact_id, mesh in self.meshes.items():
            features = self._extract_features(mesh, artifact_id)
            features_list.append(features)

        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(features_list, f, indent=2)

        elif format == 'csv':
            import pandas as pd
            # Flatten features for CSV
            flat_features = []
            for f in features_list:
                flat = {k: v for k, v in f.items() if not isinstance(v, (list, dict))}
                flat_features.append(flat)

            df = pd.DataFrame(flat_features)
            df.to_csv(filepath, index=False)

        else:
            raise ValueError(f"Unsupported format: {format}")
