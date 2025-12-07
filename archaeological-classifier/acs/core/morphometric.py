"""
Morphometric Analysis Module
===========================

Advanced morphometric analysis including:
- Elliptic Fourier Analysis (EFA)
- Principal Component Analysis (PCA)
- Procrustes superimposition
- Hierarchical clustering
- Similarity metrics
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.spatial import procrustes
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler


class MorphometricAnalyzer:
    """Advanced morphometric analysis for archaeological artifacts."""

    def __init__(self):
        """Initialize morphometric analyzer."""
        self.features: Dict[str, np.ndarray] = {}
        self.features_dict: Dict[str, Dict[str, float]] = {}  # Store as dicts for normalization
        self.pca_model: Optional[PCA] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: Optional[List[str]] = None
        self._normalized = False

    def add_features(self, artifact_id: str, features: Dict):
        """
        Add feature vector for an artifact.

        Args:
            artifact_id: Unique artifact identifier
            features: Dictionary of numeric features (may include 'savignano' sub-dict)
        """
        # Extract numeric features only
        numeric_features = {}

        for k, v in features.items():
            if k == 'id':
                continue

            # Handle Savignano sub-dictionary
            if k == 'savignano' and isinstance(v, dict):
                # Extract numeric Savignano features with 'sav_' prefix
                for sav_key, sav_val in v.items():
                    if isinstance(sav_val, (int, float, bool)):
                        # Convert booleans to 0/1
                        if isinstance(sav_val, bool):
                            numeric_features[f'sav_{sav_key}'] = float(sav_val)
                        else:
                            numeric_features[f'sav_{sav_key}'] = float(sav_val)

            # Regular numeric features
            elif isinstance(v, (int, float)):
                numeric_features[k] = float(v)

        # Store as dictionary for later normalization
        self.features_dict[artifact_id] = numeric_features
        self._normalized = False

    def _normalize_features(self):
        """
        Normalize all feature vectors to use the same set of features.
        Missing features are filled with 0.
        """
        if self._normalized and self.feature_names is not None:
            return

        # Collect all unique feature names across all artifacts
        all_feature_names = set()
        for feat_dict in self.features_dict.values():
            all_feature_names.update(feat_dict.keys())

        # Sort for consistent ordering
        self.feature_names = sorted(list(all_feature_names))

        # Create normalized feature vectors
        self.features = {}
        for artifact_id, feat_dict in self.features_dict.items():
            # Create vector with all features, filling missing with 0
            feature_vector = np.array([
                feat_dict.get(fname, 0.0) for fname in self.feature_names
            ])
            self.features[artifact_id] = feature_vector

        self._normalized = True

    def fit_pca(
        self,
        n_components: Optional[int] = None,
        explained_variance: float = 0.95
    ) -> Dict:
        """
        Fit PCA model on all features.

        Args:
            n_components: Number of components (if None, use explained_variance)
            explained_variance: Target cumulative explained variance

        Returns:
            Dictionary with PCA results including full component analysis
        """
        # Normalize features to common set before analysis
        self._normalize_features()

        if len(self.features) < 2:
            raise ValueError("Need at least 2 artifacts for PCA")

        # Stack features
        artifact_ids = list(self.features.keys())
        X = np.vstack([self.features[aid] for aid in artifact_ids])

        # Standardize
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Fit FULL PCA first to analyze ALL possible components
        pca_full = PCA()
        pca_full.fit(X_scaled)
        full_variance_ratio = pca_full.explained_variance_ratio_
        full_cumsum = np.cumsum(full_variance_ratio)
        eigenvalues = pca_full.explained_variance_

        # Get feature names
        feature_names = getattr(self, 'feature_names', None) or [f'feature_{i}' for i in range(X.shape[1])]

        # ============ BUILD ALL COMPONENTS TABLE ============
        # This shows ALL possible components before selection
        all_components_analysis = []
        kaiser_threshold = 1.0  # Eigenvalue > 1 rule

        for i in range(len(full_variance_ratio)):
            # Get top features for this component (from full PCA)
            component = pca_full.components_[i]
            sorted_indices = np.argsort(np.abs(component))[::-1]
            top_features = []
            for idx in sorted_indices[:3]:
                if idx < len(feature_names):
                    top_features.append({
                        'name': feature_names[idx],
                        'loading': float(component[idx])
                    })

            all_components_analysis.append({
                'pc': i + 1,
                'eigenvalue': float(eigenvalues[i]),
                'variance_percent': float(full_variance_ratio[i] * 100),
                'cumulative_percent': float(full_cumsum[i] * 100),
                'passes_kaiser': bool(eigenvalues[i] > kaiser_threshold),
                'top_features': top_features
            })

        # ============ DETERMINE SELECTION ============
        selection_method = 'user_specified'
        selection_reason = ""

        if n_components is None:
            # Calculate different criteria
            kaiser_components = int(np.sum(eigenvalues > kaiser_threshold))
            variance_components = int(np.argmax(full_cumsum >= explained_variance) + 1)

            # Elbow method: find where adding more components gives diminishing returns
            variance_diffs = np.diff(full_variance_ratio)
            if len(variance_diffs) > 1:
                # Find where the drop becomes less than 2% of total variance
                elbow_idx = np.argmax(variance_diffs > -0.02) + 1
                elbow_components = max(2, min(elbow_idx, len(full_variance_ratio)))
            else:
                elbow_components = 1

            # Use explained variance as primary criterion
            n_components = variance_components
            selection_method = 'explained_variance'

            selection_reason = (
                f"Sono stati valutati 3 criteri di selezione:\n\n"
                f"1. CRITERIO VARIANZA ({explained_variance*100:.0f}%): {variance_components} componenti\n"
                f"   → Seleziona il minimo numero di PC che spiega almeno il {explained_variance*100:.0f}% della varianza\n\n"
                f"2. CRITERIO KAISER (eigenvalue > 1): {kaiser_components} componenti\n"
                f"   → Mantiene solo le PC con autovalore > 1 (varianza > media)\n\n"
                f"3. CRITERIO GOMITO: ~{elbow_components} componenti\n"
                f"   → Punto dove l'aggiunta di nuove PC non aggiunge varianza significativa\n\n"
                f"DECISIONE: Selezionate {n_components} componenti usando il criterio varianza ({explained_variance*100:.0f}%).\n"
                f"Questo criterio è preferito perché garantisce di mantenere una quantità definita di informazione."
            )
        else:
            selection_reason = (
                f"Numero di componenti specificato manualmente: {n_components}\n\n"
                f"Con {n_components} componenti si spiega il {full_cumsum[n_components-1]*100:.1f}% della varianza totale."
            )

        # ============ MARK SELECTED VS REJECTED ============
        for comp in all_components_analysis:
            pc_num = comp['pc']
            is_selected = pc_num <= n_components
            comp['selected'] = is_selected

            if is_selected:
                if pc_num == 1:
                    comp['selection_reason'] = (
                        f"✅ SELEZIONATA: PC1 è sempre la più importante, spiega il {comp['variance_percent']:.1f}% "
                        f"della varianza totale. Rappresenta il pattern di variazione principale."
                    )
                else:
                    prev_cumsum = full_cumsum[pc_num - 2] * 100 if pc_num > 1 else 0
                    comp['selection_reason'] = (
                        f"✅ SELEZIONATA: PC{pc_num} aggiunge {comp['variance_percent']:.1f}% di varianza "
                        f"(cumulativo: {comp['cumulative_percent']:.1f}%). "
                        f"Ancora sotto la soglia target del {explained_variance*100:.0f}%."
                    )
            else:
                comp['selection_reason'] = (
                    f"❌ ESCLUSA: PC{pc_num} spiega solo {comp['variance_percent']:.1f}% di varianza. "
                    f"Il target del {explained_variance*100:.0f}% è già raggiunto con le prime {n_components} componenti "
                    f"({full_cumsum[n_components-1]*100:.1f}%)."
                )

        # ============ FIT FINAL MODEL WITH SELECTED COMPONENTS ============
        self.pca_model = PCA(n_components=n_components)
        X_pca = self.pca_model.fit_transform(X_scaled)

        # Detailed analysis of SELECTED components
        selected_components_detail = []
        for i, component in enumerate(self.pca_model.components_):
            sorted_indices = np.argsort(np.abs(component))[::-1]
            top_features = []
            for idx in sorted_indices[:5]:
                if idx < len(feature_names):
                    loading = float(component[idx])
                    top_features.append({
                        'name': feature_names[idx],
                        'loading': loading,
                        'importance': float(abs(loading)),
                        'direction': 'positivo' if loading > 0 else 'negativo'
                    })

            pc_interpretation = self._interpret_component(i + 1, top_features)

            selected_components_detail.append({
                'pc': i + 1,
                'variance_explained': float(self.pca_model.explained_variance_ratio_[i]),
                'variance_percent': float(self.pca_model.explained_variance_ratio_[i] * 100),
                'cumulative_variance_percent': float(full_cumsum[i] * 100),
                'top_features': top_features,
                'interpretation': pc_interpretation,
                'why_selected': all_components_analysis[i]['selection_reason']
            })

        # ============ BUILD COMPREHENSIVE RESULT ============
        return {
            'n_components': n_components,
            'total_possible_components': len(full_variance_ratio),

            # All components table (for understanding what was available)
            'all_components': all_components_analysis,

            # Selection explanation
            'selection': {
                'method': selection_method,
                'target_variance': explained_variance,
                'achieved_variance': float(full_cumsum[n_components - 1]),
                'total_features': X.shape[1],
                'reduced_to': n_components,
                'reduction_ratio': f"{X.shape[1]} features → {n_components} PC ({(1 - n_components/X.shape[1])*100:.1f}% riduzione dimensionale)",
                'selection_reasoning': selection_reason
            },

            # Detailed analysis of selected components
            'component_features': selected_components_detail,

            # Data for visualization
            'explained_variance_ratio': self.pca_model.explained_variance_ratio_.tolist(),
            'cumulative_variance': full_cumsum[:n_components].tolist(),
            'full_cumulative_variance': full_cumsum.tolist(),
            'eigenvalues': eigenvalues.tolist(),
            'components': X_pca.tolist(),
            'artifact_ids': artifact_ids,
            'loadings': self.pca_model.components_.tolist(),
            'feature_names': feature_names,
            'n_artifacts': len(artifact_ids)
        }

    def _interpret_component(self, pc_num: int, top_features: list) -> str:
        """Generate human-readable interpretation for a principal component."""
        if not top_features:
            return "Componente non interpretabile"

        # Get the dominant features
        dominant = top_features[:3]
        feature_names = [f['name'] for f in dominant]

        # Check for common patterns
        size_features = ['length', 'width', 'height', 'area', 'volume', 'perimeter']
        shape_features = ['ratio', 'aspect', 'circularity', 'elongation', 'compactness']
        position_features = ['centroid', 'center', 'position', 'offset']

        has_size = any(any(sf in fn.lower() for sf in size_features) for fn in feature_names)
        has_shape = any(any(sf in fn.lower() for sf in shape_features) for fn in feature_names)

        if has_size and not has_shape:
            return f"PC{pc_num}: Dimensioni generali (features dominanti: {', '.join(feature_names[:2])})"
        elif has_shape and not has_size:
            return f"PC{pc_num}: Forma/proporzioni (features dominanti: {', '.join(feature_names[:2])})"
        elif has_size and has_shape:
            return f"PC{pc_num}: Dimensioni e forma combinate (features dominanti: {', '.join(feature_names[:2])})"
        else:
            return f"PC{pc_num}: Variazione morfometrica (features dominanti: {', '.join(feature_names[:2])})"

    def _get_selection_explanation(self, method: str, target_variance: float,
                                    n_components: int, total_features: int,
                                    cumsum: np.ndarray) -> str:
        """Generate detailed explanation of component selection criteria."""
        if method == 'user_specified':
            return (
                f"Numero di componenti specificato dall'utente: {n_components}. "
                f"Queste {n_components} componenti spiegano il {cumsum[n_components-1]*100:.1f}% "
                f"della varianza totale dei {total_features} features originali."
            )
        elif method == 'explained_variance':
            return (
                f"Criterio di selezione: Varianza spiegata cumulativa ≥ {target_variance*100:.0f}%.\n\n"
                f"Il PCA ha identificato che {n_components} componenti principali sono sufficienti "
                f"per catturare il {cumsum[n_components-1]*100:.1f}% della variabilità presente "
                f"nei {total_features} features morfometrici originali.\n\n"
                f"Questo significa che la complessità dei dati è stata ridotta da {total_features} "
                f"dimensioni a sole {n_components}, mantenendo quasi tutta l'informazione utile.\n\n"
                f"Interpretazione pratica: Le prime {n_components} componenti rappresentano "
                f"i pattern di variazione più importanti negli artefatti analizzati."
            )
        else:
            return f"Metodo di selezione: {method}"

    def transform_pca(self, features: Dict) -> np.ndarray:
        """Transform new features using fitted PCA model."""
        if self.pca_model is None or self.scaler is None:
            raise ValueError("PCA model not fitted. Call fit_pca() first.")

        # Extract numeric features
        numeric_features = {
            k: v for k, v in features.items()
            if isinstance(v, (int, float)) and k != 'id'
        }

        X = np.array(list(numeric_features.values())).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        X_pca = self.pca_model.transform(X_scaled)

        return X_pca[0]

    def hierarchical_clustering(
        self,
        n_clusters: Optional[int] = None,
        method: str = 'ward',
        distance_threshold: Optional[float] = None
    ) -> Dict:
        """
        Perform hierarchical clustering on artifacts.

        Args:
            n_clusters: Number of clusters (if None, use distance_threshold)
            method: Linkage method ('ward', 'complete', 'average')
            distance_threshold: Distance threshold for clustering

        Returns:
            Dictionary with clustering results
        """
        # Normalize features to common set before analysis
        self._normalize_features()

        if len(self.features) < 2:
            raise ValueError("Need at least 2 artifacts for clustering")

        # Get feature matrix
        artifact_ids = list(self.features.keys())
        X = np.vstack([self.features[aid] for aid in artifact_ids])

        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Clustering
        if n_clusters is not None:
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage=method
            )
        else:
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=distance_threshold,
                linkage=method
            )

        labels = clustering.fit_predict(X_scaled)

        # Get feature names
        feature_names = getattr(self, 'feature_names', None) or [f'feature_{i}' for i in range(X.shape[1])]

        # Organize by cluster with statistics
        clusters = {}
        cluster_stats = {}

        for artifact_id, label in zip(artifact_ids, labels):
            label = int(label)
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(artifact_id)

        # Calculate cluster characteristics
        for label, members in clusters.items():
            # Get feature vectors for cluster members
            member_features = np.array([self.features[aid] for aid in members])
            mean_features = np.mean(member_features, axis=0)
            std_features = np.std(member_features, axis=0)

            # Find distinguishing features (highest mean values relative to overall)
            overall_mean = np.mean(X, axis=0)
            overall_std = np.std(X, axis=0) + 1e-6  # Avoid division by zero
            z_scores = (mean_features - overall_mean) / overall_std

            # Top distinguishing features
            sorted_indices = np.argsort(np.abs(z_scores))[::-1]
            distinguishing_features = []
            for idx in sorted_indices[:5]:
                if idx < len(feature_names):
                    distinguishing_features.append({
                        'name': feature_names[idx],
                        'cluster_mean': float(mean_features[idx]),
                        'overall_mean': float(overall_mean[idx]),
                        'z_score': float(z_scores[idx]),
                        'direction': 'alto' if z_scores[idx] > 0 else 'basso'
                    })

            cluster_stats[label] = {
                'n_members': len(members),
                'members': members,
                'distinguishing_features': distinguishing_features
            }

        return {
            'n_clusters': len(clusters),
            'clusters': clusters,
            'cluster_stats': cluster_stats,
            'labels': {aid: int(label) for aid, label in zip(artifact_ids, labels)},
            'method': method,
            'feature_names': feature_names,
            'n_artifacts': len(artifact_ids)
        }

    def dbscan_clustering(
        self,
        eps: float = 0.5,
        min_samples: int = 3
    ) -> Dict:
        """
        Perform DBSCAN clustering (density-based).

        Args:
            eps: Maximum distance between samples
            min_samples: Minimum samples in neighborhood

        Returns:
            Dictionary with clustering results
        """
        # Normalize features to common set before analysis
        self._normalize_features()

        if len(self.features) < min_samples:
            raise ValueError(f"Need at least {min_samples} artifacts for DBSCAN")

        # Get feature matrix
        artifact_ids = list(self.features.keys())
        X = np.vstack([self.features[aid] for aid in artifact_ids])

        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # DBSCAN
        clustering = DBSCAN(eps=eps, min_samples=min_samples)
        labels = clustering.fit_predict(X_scaled)

        # Organize by cluster (-1 = noise)
        clusters = {}
        noise = []

        for artifact_id, label in zip(artifact_ids, labels):
            label = int(label)
            if label == -1:
                noise.append(artifact_id)
            else:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(artifact_id)

        return {
            'n_clusters': len(clusters),
            'clusters': clusters,
            'noise': noise,
            'labels': {aid: int(label) for aid, label in zip(artifact_ids, labels)}
        }

    def compute_similarity_matrix(
        self,
        metric: str = 'euclidean'
    ) -> Dict:
        """
        Compute pairwise similarity matrix.

        Args:
            metric: Distance metric ('euclidean', 'cosine', 'manhattan')

        Returns:
            Dictionary with similarity matrix and artifact IDs
        """
        from scipy.spatial.distance import pdist, squareform

        # Normalize features to common set before analysis
        self._normalize_features()

        artifact_ids = list(self.features.keys())
        X = np.vstack([self.features[aid] for aid in artifact_ids])

        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Compute distances
        distances = pdist(X_scaled, metric=metric)
        distance_matrix = squareform(distances)

        # Convert to similarity (1 / (1 + distance))
        similarity_matrix = 1 / (1 + distance_matrix)

        return {
            'similarity_matrix': similarity_matrix.tolist(),
            'distance_matrix': distance_matrix.tolist(),
            'artifact_ids': artifact_ids,
            'metric': metric
        }

    def find_most_similar(
        self,
        query_id: str,
        n: int = 5,
        metric: str = 'euclidean'
    ) -> List[Tuple[str, float]]:
        """
        Find n most similar artifacts to query.

        Args:
            query_id: Query artifact ID
            n: Number of similar artifacts to return
            metric: Distance metric

        Returns:
            List of (artifact_id, similarity_score) tuples
        """
        from scipy.spatial.distance import cdist

        # Normalize features to common set before analysis
        self._normalize_features()

        if query_id not in self.features:
            raise ValueError(f"Query artifact {query_id} not found")

        query_features = self.features[query_id].reshape(1, -1)

        # Compute distances to all others
        similarities = []
        for artifact_id, features in self.features.items():
            if artifact_id == query_id:
                continue

            target_features = features.reshape(1, -1)
            distance = cdist(query_features, target_features, metric=metric)[0, 0]
            similarity = 1 / (1 + distance)
            similarities.append((artifact_id, float(similarity)))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:n]

    def procrustes_alignment(
        self,
        artifact_ids: List[str]
    ) -> Dict:
        """
        Perform Procrustes superimposition on selected artifacts.

        Args:
            artifact_ids: List of artifact IDs to align

        Returns:
            Dictionary with aligned coordinates and disparity
        """
        if len(artifact_ids) < 2:
            raise ValueError("Need at least 2 artifacts for Procrustes")

        # Normalize features to common set before analysis
        self._normalize_features()

        # Get feature matrices
        matrices = [self.features[aid] for aid in artifact_ids]

        # Use first as reference
        reference = matrices[0]
        aligned = [reference]
        disparities = []

        for matrix in matrices[1:]:
            # Ensure same shape
            if matrix.shape != reference.shape:
                raise ValueError("All feature vectors must have same dimensions")

            # Procrustes alignment
            mtx1, mtx2, disparity = procrustes(reference, matrix)
            aligned.append(mtx2)
            disparities.append(float(disparity))

        return {
            'aligned_features': [a.tolist() for a in aligned],
            'disparities': disparities,
            'mean_disparity': float(np.mean(disparities)),
            'artifact_ids': artifact_ids
        }

    def elliptic_fourier_analysis(
        self,
        contour: np.ndarray,
        n_harmonics: int = 10
    ) -> np.ndarray:
        """
        Perform Elliptic Fourier Analysis on a 2D contour.

        Args:
            contour: Nx2 array of contour points
            n_harmonics: Number of Fourier harmonics

        Returns:
            EFA coefficients array
        """
        try:
            from pyefd import elliptic_fourier_descriptors
            coeffs = elliptic_fourier_descriptors(
                contour,
                order=n_harmonics,
                normalize=True
            )
            return coeffs
        except ImportError:
            raise ImportError(
                "pyefd is required for EFA. "
                "Install with: pip install pyefd"
            )

    def get_feature_statistics(self) -> Dict:
        """
        Compute statistics across all features.

        Returns:
            Dictionary with mean, std, min, max for each feature
        """
        if len(self.features_dict) == 0:
            return {}

        # Normalize features to common set before analysis
        self._normalize_features()

        artifact_ids = list(self.features.keys())
        X = np.vstack([self.features[aid] for aid in artifact_ids])

        stats = {
            'n_artifacts': len(artifact_ids),
            'n_features': X.shape[1],
            'mean': np.mean(X, axis=0).tolist(),
            'std': np.std(X, axis=0).tolist(),
            'min': np.min(X, axis=0).tolist(),
            'max': np.max(X, axis=0).tolist(),
            'median': np.median(X, axis=0).tolist()
        }

        return stats
