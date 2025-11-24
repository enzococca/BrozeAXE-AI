"""
Similarity Search & Batch Comparison
====================================

Find similar artifacts based on morphometric and stylistic features.
Supports 1:many comparisons and batch processing.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances


class SimilaritySearchEngine:
    """
    Engine for finding similar artifacts using combined features.

    Supports:
    - Morphometric similarity
    - Stylistic similarity
    - Combined multi-feature similarity
    - Batch comparisons (1:many)
    """

    def __init__(self):
        self.feature_database = {}  # artifact_id -> combined features
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_fitted = False

    def add_artifact_features(self, artifact_id: str,
                              morphometric: Dict = None,
                              stylistic: Dict = None):
        """
        Add artifact to search index.

        Args:
            artifact_id: Artifact identifier
            morphometric: Morphometric features dict
            stylistic: Stylistic features dict
        """
        combined = {}

        # Add morphometric features
        if morphometric:
            for key, val in morphometric.items():
                if isinstance(val, (int, float)):
                    combined[f'morph_{key}'] = val

        # Add stylistic features (flattened)
        if stylistic:
            combined.update(self._flatten_stylistic(stylistic))

        self.feature_database[artifact_id] = combined

    def _flatten_stylistic(self, stylistic: Dict) -> Dict:
        """Flatten nested stylistic features."""
        flattened = {}

        for category, features in stylistic.items():
            if isinstance(features, dict):
                for key, val in features.items():
                    if isinstance(val, (int, float)):
                        flattened[f'style_{category}_{key}'] = val
            elif isinstance(features, (int, float)):
                flattened[f'style_{category}'] = features

        return flattened

    def build_index(self):
        """
        Build search index from all added artifacts.

        This prepares the feature matrix and fits the scaler.
        """
        if not self.feature_database:
            raise ValueError("No artifacts added to index")

        # Get all feature names (union of all artifacts)
        all_features = set()
        for features in self.feature_database.values():
            all_features.update(features.keys())

        self.feature_names = sorted(list(all_features))

        # Build feature matrix
        artifact_ids = list(self.feature_database.keys())
        X = []

        for aid in artifact_ids:
            features = self.feature_database[aid]
            vector = [features.get(fname, 0.0) for fname in self.feature_names]
            X.append(vector)

        X = np.array(X)

        # Fit scaler
        self.scaler.fit(X)
        self.is_fitted = True

    def find_similar(self, query_id: str, n_results: int = 10,
                    metric: str = 'cosine',
                    min_similarity: float = 0.0) -> List[Tuple[str, float]]:
        """
        Find similar artifacts to query.

        Args:
            query_id: Query artifact ID
            n_results: Number of results to return
            metric: 'cosine' or 'euclidean'
            min_similarity: Minimum similarity threshold

        Returns:
            List of (artifact_id, similarity_score) tuples, sorted by similarity
        """
        if not self.is_fitted:
            self.build_index()

        if query_id not in self.feature_database:
            return []

        # Get query vector
        query_features = self.feature_database[query_id]
        query_vector = np.array([query_features.get(fname, 0.0)
                                for fname in self.feature_names]).reshape(1, -1)

        # Scale
        query_scaled = self.scaler.transform(query_vector)

        # Get all vectors
        artifact_ids = list(self.feature_database.keys())
        X = []
        for aid in artifact_ids:
            features = self.feature_database[aid]
            vector = [features.get(fname, 0.0) for fname in self.feature_names]
            X.append(vector)

        X = np.array(X)
        X_scaled = self.scaler.transform(X)

        # Compute similarities
        if metric == 'cosine':
            similarities = cosine_similarity(query_scaled, X_scaled)[0]
        elif metric == 'euclidean':
            distances = euclidean_distances(query_scaled, X_scaled)[0]
            # Convert distances to similarities (0-1 range)
            max_dist = np.max(distances)
            similarities = 1 - (distances / max_dist) if max_dist > 0 else np.ones_like(distances)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        # Create results
        results = []
        all_sims = []  # For debugging
        for i, aid in enumerate(artifact_ids):
            if aid == query_id:  # Skip self
                continue
            sim = float(similarities[i])
            all_sims.append((aid, sim))
            if sim >= min_similarity:
                results.append((aid, sim))

        # DEBUG: Print all similarities
        print(f"\n=== SIMILARITY SEARCH DEBUG ===")
        print(f"Query: {query_id}")
        print(f"Min similarity threshold: {min_similarity}")
        print(f"All similarities (top 10):")
        all_sims.sort(key=lambda x: x[1], reverse=True)
        for aid, sim in all_sims[:10]:
            print(f"  {aid}: {sim:.4f} {'✓' if sim >= min_similarity else '✗'}")
        print(f"Results passing threshold: {len(results)}")
        print(f"=== END DEBUG ===\n")

        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:n_results]

    def batch_compare(self, query_id: str, target_ids: List[str],
                     metric: str = 'cosine') -> List[Tuple[str, float]]:
        """
        Compare one artifact to many targets.

        Args:
            query_id: Query artifact
            target_ids: List of target artifact IDs
            metric: Similarity metric

        Returns:
            List of (artifact_id, similarity_score) tuples
        """
        if not self.is_fitted:
            self.build_index()

        if query_id not in self.feature_database:
            return []

        # Filter targets
        valid_targets = [tid for tid in target_ids if tid in self.feature_database]

        if not valid_targets:
            return []

        # Get query vector
        query_features = self.feature_database[query_id]
        query_vector = np.array([query_features.get(fname, 0.0)
                                for fname in self.feature_names]).reshape(1, -1)
        query_scaled = self.scaler.transform(query_vector)

        # Get target vectors
        X = []
        for tid in valid_targets:
            features = self.feature_database[tid]
            vector = [features.get(fname, 0.0) for fname in self.feature_names]
            X.append(vector)

        X = np.array(X)
        X_scaled = self.scaler.transform(X)

        # Compute similarities
        if metric == 'cosine':
            similarities = cosine_similarity(query_scaled, X_scaled)[0]
        elif metric == 'euclidean':
            distances = euclidean_distances(query_scaled, X_scaled)[0]
            max_dist = np.max(distances)
            similarities = 1 - (distances / max_dist) if max_dist > 0 else np.ones_like(distances)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        # Create results
        results = [(valid_targets[i], float(similarities[i]))
                  for i in range(len(valid_targets))]

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def find_clusters(self, n_clusters: int = 5) -> Dict[int, List[str]]:
        """
        Automatically find clusters of similar artifacts.

        Args:
            n_clusters: Number of clusters

        Returns:
            Dict mapping cluster_id -> list of artifact_ids
        """
        if not self.is_fitted:
            self.build_index()

        from sklearn.cluster import KMeans

        # Get all vectors
        artifact_ids = list(self.feature_database.keys())
        X = []
        for aid in artifact_ids:
            features = self.feature_database[aid]
            vector = [features.get(fname, 0.0) for fname in self.feature_names]
            X.append(vector)

        X = np.array(X)
        X_scaled = self.scaler.transform(X)

        # Cluster
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        # Group by cluster
        clusters = {}
        for aid, label in zip(artifact_ids, labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(aid)

        return clusters

    def get_feature_importance(self, query_id: str, target_id: str) -> Dict[str, float]:
        """
        Get which features are most important in similarity.

        Args:
            query_id: Query artifact
            target_id: Target artifact

        Returns:
            Dict of feature_name -> importance score
        """
        if query_id not in self.feature_database or target_id not in self.feature_database:
            return {}

        query_features = self.feature_database[query_id]
        target_features = self.feature_database[target_id]

        importance = {}

        for fname in self.feature_names:
            q_val = query_features.get(fname, 0.0)
            t_val = target_features.get(fname, 0.0)

            # Feature similarity (1 = identical, 0 = very different)
            max_val = max(abs(q_val), abs(t_val), 1e-6)
            diff = abs(q_val - t_val)
            similarity = max(0, 1 - (diff / max_val))

            importance[fname] = float(similarity)

        # Sort by importance
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        return importance

    def get_statistics(self) -> Dict:
        """Get statistics about the search index."""
        return {
            'n_artifacts': len(self.feature_database),
            'n_features': len(self.feature_names),
            'is_fitted': self.is_fitted,
            'feature_names': self.feature_names[:20]  # First 20
        }


# Global instance
_similarity_engine = None


def get_similarity_engine() -> SimilaritySearchEngine:
    """Get or create global similarity search engine."""
    global _similarity_engine
    if _similarity_engine is None:
        _similarity_engine = SimilaritySearchEngine()
    return _similarity_engine
