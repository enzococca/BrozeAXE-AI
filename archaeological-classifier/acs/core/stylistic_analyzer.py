"""
Stylistic Analysis Module
=========================

Analyzes stylistic characteristics of artifacts beyond pure morphometrics.
Includes decoration patterns, surface treatment, manufacturing traces, etc.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from enum import Enum


class StylisticFeature(Enum):
    """Stylistic feature categories."""
    DECORATION = "decoration"
    SURFACE_TREATMENT = "surface_treatment"
    EDGE_PROFILE = "edge_profile"
    SYMMETRY = "symmetry"
    PROPORTIONS = "proportions"
    MANUFACTURING_TRACES = "manufacturing_traces"


class StylisticAnalyzer:
    """
    Analyzes stylistic characteristics of archaeological artifacts.

    Stylistic features complement morphometric analysis by capturing
    qualitative aspects like decoration, proportions, and craftsmanship.
    """

    def __init__(self):
        self.style_database = {}  # artifact_id -> stylistic features

    def analyze_style(self, mesh, artifact_id: str,
                     morphometric_features: Dict = None) -> Dict:
        """
        Analyze stylistic characteristics of an artifact.

        Args:
            mesh: Trimesh object
            artifact_id: Artifact identifier
            morphometric_features: Optional morphometric data

        Returns:
            Dictionary of stylistic features
        """
        style_features = {}

        # 1. Symmetry Analysis
        style_features['symmetry'] = self._analyze_symmetry(mesh)

        # 2. Proportions Analysis
        if morphometric_features:
            style_features['proportions'] = self._analyze_proportions(morphometric_features)

        # 3. Edge Profile Analysis
        style_features['edge_profile'] = self._analyze_edge_profile(mesh)

        # 4. Surface Roughness (manufacturing quality)
        style_features['surface_quality'] = self._analyze_surface_quality(mesh)

        # 5. Shape Regularity
        style_features['shape_regularity'] = self._analyze_shape_regularity(mesh)

        # 6. Curvature Analysis
        style_features['curvature'] = self._analyze_curvature(mesh)

        # Store in database
        self.style_database[artifact_id] = style_features

        return style_features

    def _analyze_symmetry(self, mesh) -> Dict:
        """
        Analyze bilateral symmetry of the artifact.

        Returns scores for X, Y, Z axis symmetry.

        For performance, samples vertices if mesh is large.
        """
        vertices = mesh.vertices

        # For performance: sample vertices if mesh is large
        MAX_VERTICES = 5000
        if len(vertices) > MAX_VERTICES:
            # Sample vertices uniformly
            indices = np.random.choice(len(vertices), MAX_VERTICES, replace=False)
            sampled_vertices = vertices[indices]
        else:
            sampled_vertices = vertices

        # Calculate symmetry for each axis
        symmetry = {}

        for axis_idx, axis_name in enumerate(['x', 'y', 'z']):
            # Reflect vertices across axis
            reflected = sampled_vertices.copy()
            reflected[:, axis_idx] *= -1

            # Find closest points and calculate distance
            from scipy.spatial import cKDTree
            tree = cKDTree(sampled_vertices)
            distances, _ = tree.query(reflected)

            # Symmetry score (1.0 = perfect symmetry)
            avg_distance = np.mean(distances)
            bbox_size = np.ptp(vertices[:, axis_idx])

            if bbox_size > 0:
                symmetry_score = max(0, 1 - (avg_distance / bbox_size))
            else:
                symmetry_score = 0

            symmetry[f'{axis_name}_symmetry'] = float(symmetry_score)

        # Overall symmetry (max across axes - most likely symmetry axis)
        symmetry['overall_symmetry'] = float(max(symmetry.values()))
        symmetry['primary_axis'] = max(symmetry.items(), key=lambda x: x[1])[0].replace('_symmetry', '')

        return symmetry

    def _analyze_proportions(self, features: Dict) -> Dict:
        """
        Analyze shape proportions.

        Bronze Age typology often focuses on ratios like length/width.
        """
        proportions = {}

        # Length to width ratio
        if 'length' in features and 'width' in features and features['width'] > 0:
            proportions['length_width_ratio'] = features['length'] / features['width']

        # Length to height ratio
        if 'length' in features and 'height' in features and features['height'] > 0:
            proportions['length_height_ratio'] = features['length'] / features['height']

        # Width to height ratio
        if 'width' in features and 'height' in features and features['height'] > 0:
            proportions['width_height_ratio'] = features['width'] / features['height']

        # Slenderness (length vs cross-section)
        if 'length' in features and 'width' in features and 'height' in features:
            cross_section = (features['width'] + features['height']) / 2
            if cross_section > 0:
                proportions['slenderness'] = features['length'] / cross_section

        # Compactness category
        if 'compactness' in features:
            comp = features['compactness']
            if comp > 0.7:
                proportions['shape_category'] = 'compact'
            elif comp > 0.4:
                proportions['shape_category'] = 'moderate'
            else:
                proportions['shape_category'] = 'elongated'

        return proportions

    def _analyze_edge_profile(self, mesh) -> Dict:
        """
        Analyze edge sharpness and profile.

        Important for Bronze Age axes: sharp cutting edge vs blunt.
        """
        vertices = mesh.vertices

        # Get edges
        edges = mesh.edges_unique
        edge_vectors = vertices[edges[:, 1]] - vertices[edges[:, 0]]
        edge_lengths = np.linalg.norm(edge_vectors, axis=1)

        # Edge statistics
        # Calculate edge uniformity with safe division
        mean_edge_len = np.mean(edge_lengths)
        if mean_edge_len > 0:
            edge_uniformity = float(1 - (np.std(edge_lengths) / mean_edge_len))
        else:
            edge_uniformity = 0.0

        profile = {
            'avg_edge_length': float(np.mean(edge_lengths)),
            'edge_length_std': float(np.std(edge_lengths)),
            'edge_uniformity': edge_uniformity
        }

        # Analyze vertex valence (number of edges per vertex)
        vertex_valence = np.bincount(edges.flatten())
        profile['avg_vertex_valence'] = float(np.mean(vertex_valence))

        # Calculate mesh regularity with safe division
        mean_valence = np.mean(vertex_valence)
        if mean_valence > 0:
            profile['mesh_regularity'] = float(1 - (np.std(vertex_valence) / mean_valence))
        else:
            profile['mesh_regularity'] = 0.0

        return profile

    def _analyze_surface_quality(self, mesh) -> Dict:
        """
        Analyze surface treatment quality.

        Smoother surfaces indicate more finishing work.
        """
        quality = {}

        # Face area variation (uniform = well-finished)
        face_areas = mesh.area_faces
        mean_area = np.mean(face_areas)
        if mean_area > 0:
            quality['face_area_uniformity'] = float(1 - (np.std(face_areas) / mean_area))
        else:
            quality['face_area_uniformity'] = 0.0

        # Normal variation (smooth = low variation)
        normals = mesh.face_normals

        # Calculate normal coherence with neighbors
        adjacency = mesh.face_adjacency
        if len(adjacency) > 0:
            normal_diffs = []
            for edge in adjacency:
                n1 = normals[edge[0]]
                n2 = normals[edge[1]]
                # Dot product = cosine of angle
                similarity = np.dot(n1, n2)
                normal_diffs.append(1 - abs(similarity))  # 0 = identical, 1 = opposite

            quality['surface_smoothness'] = float(1 - np.mean(normal_diffs))
        else:
            quality['surface_smoothness'] = 0.5

        # Overall quality score
        quality['overall_quality'] = (quality['face_area_uniformity'] +
                                     quality['surface_smoothness']) / 2

        # Quality category
        if quality['overall_quality'] > 0.7:
            quality['quality_category'] = 'high_finish'
        elif quality['overall_quality'] > 0.4:
            quality['quality_category'] = 'moderate_finish'
        else:
            quality['quality_category'] = 'rough'

        return quality

    def _analyze_shape_regularity(self, mesh) -> Dict:
        """
        Analyze overall shape regularity and craftsmanship.
        """
        vertices = mesh.vertices
        center = vertices.mean(axis=0)

        # Distance from center to all vertices
        distances = np.linalg.norm(vertices - center, axis=1)

        # Calculate radial uniformity with safe division
        mean_dist = np.mean(distances)
        if mean_dist > 0:
            radial_uniformity = float(1 - (np.std(distances) / mean_dist))
        else:
            radial_uniformity = 0.0

        regularity = {
            'radial_uniformity': radial_uniformity,
            'shape_consistency': float(np.percentile(distances, 75) - np.percentile(distances, 25))
        }

        # Convexity (how much volume vs convex hull)
        try:
            convex_hull = mesh.convex_hull
            if convex_hull.volume > 0:
                regularity['convexity'] = float(mesh.volume / convex_hull.volume)
            else:
                regularity['convexity'] = 1.0
        except:
            regularity['convexity'] = 1.0

        return regularity

    def _analyze_curvature(self, mesh) -> Dict:
        """
        Analyze surface curvature patterns.

        Different curvature patterns indicate different manufacturing techniques.
        """
        try:
            # Discrete mean curvature
            curvature = mesh.vertex_defects

            curv_analysis = {
                'mean_curvature': float(np.mean(np.abs(curvature))),
                'curvature_variation': float(np.std(curvature)),
                'max_curvature': float(np.max(np.abs(curvature))),
            }

            # Curvature distribution
            curv_abs = np.abs(curvature)
            curv_analysis['low_curvature_pct'] = float(np.sum(curv_abs < 0.1) / len(curv_abs))
            curv_analysis['high_curvature_pct'] = float(np.sum(curv_abs > 0.5) / len(curv_abs))

            return curv_analysis
        except:
            return {
                'mean_curvature': 0.0,
                'curvature_variation': 0.0,
                'max_curvature': 0.0
            }

    def compare_styles(self, artifact1_id: str, artifact2_id: str) -> Dict:
        """
        Compare stylistic features of two artifacts.

        Args:
            artifact1_id: First artifact
            artifact2_id: Second artifact

        Returns:
            Stylistic similarity scores
        """
        if artifact1_id not in self.style_database or artifact2_id not in self.style_database:
            return {'error': 'One or both artifacts not analyzed'}

        style1 = self.style_database[artifact1_id]
        style2 = self.style_database[artifact2_id]

        similarities = {}

        # Compare each category
        for category in ['symmetry', 'proportions', 'edge_profile', 'surface_quality', 'curvature']:
            if category in style1 and category in style2:
                cat_similarity = self._compare_category(style1[category], style2[category])
                similarities[category] = cat_similarity

        # Overall stylistic similarity
        if similarities:
            similarities['overall_style_similarity'] = np.mean(list(similarities.values()))

        return similarities

    def _compare_category(self, cat1: Dict, cat2: Dict) -> float:
        """Compare two feature categories."""
        scores = []

        for key in cat1:
            if key in cat2:
                val1 = cat1[key]
                val2 = cat2[key]

                # Skip non-numeric
                if not isinstance(val1, (int, float)) or not isinstance(val2, (int, float)):
                    continue

                # Compute normalized difference
                max_val = max(abs(val1), abs(val2), 1e-6)
                diff = abs(val1 - val2) / max_val
                similarity = max(0, 1 - diff)
                scores.append(similarity)

        return float(np.mean(scores)) if scores else 0.0

    def get_style_vector(self, artifact_id: str) -> np.ndarray:
        """
        Get flattened style feature vector for ML/similarity.

        Returns:
            Numpy array of all numeric style features
        """
        if artifact_id not in self.style_database:
            return np.array([])

        style = self.style_database[artifact_id]

        # Flatten all numeric values
        values = []
        for category in style.values():
            if isinstance(category, dict):
                for val in category.values():
                    if isinstance(val, (int, float)):
                        values.append(val)
            elif isinstance(category, (int, float)):
                values.append(category)

        return np.array(values)

    def find_stylistically_similar(self, artifact_id: str, n_results: int = 5) -> List[tuple]:
        """
        Find artifacts with similar style.

        Args:
            artifact_id: Query artifact
            n_results: Number of results to return

        Returns:
            List of (artifact_id, similarity_score) tuples
        """
        if artifact_id not in self.style_database:
            return []

        query_vector = self.get_style_vector(artifact_id)

        similarities = []
        for other_id in self.style_database:
            if other_id == artifact_id:
                continue

            other_vector = self.get_style_vector(other_id)

            # Cosine similarity
            if len(query_vector) > 0 and len(other_vector) > 0:
                dot_product = np.dot(query_vector, other_vector)
                norm_product = np.linalg.norm(query_vector) * np.linalg.norm(other_vector)

                if norm_product > 0:
                    similarity = dot_product / norm_product
                    similarities.append((other_id, float(similarity)))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:n_results]

    def export_styles(self, filepath: str):
        """Export stylistic database to JSON."""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.style_database, f, indent=2)

    def import_styles(self, filepath: str):
        """Import stylistic database from JSON."""
        import json
        with open(filepath, 'r') as f:
            self.style_database = json.load(f)


# Global instance
_stylistic_analyzer = None


def get_stylistic_analyzer() -> StylisticAnalyzer:
    """Get or create global stylistic analyzer."""
    global _stylistic_analyzer
    if _stylistic_analyzer is None:
        _stylistic_analyzer = StylisticAnalyzer()
    return _stylistic_analyzer
