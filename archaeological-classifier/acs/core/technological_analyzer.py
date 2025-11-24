"""
Technological Analysis Module
==============================

Analyzes manufacturing techniques, wear patterns, and production methods
from 3D mesh data of archaeological artifacts.
"""

import numpy as np
from typing import Dict, List, Optional
from scipy import ndimage
from scipy.spatial import cKDTree


class TechnologicalAnalyzer:
    """
    Analyzes technological features of archaeological artifacts.

    Focuses on:
    - Manufacturing techniques (casting, forging, hammering)
    - Wear patterns and usage traces
    - Surface treatment and finishing
    - Production methods and tool marks
    """

    def __init__(self):
        self.analysis_history = []

    def analyze_technology(self, mesh, artifact_id: str) -> Dict:
        """
        Comprehensive technological analysis.

        Args:
            mesh: Trimesh object
            artifact_id: Artifact identifier

        Returns:
            Dictionary of technological features
        """
        tech_features = {}

        # 1. Hammering and forging marks
        tech_features['hammering'] = self._detect_hammering_marks(mesh)

        # 2. Casting indicators
        tech_features['casting'] = self._detect_casting_features(mesh)

        # 3. Wear patterns
        tech_features['wear'] = self._analyze_wear_patterns(mesh)

        # 4. Surface treatment
        tech_features['surface_treatment'] = self._analyze_surface_treatment(mesh)

        # 5. Edge condition and sharpening
        tech_features['edge_analysis'] = self._analyze_edge_condition(mesh)

        # 6. Production technique inference
        tech_features['production_method'] = self._infer_production_method(tech_features)

        # Ensure all values are JSON-serializable
        tech_features = self._make_json_serializable(tech_features)

        return tech_features

    def _detect_hammering_marks(self, mesh) -> Dict:
        """
        Detect hammering marks from surface irregularities.

        Hammering creates characteristic patterns:
        - Local depressions/bumps
        - Regular spacing patterns
        - Directional orientation
        """
        vertices = mesh.vertices
        normals = mesh.vertex_normals

        # Calculate local surface variation
        tree = cKDTree(vertices)

        # Sample vertices for performance
        sample_size = min(2000, len(vertices))
        indices = np.random.choice(len(vertices), sample_size, replace=False)
        sampled_vertices = vertices[indices]

        local_variations = []
        for i, vertex in enumerate(sampled_vertices):
            # Find neighbors within radius
            neighbors_idx = tree.query_ball_point(vertex, r=5.0)

            if len(neighbors_idx) > 5:
                neighbor_points = vertices[neighbors_idx]
                # Calculate local planarity deviation
                centroid = neighbor_points.mean(axis=0)
                deviations = np.linalg.norm(neighbor_points - centroid, axis=1)
                local_variations.append(np.std(deviations))

        hammering = {
            'detected': False,
            'intensity': 0.0,
            'pattern_regularity': 0.0,
            'affected_area_pct': 0.0
        }

        if local_variations:
            variation_array = np.array(local_variations)
            mean_var = np.mean(variation_array)
            std_var = np.std(variation_array)

            # High variation suggests hammering
            if mean_var > 0.5:
                hammering['detected'] = True
                hammering['intensity'] = float(min(mean_var / 2.0, 1.0))

                # Calculate pattern regularity (regular spacing = intentional hammering)
                if std_var > 0:
                    hammering['pattern_regularity'] = float(1.0 - min(std_var / mean_var, 1.0))

                # Estimate affected area
                high_var_count = np.sum(variation_array > mean_var + std_var)
                hammering['affected_area_pct'] = float(high_var_count / len(variation_array))

        return hammering

    def _detect_casting_features(self, mesh) -> Dict:
        """
        Detect features typical of casting.

        Casting indicators:
        - Very smooth surfaces (no hammering marks)
        - Thin flash lines (mold seams)
        - Uniform wall thickness
        - Bubbles or porosity
        """
        vertices = mesh.vertices
        faces = mesh.faces

        # Calculate surface smoothness
        try:
            curvature = mesh.vertex_defects
            mean_curvature = np.mean(np.abs(curvature))
        except:
            mean_curvature = 0

        # Check for thin sharp lines (mold seams)
        edge_lengths = mesh.edges_unique_length
        very_thin_edges = np.sum(edge_lengths < 0.1)
        thin_edge_ratio = very_thin_edges / len(edge_lengths) if len(edge_lengths) > 0 else 0

        # Surface uniformity
        face_areas = mesh.area_faces
        area_uniformity = 1.0 - (np.std(face_areas) / np.mean(face_areas)) if np.mean(face_areas) > 0 else 0

        casting = {
            'likely_cast': False,
            'confidence': 0.0,
            'surface_smoothness': float(1.0 - min(mean_curvature, 1.0)),
            'mold_seam_probability': float(thin_edge_ratio),
            'uniformity': float(area_uniformity)
        }

        # Casting likelihood
        indicators = []
        if casting['surface_smoothness'] > 0.8:
            indicators.append(0.3)
        if casting['mold_seam_probability'] > 0.01:
            indicators.append(0.2)
        if casting['uniformity'] > 0.7:
            indicators.append(0.5)

        if indicators:
            casting['confidence'] = float(np.mean(indicators))
            casting['likely_cast'] = casting['confidence'] > 0.5

        return casting

    def _analyze_wear_patterns(self, mesh) -> Dict:
        """
        Analyze wear patterns and usage traces.

        Wear indicators:
        - Edge rounding/blunting
        - Localized smoothing
        - Asymmetric damage
        - Material loss patterns
        """
        vertices = mesh.vertices

        # Analyze edge regions (top 10% highest points)
        z_coords = vertices[:, 2]
        edge_threshold = np.percentile(z_coords, 90)
        edge_vertices = vertices[z_coords > edge_threshold]

        wear = {
            'detected': False,
            'severity': 'none',
            'type': 'unknown',
            'edge_rounding': 0.0,
            'asymmetric_wear': 0.0,
            'wear_location': 'unknown'
        }

        if len(edge_vertices) > 10:
            # Calculate edge sharpness
            # Sharp edge = high variance in small radius
            tree = cKDTree(edge_vertices)
            edge_sharpness_values = []

            sample_count = min(100, len(edge_vertices))
            for i in range(sample_count):
                idx = np.random.randint(len(edge_vertices))
                point = edge_vertices[idx]
                neighbors_idx = tree.query_ball_point(point, r=2.0)

                if len(neighbors_idx) > 3:
                    neighbor_points = edge_vertices[neighbors_idx]
                    z_variance = np.var(neighbor_points[:, 2])
                    edge_sharpness_values.append(z_variance)

            if edge_sharpness_values:
                mean_sharpness = np.mean(edge_sharpness_values)

                # Low variance = rounded/worn edge
                wear['edge_rounding'] = float(1.0 - min(mean_sharpness / 10.0, 1.0))

                if wear['edge_rounding'] > 0.6:
                    wear['detected'] = True
                    wear['severity'] = 'heavy' if wear['edge_rounding'] > 0.8 else 'moderate'
                    wear['type'] = 'edge_wear'

            # Check for asymmetric wear (one side more worn)
            left_edge = edge_vertices[edge_vertices[:, 0] < np.median(vertices[:, 0])]
            right_edge = edge_vertices[edge_vertices[:, 0] >= np.median(vertices[:, 0])]

            if len(left_edge) > 5 and len(right_edge) > 5:
                left_avg_height = np.mean(left_edge[:, 2])
                right_avg_height = np.mean(right_edge[:, 2])
                asymmetry = abs(left_avg_height - right_avg_height)
                wear['asymmetric_wear'] = float(min(asymmetry / 10.0, 1.0))

                if asymmetry > 2.0:
                    wear['wear_location'] = 'left_side' if left_avg_height < right_avg_height else 'right_side'

        return wear

    def _analyze_surface_treatment(self, mesh) -> Dict:
        """
        Analyze surface treatment and finishing techniques.

        Treatment types:
        - Polishing (very smooth)
        - Filing (parallel striations)
        - Grinding (random scratches)
        - Patination (uniform coating)
        """
        normals = mesh.face_normals
        vertices = mesh.vertices

        # Calculate normal coherence (smooth = polished)
        adjacency = mesh.face_adjacency
        normal_similarities = []

        if len(adjacency) > 0:
            sample_size = min(1000, len(adjacency))
            sample_indices = np.random.choice(len(adjacency), sample_size, replace=False)

            for idx in sample_indices:
                edge = adjacency[idx]
                n1 = normals[edge[0]]
                n2 = normals[edge[1]]
                similarity = np.dot(n1, n2)
                normal_similarities.append(abs(similarity))

        smoothness = np.mean(normal_similarities) if normal_similarities else 0

        treatment = {
            'type': 'unknown',
            'quality': 'rough',
            'smoothness_score': float(smoothness),
            'likely_polished': False,
            'finishing_marks': False
        }

        # Classify treatment
        if smoothness > 0.9:
            treatment['type'] = 'polished'
            treatment['quality'] = 'high'
            treatment['likely_polished'] = True
        elif smoothness > 0.7:
            treatment['type'] = 'smoothed'
            treatment['quality'] = 'medium'
        elif smoothness > 0.5:
            treatment['type'] = 'filed_or_ground'
            treatment['quality'] = 'medium'
            treatment['finishing_marks'] = True
        else:
            treatment['type'] = 'rough_finished'
            treatment['quality'] = 'low'

        return treatment

    def _analyze_edge_condition(self, mesh) -> Dict:
        """
        Detailed analysis of cutting edge condition.

        Important for Bronze Age tools:
        - Sharpness
        - Damage/nicks
        - Resharpening evidence
        - Usage wear
        """
        vertices = mesh.vertices

        # Find the cutting edge (typically highest Z)
        z_coords = vertices[:, 2]
        edge_threshold = np.percentile(z_coords, 95)
        edge_vertices = vertices[z_coords > edge_threshold]

        edge_condition = {
            'sharpness': 'unknown',
            'damage_level': 'none',
            'resharpened': False,
            'usable': True,
            'edge_angle_estimate': 0.0
        }

        if len(edge_vertices) > 10:
            # Calculate edge thickness (narrower = sharper)
            x_span = np.ptp(edge_vertices[:, 0])
            z_height = np.ptp(edge_vertices[:, 2])

            if z_height > 0:
                edge_angle = np.arctan(x_span / z_height) * 180 / np.pi
                edge_condition['edge_angle_estimate'] = float(edge_angle)

                # Classify sharpness
                if edge_angle < 20:
                    edge_condition['sharpness'] = 'very_sharp'
                elif edge_angle < 35:
                    edge_condition['sharpness'] = 'sharp'
                elif edge_angle < 50:
                    edge_condition['sharpness'] = 'moderate'
                else:
                    edge_condition['sharpness'] = 'blunt'
                    edge_condition['usable'] = edge_angle < 70

            # Check for damage (irregularities in edge line)
            edge_z = edge_vertices[:, 2]
            edge_irregularity = np.std(edge_z) / np.mean(edge_z) if np.mean(edge_z) > 0 else 0

            if edge_irregularity > 0.1:
                edge_condition['damage_level'] = 'heavy'
            elif edge_irregularity > 0.05:
                edge_condition['damage_level'] = 'moderate'
            elif edge_irregularity > 0.02:
                edge_condition['damage_level'] = 'light'

            # Resharpening evidence (very straight edge + sharp angle)
            if edge_irregularity < 0.02 and edge_angle < 30:
                edge_condition['resharpened'] = True

        return edge_condition

    def _infer_production_method(self, tech_features: Dict) -> Dict:
        """
        Infer overall production method from all features.

        Bronze Age techniques:
        - Lost-wax casting
        - Bivalve mold casting
        - Forging from ingot
        - Cold hammering
        - Combination techniques
        """
        hammering = tech_features.get('hammering', {})
        casting = tech_features.get('casting', {})
        treatment = tech_features.get('surface_treatment', {})

        production = {
            'primary_method': 'unknown',
            'confidence': 0.0,
            'secondary_methods': [],
            'technique_description': ''
        }

        # Decision tree based on features
        if casting.get('likely_cast', False) and casting.get('confidence', 0) > 0.6:
            production['primary_method'] = 'cast'
            production['confidence'] = casting['confidence']

            if hammering.get('detected', False):
                production['secondary_methods'].append('post-cast_hammering')
                production['technique_description'] = 'Cast in mold, then cold-hammered for finishing and hardening'
            else:
                production['technique_description'] = 'Cast in mold with minimal post-processing'

        elif hammering.get('detected', False) and hammering.get('intensity', 0) > 0.6:
            production['primary_method'] = 'forged'
            production['confidence'] = hammering['intensity']
            production['technique_description'] = 'Forged from ingot using hammering techniques'

            if treatment.get('likely_polished', False):
                production['secondary_methods'].append('polishing')

        elif treatment.get('likely_polished', False):
            production['primary_method'] = 'cast_and_polished'
            production['confidence'] = 0.7
            production['technique_description'] = 'Cast and extensively polished/finished'

        else:
            production['primary_method'] = 'uncertain'
            production['confidence'] = 0.3
            production['technique_description'] = 'Production method unclear from surface analysis'

        return production

    def _make_json_serializable(self, obj):
        """Convert NumPy types to Python native types for JSON serialization."""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, (np.integer, int)):
            return int(obj)
        elif isinstance(obj, (np.floating, float)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    def generate_technical_report(self, tech_features: Dict, artifact_id: str) -> str:
        """
        Generate human-readable technical report.

        Args:
            tech_features: Dictionary from analyze_technology()
            artifact_id: Artifact identifier

        Returns:
            Formatted technical report string
        """
        report = f"TECHNOLOGICAL ANALYSIS REPORT - {artifact_id}\n"
        report += "=" * 60 + "\n\n"

        # Production method
        prod = tech_features.get('production_method', {})
        report += f"PRODUCTION METHOD:\n"
        report += f"  Primary: {prod.get('primary_method', 'unknown').upper()}\n"
        report += f"  Confidence: {prod.get('confidence', 0)*100:.1f}%\n"
        if prod.get('secondary_methods'):
            report += f"  Secondary: {', '.join(prod.get('secondary_methods', []))}\n"
        report += f"  Description: {prod.get('technique_description', 'N/A')}\n\n"

        # Hammering (show always, with detected status)
        hammer = tech_features.get('hammering', {})
        report += f"HAMMERING MARKS:\n"
        report += f"  Detected: {'YES' if hammer.get('detected', False) else 'NO'}\n"
        report += f"  Intensity: {hammer.get('intensity', 0):.4f} (threshold: 0.60 for 'forged')\n"
        report += f"  Pattern regularity: {hammer.get('pattern_regularity', 0):.4f}\n"
        report += f"  Affected area: {hammer.get('affected_area_pct', 0)*100:.1f}%\n"
        if hammer.get('intensity', 0) > 0.5:
            report += f"  → Analysis: "
            if hammer.get('intensity', 0) >= 0.6:
                report += "Strong evidence of forging/hammering\n"
            else:
                report += "Moderate hammering (borderline - may be post-cast finishing)\n"
        report += "\n"

        # Casting
        casting = tech_features.get('casting', {})
        report += f"CASTING FEATURES:\n"
        report += f"  Likely cast: {'YES' if casting.get('likely_cast', False) else 'NO'}\n"
        report += f"  Confidence: {casting.get('confidence', 0):.4f} (threshold: 0.50)\n"
        report += f"  Surface smoothness: {casting.get('surface_smoothness', 0):.4f} (>0.80 = cast)\n"
        report += f"  Mold seam probability: {casting.get('mold_seam_probability', 0):.4f}\n"
        report += f"  Uniformity: {casting.get('uniformity', 0):.4f} (>0.70 = cast indicator)\n\n"

        # Wear
        wear = tech_features.get('wear', {})
        report += f"WEAR PATTERNS:\n"
        report += f"  Detected: {'YES' if wear.get('detected', False) else 'NO'}\n"
        report += f"  Severity: {wear.get('severity', 'none').upper()}\n"
        report += f"  Type: {wear.get('type', 'unknown')}\n"
        report += f"  Edge rounding: {wear.get('edge_rounding', 0):.4f} (>0.60 = worn)\n"
        report += f"  Asymmetric wear: {wear.get('asymmetric_wear', 0):.4f}\n"
        report += f"  Location: {wear.get('wear_location', 'unknown')}\n"
        if wear.get('edge_rounding', 0) > 0.8:
            report += f"  → Analysis: HEAVY WEAR - artifact extensively used/degraded\n"
        elif wear.get('edge_rounding', 0) > 0.6:
            report += f"  → Analysis: Moderate wear consistent with functional use\n"
        report += "\n"

        # Edge condition
        edge = tech_features.get('edge_analysis', {})
        report += f"EDGE CONDITION:\n"
        report += f"  Sharpness: {edge.get('sharpness', 'unknown').upper()}\n"
        report += f"  Damage: {edge.get('damage_level', 'none')}\n"
        report += f"  Estimated angle: {edge.get('edge_angle_estimate', 0):.2f}° (sharp <30°, usable <70°)\n"
        report += f"  Resharpened: {'YES' if edge.get('resharpened', False) else 'NO'}\n"
        report += f"  Usable: {'YES' if edge.get('usable', True) else 'NO'}\n"
        if not edge.get('usable', True):
            report += f"  → Analysis: Edge too degraded for functional use\n"
        elif edge.get('resharpened', False):
            report += f"  → Analysis: Evidence of maintenance/resharpening\n"
        report += "\n"

        # Surface treatment
        treatment = tech_features.get('surface_treatment', {})
        report += f"SURFACE TREATMENT:\n"
        report += f"  Type: {treatment.get('type', 'unknown')}\n"
        report += f"  Quality: {treatment.get('quality', 'unknown')}\n"
        report += f"  Smoothness score: {treatment.get('smoothness_score', 0):.4f} (>0.90 = polished)\n"
        report += f"  Polished: {'YES' if treatment.get('likely_polished', False) else 'NO'}\n"
        report += f"  Finishing marks: {'YES' if treatment.get('finishing_marks', False) else 'NO'}\n"

        return report

    def analyze_batch(self, meshes: Dict, artifact_ids: List[str]) -> Dict:
        """
        Analyze multiple artifacts and return batch results.

        Args:
            meshes: Dictionary of {artifact_id: mesh}
            artifact_ids: List of artifact IDs to analyze

        Returns:
            Dictionary with results for each artifact and summary statistics
        """
        results = {}
        all_features = []

        for artifact_id in artifact_ids:
            if artifact_id in meshes:
                try:
                    tech_features = self.analyze_technology(meshes[artifact_id], artifact_id)
                    results[artifact_id] = {
                        'status': 'success',
                        'features': tech_features
                    }
                    all_features.append(tech_features)
                except Exception as e:
                    results[artifact_id] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                results[artifact_id] = {
                    'status': 'error',
                    'error': 'Artifact not found'
                }

        # Calculate summary statistics
        summary = self._calculate_batch_summary(all_features)

        return {
            'total_analyzed': len(artifact_ids),
            'successful': len(all_features),
            'failed': len(artifact_ids) - len(all_features),
            'results': results,
            'summary': summary
        }

    def _calculate_batch_summary(self, all_features: List[Dict]) -> Dict:
        """Calculate summary statistics across multiple artifacts."""
        if not all_features:
            return {}

        summary = {
            'production_methods': {},
            'hammering_stats': {
                'detected_count': 0,
                'avg_intensity': 0.0,
                'max_intensity': 0.0
            },
            'casting_stats': {
                'likely_cast_count': 0,
                'avg_confidence': 0.0
            },
            'wear_stats': {
                'detected_count': 0,
                'heavy_count': 0,
                'avg_edge_rounding': 0.0
            },
            'edge_stats': {
                'sharp_count': 0,
                'usable_count': 0,
                'resharpened_count': 0,
                'avg_angle': 0.0
            }
        }

        # Collect stats
        intensities = []
        cast_confidences = []
        edge_roundings = []
        edge_angles = []

        for features in all_features:
            # Production method
            prod_method = features.get('production_method', {}).get('primary_method', 'unknown')
            summary['production_methods'][prod_method] = summary['production_methods'].get(prod_method, 0) + 1

            # Hammering
            hammer = features.get('hammering', {})
            if hammer.get('detected'):
                summary['hammering_stats']['detected_count'] += 1
            intensity = hammer.get('intensity', 0)
            intensities.append(intensity)
            summary['hammering_stats']['max_intensity'] = max(
                summary['hammering_stats']['max_intensity'], intensity
            )

            # Casting
            casting = features.get('casting', {})
            if casting.get('likely_cast'):
                summary['casting_stats']['likely_cast_count'] += 1
            cast_confidences.append(casting.get('confidence', 0))

            # Wear
            wear = features.get('wear', {})
            if wear.get('detected'):
                summary['wear_stats']['detected_count'] += 1
            if wear.get('severity') == 'heavy':
                summary['wear_stats']['heavy_count'] += 1
            edge_roundings.append(wear.get('edge_rounding', 0))

            # Edge
            edge = features.get('edge_analysis', {})
            if edge.get('sharpness') in ['very_sharp', 'sharp']:
                summary['edge_stats']['sharp_count'] += 1
            if edge.get('usable'):
                summary['edge_stats']['usable_count'] += 1
            if edge.get('resharpened'):
                summary['edge_stats']['resharpened_count'] += 1
            edge_angles.append(edge.get('edge_angle_estimate', 0))

        # Calculate averages
        n = len(all_features)
        summary['hammering_stats']['avg_intensity'] = sum(intensities) / n if n > 0 else 0
        summary['casting_stats']['avg_confidence'] = sum(cast_confidences) / n if n > 0 else 0
        summary['wear_stats']['avg_edge_rounding'] = sum(edge_roundings) / n if n > 0 else 0
        summary['edge_stats']['avg_angle'] = sum(edge_angles) / n if n > 0 else 0

        return summary

    def generate_batch_report(self, batch_results: Dict) -> str:
        """
        Generate comprehensive batch report.

        Args:
            batch_results: Results from analyze_batch()

        Returns:
            Formatted batch report string
        """
        report = "BATCH TECHNOLOGICAL ANALYSIS REPORT\n"
        report += "=" * 70 + "\n\n"

        report += f"OVERVIEW:\n"
        report += f"  Total artifacts: {batch_results['total_analyzed']}\n"
        report += f"  Successfully analyzed: {batch_results['successful']}\n"
        report += f"  Failed: {batch_results['failed']}\n\n"

        summary = batch_results.get('summary', {})
        if not summary:
            report += "No summary statistics available.\n"
            return report

        # Production methods distribution
        report += "PRODUCTION METHODS DISTRIBUTION:\n"
        prod_methods = summary.get('production_methods', {})
        for method, count in sorted(prod_methods.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / batch_results['successful']) * 100 if batch_results['successful'] > 0 else 0
            report += f"  {method.upper()}: {count} ({percentage:.1f}%)\n"
        report += "\n"

        # Hammering statistics
        hammer_stats = summary.get('hammering_stats', {})
        report += "HAMMERING STATISTICS:\n"
        report += f"  Artifacts with hammering: {hammer_stats.get('detected_count', 0)}\n"
        report += f"  Average intensity: {hammer_stats.get('avg_intensity', 0):.4f}\n"
        report += f"  Maximum intensity: {hammer_stats.get('max_intensity', 0):.4f}\n\n"

        # Casting statistics
        cast_stats = summary.get('casting_stats', {})
        report += "CASTING STATISTICS:\n"
        report += f"  Likely cast artifacts: {cast_stats.get('likely_cast_count', 0)}\n"
        report += f"  Average confidence: {cast_stats.get('avg_confidence', 0):.4f}\n\n"

        # Wear statistics
        wear_stats = summary.get('wear_stats', {})
        report += "WEAR STATISTICS:\n"
        report += f"  Artifacts with wear: {wear_stats.get('detected_count', 0)}\n"
        report += f"  Heavy wear: {wear_stats.get('heavy_count', 0)}\n"
        report += f"  Average edge rounding: {wear_stats.get('avg_edge_rounding', 0):.4f}\n\n"

        # Edge statistics
        edge_stats = summary.get('edge_stats', {})
        report += "EDGE CONDITION STATISTICS:\n"
        report += f"  Sharp edges: {edge_stats.get('sharp_count', 0)}\n"
        report += f"  Usable edges: {edge_stats.get('usable_count', 0)}\n"
        report += f"  Resharpened: {edge_stats.get('resharpened_count', 0)}\n"
        report += f"  Average edge angle: {edge_stats.get('avg_angle', 0):.2f}°\n\n"

        # Individual results summary
        report += "=" * 70 + "\n"
        report += "INDIVIDUAL ARTIFACTS:\n\n"

        for artifact_id, result in batch_results['results'].items():
            report += f"{artifact_id}:\n"
            if result['status'] == 'success':
                features = result['features']
                prod = features.get('production_method', {})
                report += f"  Method: {prod.get('primary_method', 'unknown').upper()} "
                report += f"(confidence: {prod.get('confidence', 0)*100:.1f}%)\n"

                hammer = features.get('hammering', {})
                report += f"  Hammering: {'YES' if hammer.get('detected') else 'NO'} "
                if hammer.get('detected'):
                    report += f"(intensity: {hammer.get('intensity', 0):.4f})\n"
                else:
                    report += "\n"

                wear = features.get('wear', {})
                if wear.get('detected'):
                    report += f"  Wear: {wear.get('severity', 'unknown').upper()} "
                    report += f"(rounding: {wear.get('edge_rounding', 0):.4f})\n"

                edge = features.get('edge_analysis', {})
                report += f"  Edge: {edge.get('sharpness', 'unknown').upper()} "
                report += f"({edge.get('edge_angle_estimate', 0):.1f}°)\n"
            else:
                report += f"  Status: FAILED - {result.get('error', 'Unknown error')}\n"
            report += "\n"

        return report

    def export_batch_csv(self, batch_results: Dict) -> str:
        """Export batch results as CSV format."""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'artifact_id', 'status', 'production_method', 'production_confidence',
            'hammering_detected', 'hammering_intensity', 'casting_likely', 'casting_confidence',
            'wear_detected', 'wear_severity', 'edge_rounding', 'edge_sharpness',
            'edge_angle', 'edge_usable', 'surface_smoothness'
        ])

        # Data rows
        for artifact_id, result in batch_results['results'].items():
            if result['status'] == 'success':
                features = result['features']
                prod = features.get('production_method', {})
                hammer = features.get('hammering', {})
                casting = features.get('casting', {})
                wear = features.get('wear', {})
                edge = features.get('edge_analysis', {})
                surface = features.get('surface_treatment', {})

                writer.writerow([
                    artifact_id,
                    'success',
                    prod.get('primary_method', ''),
                    f"{prod.get('confidence', 0):.4f}",
                    'yes' if hammer.get('detected') else 'no',
                    f"{hammer.get('intensity', 0):.4f}",
                    'yes' if casting.get('likely_cast') else 'no',
                    f"{casting.get('confidence', 0):.4f}",
                    'yes' if wear.get('detected') else 'no',
                    wear.get('severity', ''),
                    f"{wear.get('edge_rounding', 0):.4f}",
                    edge.get('sharpness', ''),
                    f"{edge.get('edge_angle_estimate', 0):.2f}",
                    'yes' if edge.get('usable') else 'no',
                    f"{surface.get('smoothness_score', 0):.4f}"
                ])
            else:
                writer.writerow([artifact_id, 'failed', '', '', '', '', '', '', '', '', '', '', '', '', ''])

        return output.getvalue()


# Global instance
_technological_analyzer = None


def get_technological_analyzer() -> TechnologicalAnalyzer:
    """Get or create global technological analyzer."""
    global _technological_analyzer
    if _technological_analyzer is None:
        _technological_analyzer = TechnologicalAnalyzer()
    return _technological_analyzer
