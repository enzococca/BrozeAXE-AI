"""
Savignano Matrix Analyzer
==========================

Sistema per identificazione matrici di fusione e analisi delle fusioni.

Domande archeologiche affrontate:
1. Quante matrici sono state usate per produrre le 96 asce?
2. Caratteristiche tecniche e formali delle matrici
3. Quante fusioni sono state eseguite per ciascuna matrice?

Metodi utilizzati:
- Clustering gerarchico (Hierarchical Clustering)
- K-Means clustering
- Analisi PCA per riduzione dimensionalità
- Similarità morfometrica

Autore: Archaeological Classifier System
Data: Novembre 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import seaborn as sns
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatrixAnalyzer:
    """
    Analizzatore di matrici di fusione per asce Savignano.

    Identifica gruppi di asce prodotte dalla stessa matrice basandosi su:
    - Similarità morfometrica (dimensioni, forme)
    - Presenza/assenza di caratteristiche (incavo, margini, etc.)
    - Micro-variazioni indicative di fusioni successive

    Attributes:
        features_df: DataFrame con features morfometriche
        n_matrices: Numero matrici identificate
        matrices: Dict con informazioni sulle matrici
        assignments: Dict con assegnazioni asce->matrici
    """

    def __init__(self, features_df: pd.DataFrame):
        """
        Inizializza analyzer.

        Args:
            features_df: DataFrame con features morfometriche estratte
                         Colonne richieste: artifact_id, tallone_larghezza,
                         incavo_presente, tagliente_larghezza, peso, etc.
        """
        self.features_df = features_df.copy()
        self.n_matrices = None
        self.matrices = {}
        self.assignments = {}
        self.cluster_labels = None
        self.linkage_matrix = None

        logger.info(f"MatrixAnalyzer inizializzato con {len(features_df)} asce")

    def identify_matrices(self,
                         method: str = 'hierarchical',
                         n_clusters: Optional[int] = None,
                         max_clusters: int = 15,
                         threshold: Optional[float] = None) -> Dict:
        """
        Identifica matrici di fusione usando clustering.

        Args:
            method: 'hierarchical' o 'kmeans'
            n_clusters: Numero cluster (se None, determina automaticamente)
            max_clusters: Massimo numero cluster da considerare
            threshold: Soglia distanza per hierarchical (se None, usa silhouette)

        Returns:
            Dict con:
            - n_matrices: Numero matrici identificate
            - method_used: Metodo clustering
            - silhouette_score: Score qualità clustering
            - matrices_info: Info sulle matrici

        Example:
            >>> analyzer = MatrixAnalyzer(features_df)
            >>> result = analyzer.identify_matrices(method='hierarchical')
            >>> print(f"Identificate {result['n_matrices']} matrici")
        """
        logger.info(f"Inizio identificazione matrici con metodo: {method}")

        # 1. Prepara feature matrix
        X = self._prepare_feature_matrix()

        # 2. Edge case: singola ascia
        if len(X) == 1:
            logger.warning("Solo 1 ascia presente - clustering non necessario. Assegnata a matrice 1.")
            self.cluster_labels = np.array([0])
            self.n_matrices = 1
            self._analyze_matrix_characteristics()

            return {
                'n_matrices': 1,
                'method_used': 'single_sample',
                'silhouette_score': None,
                'davies_bouldin_score': None,
                'matrices_info': self.matrices
            }

        # 2b. Edge case: solo 2 asce - silhouette score richiede almeno 3 campioni
        if len(X) == 2:
            logger.warning("Solo 2 asce presenti - silhouette score non calcolabile. Assegnate a cluster separati basati su distanza.")
            # Calcola distanza euclidea tra i 2 campioni
            from scipy.spatial.distance import euclidean
            dist = euclidean(X[0], X[1])
            # Se distanza bassa, stesso cluster; altrimenti cluster diversi
            threshold_dist = np.std(X) * 2  # Soglia basata su varianza
            if dist < threshold_dist:
                self.cluster_labels = np.array([0, 0])  # Stesso cluster
                self.n_matrices = 1
                logger.info(f"2 asce molto simili (dist={dist:.3f} < {threshold_dist:.3f}) - assegnate alla stessa matrice")
            else:
                self.cluster_labels = np.array([0, 1])  # Cluster diversi
                self.n_matrices = 2
                logger.info(f"2 asce diverse (dist={dist:.3f} >= {threshold_dist:.3f}) - assegnate a matrici diverse")

            self._analyze_matrix_characteristics()

            return {
                'n_matrices': self.n_matrices,
                'method_used': 'two_samples_heuristic',
                'silhouette_score': None,
                'davies_bouldin_score': None,
                'matrices_info': self.matrices
            }

        # 3. Esegui clustering
        if method == 'hierarchical':
            result = self._hierarchical_clustering(X, n_clusters, max_clusters, threshold)
        elif method == 'kmeans':
            result = self._kmeans_clustering(X, n_clusters, max_clusters)
        else:
            raise ValueError(f"Metodo non supportato: {method}")

        self.cluster_labels = result['labels']
        self.n_matrices = result['n_clusters']

        # 4. Analizza caratteristiche matrici
        self._analyze_matrix_characteristics()

        # 5. Calcola metriche qualità (se possibile)
        # Silhouette richiede: 2 <= n_labels <= n_samples - 1
        n_unique_labels = len(np.unique(self.cluster_labels))
        n_samples = len(X)

        silhouette = None
        davies_bouldin = None

        if n_unique_labels >= 2 and n_unique_labels <= n_samples - 1:
            try:
                silhouette = silhouette_score(X, self.cluster_labels)
                davies_bouldin = davies_bouldin_score(X, self.cluster_labels)
                logger.info(f"Identificate {self.n_matrices} matrici. "
                           f"Silhouette={silhouette:.3f}, Davies-Bouldin={davies_bouldin:.3f}")
            except Exception as e:
                logger.warning(f"Impossibile calcolare metriche qualità: {e}")
        else:
            logger.info(f"Identificate {self.n_matrices} matrici. "
                       f"Metriche qualità non calcolabili (n_labels={n_unique_labels}, n_samples={n_samples})")

        return {
            'n_matrices': self.n_matrices,
            'method_used': method,
            'silhouette_score': float(silhouette) if silhouette is not None else None,
            'davies_bouldin_score': float(davies_bouldin) if davies_bouldin is not None else None,
            'matrices_info': self.matrices
        }

    def _prepare_feature_matrix(self) -> np.ndarray:
        """
        Prepara matrice features per clustering.

        Seleziona features più rilevanti per identificazione matrici:
        - Dimensioni chiave (lunghezza, larghezza, spessore tallone)
        - Caratteristiche incavo (larghezza, profondità)
        - Caratteristiche tagliente (larghezza, forma codificata)
        - Peso

        Returns:
            Matrice features standardizzata (n_samples, n_features)
        """
        # Check if dataframe is empty
        if len(self.features_df) == 0:
            raise ValueError("Cannot prepare feature matrix: dataframe is empty. "
                           "No features were extracted from the meshes.")

        feature_cols = [
            'length',
            'width',
            'thickness',
            'tallone_larghezza',
            'tallone_spessore',
            'incavo_larghezza',
            'incavo_profondita',
            'tagliente_larghezza',
            'peso',
            'margini_rialzati_lunghezza',
            'larghezza_minima'
        ]

        # Aggiungi features booleane codificate
        boolean_features = [
            'incavo_presente',
            'margini_rialzati_presenti',
            'tagliente_espanso'
        ]

        # Check which columns are missing
        all_required_cols = feature_cols + boolean_features
        missing_cols = [col for col in all_required_cols if col not in self.features_df.columns]

        if missing_cols:
            logger.warning(f"Missing columns in features dataframe: {missing_cols}")
            logger.warning(f"Available columns: {list(self.features_df.columns)}")
            raise ValueError(
                f"Cannot prepare feature matrix: missing required columns: {missing_cols}.\n"
                f"This usually means feature extraction failed. Check the morphometric extractor logs.\n"
                f"Available columns: {list(self.features_df.columns)}"
            )

        # Crea matrice
        X_numeric = self.features_df[feature_cols].fillna(0).values
        X_boolean = self.features_df[boolean_features].fillna(0).astype(int).values

        X = np.hstack([X_numeric, X_boolean])

        # Standardizza
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Salva scaler per uso futuro
        self.scaler = scaler

        logger.info(f"Feature matrix preparata: shape={X_scaled.shape}")

        return X_scaled

    def _hierarchical_clustering(self,
                                 X: np.ndarray,
                                 n_clusters: Optional[int],
                                 max_clusters: int,
                                 threshold: Optional[float]) -> Dict:
        """
        Clustering gerarchico.

        Metodo:
        1. Calcola linkage matrix (Ward method)
        2. Se n_clusters non specificato, determina numero ottimale
        3. Assegna labels

        Args:
            X: Feature matrix standardizzata
            n_clusters: Numero cluster (None = auto)
            max_clusters: Massimo cluster da testare
            threshold: Soglia distanza (None = usa n_clusters)

        Returns:
            Dict con labels e n_clusters
        """
        # Calcola linkage matrix
        self.linkage_matrix = linkage(X, method='ward')

        # Determina numero ottimale cluster
        if n_clusters is None and threshold is None:
            n_clusters = self._find_optimal_n_clusters_hierarchical(X, max_clusters)
            logger.info(f"Numero ottimale cluster determinato: {n_clusters}")

        # Assegna labels
        if threshold is not None:
            labels = fcluster(self.linkage_matrix, threshold, criterion='distance')
            n_clusters = len(np.unique(labels))
        else:
            labels = fcluster(self.linkage_matrix, n_clusters, criterion='maxclust')

        # Converti a 0-indexed
        labels = labels - 1

        return {
            'labels': labels,
            'n_clusters': n_clusters
        }

    def _kmeans_clustering(self,
                          X: np.ndarray,
                          n_clusters: Optional[int],
                          max_clusters: int) -> Dict:
        """
        K-Means clustering.

        Args:
            X: Feature matrix
            n_clusters: Numero cluster (None = auto)
            max_clusters: Massimo cluster da testare

        Returns:
            Dict con labels e n_clusters
        """
        # Determina numero ottimale
        if n_clusters is None:
            n_clusters = self._find_optimal_n_clusters_kmeans(X, max_clusters)
            logger.info(f"Numero ottimale cluster determinato: {n_clusters}")

        # Esegui K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        self.kmeans_model = kmeans

        return {
            'labels': labels,
            'n_clusters': n_clusters
        }

    def _find_optimal_n_clusters_hierarchical(self, X: np.ndarray, max_k: int) -> int:
        """
        Trova numero ottimale cluster per hierarchical usando silhouette score.

        Args:
            X: Feature matrix
            max_k: Massimo numero cluster da testare

        Returns:
            Numero ottimale cluster
        """
        n_samples = len(X)

        # Silhouette score richiede: 2 <= n_labels <= n_samples - 1
        # Quindi il massimo k testabile è n_samples - 1
        effective_max_k = min(max_k, n_samples - 1)

        # Se non possiamo testare nemmeno k=2, restituisci 1 cluster
        if effective_max_k < 2:
            logger.warning(f"Troppi pochi campioni ({n_samples}) per clustering ottimale. Usando 1 cluster.")
            return 1

        silhouette_scores = []

        for k in range(2, effective_max_k + 1):
            labels = fcluster(self.linkage_matrix, k, criterion='maxclust') - 1
            score = silhouette_score(X, labels)
            silhouette_scores.append(score)

        # Trova k con massimo silhouette
        optimal_k = np.argmax(silhouette_scores) + 2

        logger.info(f"Silhouette scores testati (k=2 to {effective_max_k}): {silhouette_scores}")

        return optimal_k

    def _find_optimal_n_clusters_kmeans(self, X: np.ndarray, max_k: int) -> int:
        """
        Trova numero ottimale cluster per K-Means usando silhouette score.

        Args:
            X: Feature matrix
            max_k: Massimo numero cluster

        Returns:
            Numero ottimale cluster
        """
        n_samples = len(X)

        # Silhouette score richiede: 2 <= n_labels <= n_samples - 1
        effective_max_k = min(max_k, n_samples - 1)

        # Se non possiamo testare nemmeno k=2, restituisci 1 cluster
        if effective_max_k < 2:
            logger.warning(f"Troppi pochi campioni ({n_samples}) per clustering ottimale. Usando 1 cluster.")
            return 1

        silhouette_scores = []

        for k in range(2, effective_max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            score = silhouette_score(X, labels)
            silhouette_scores.append(score)

        optimal_k = np.argmax(silhouette_scores) + 2

        logger.info(f"Silhouette scores testati (k=2 to {effective_max_k}): {silhouette_scores}")

        return optimal_k

    def _analyze_matrix_characteristics(self):
        """
        Analizza caratteristiche distintive di ogni matrice identificata.

        Per ogni matrice (cluster), calcola:
        - Centroide (valori medi)
        - Variabilità intra-cluster
        - Caratteristiche distintive
        - Numero asce prodotte
        """
        # Aggiungi cluster labels al DataFrame
        self.features_df['matrix_id'] = self.cluster_labels

        for matrix_id in range(self.n_matrices):
            # Filtra asce di questa matrice
            matrix_axes = self.features_df[self.features_df['matrix_id'] == matrix_id]

            # Calcola statistiche
            matrix_info = {
                'matrix_id': f"MAT_{chr(65 + matrix_id)}",  # MAT_A, MAT_B, etc.
                'artifacts_count': len(matrix_axes),
                'artifact_ids': matrix_axes['artifact_id'].tolist(),

                # Dimensioni medie
                'avg_length': float(matrix_axes['length'].mean()),
                'avg_width': float(matrix_axes['width'].mean()),
                'avg_thickness': float(matrix_axes['thickness'].mean()),
                'avg_weight': float(matrix_axes['peso'].mean()) if 'peso' in matrix_axes.columns else None,

                # Tallone
                'avg_butt_width': float(matrix_axes['tallone_larghezza'].mean()),
                'avg_butt_thickness': float(matrix_axes['tallone_spessore'].mean()),

                # Incavo
                'has_socket': bool(matrix_axes['incavo_presente'].mode()[0]) if len(matrix_axes) > 0 else False,
                'avg_socket_width': float(matrix_axes['incavo_larghezza'].mean()) if matrix_axes['incavo_presente'].any() else 0.0,
                'avg_socket_depth': float(matrix_axes['incavo_profondita'].mean()) if matrix_axes['incavo_presente'].any() else 0.0,
                'socket_profile': matrix_axes['incavo_profilo'].mode()[0] if len(matrix_axes) > 0 else 'assente',

                # Tagliente
                'avg_blade_width': float(matrix_axes['tagliente_larghezza'].mean()),
                'blade_shape': matrix_axes['tagliente_forma'].mode()[0] if len(matrix_axes) > 0 else 'indeterminato',

                # Margini rialzati
                'has_raised_edges': bool(matrix_axes['margini_rialzati_presenti'].mode()[0]) if len(matrix_axes) > 0 else False,

                # Variabilità (coefficiente di variazione)
                'weight_cv': float(matrix_axes['peso'].std() / (matrix_axes['peso'].mean() + 1e-6)) if 'peso' in matrix_axes.columns else None,
                'length_cv': float(matrix_axes['length'].std() / (matrix_axes['length'].mean() + 1e-6)),
                'width_cv': float(matrix_axes['width'].std() / (matrix_axes['width'].mean() + 1e-6)),
            }

            # Determina tipo matrice (basandosi su caratteristiche)
            matrix_info['type'] = self._infer_matrix_type(matrix_info)

            # Descrizione testuale
            matrix_info['description'] = self._generate_matrix_description(matrix_info)

            self.matrices[matrix_info['matrix_id']] = matrix_info

            logger.info(f"{matrix_info['matrix_id']}: {matrix_info['artifacts_count']} asce, "
                       f"Tipo={matrix_info['type']}")

    def _infer_matrix_type(self, matrix_info: Dict) -> str:
        """
        Inferisce tipo matrice (monovalva/bivalva) basandosi su caratteristiche.

        Euristica:
        - Bivalva: simmetria elevata, bassa variabilità, incavo ben definito
        - Monovalva: maggiore variabilità, caratteristiche meno consistenti

        Args:
            matrix_info: Info matrice

        Returns:
            'bivalva' o 'monovalva'
        """
        # Se variabilità bassa e incavo presente/ben definito -> probabile bivalva
        avg_cv = np.mean([
            matrix_info['length_cv'],
            matrix_info['width_cv'],
            matrix_info['weight_cv'] if matrix_info['weight_cv'] else 0
        ])

        if avg_cv < 0.05 and matrix_info['has_socket']:
            return 'bivalva'
        else:
            return 'monovalva_o_bivalva_imprecisa'

    def _generate_matrix_description(self, matrix_info: Dict) -> str:
        """
        Genera descrizione testuale matrice.

        Args:
            matrix_info: Info matrice

        Returns:
            Stringa descrittiva
        """
        desc_parts = [f"Matrice {matrix_info['matrix_id']}"]

        # Tipo
        desc_parts.append(f"tipo {matrix_info['type']}")

        # Incavo
        if matrix_info['has_socket']:
            desc_parts.append(f"con incavo {matrix_info['socket_profile']} "
                            f"(L={matrix_info['avg_socket_width']:.1f}mm, "
                            f"P={matrix_info['avg_socket_depth']:.1f}mm)")
        else:
            desc_parts.append("senza incavo")

        # Margini
        if matrix_info['has_raised_edges']:
            desc_parts.append("con margini rialzati")

        # Dimensioni
        desc_parts.append(f"Dimensioni medie: L={matrix_info['avg_length']:.1f}mm, "
                         f"l={matrix_info['avg_width']:.1f}mm, "
                         f"Peso={matrix_info['avg_weight']:.0f}g")

        return ", ".join(desc_parts)

    def estimate_fusions_per_matrix(self,
                                    variance_threshold: float = 0.02) -> Dict:
        """
        Stima numero fusioni eseguite per ogni matrice.

        Principio:
        Fusioni successive dalla stessa matrice producono oggetti molto simili
        ma con micro-variazioni dovute a:
        - Usura matrice
        - Variazioni temperatura fusione
        - Differenze nella rifinitura post-fusione

        Assumiamo: ogni ascia = 1 fusione distinta

        Args:
            variance_threshold: Soglia variabilità per considerare fusioni identiche

        Returns:
            Dict con:
            - fusions_per_matrix: Dict {matrix_id: n_fusions}
            - fusion_details: Dettagli per matrice

        Example:
            >>> result = analyzer.estimate_fusions_per_matrix()
            >>> print(result['fusions_per_matrix'])
            {'MAT_A': 23, 'MAT_B': 18, ...}
        """
        logger.info("Stimando numero fusioni per matrice...")

        fusions_per_matrix = {}
        fusion_details = {}

        for matrix_id, matrix_info in self.matrices.items():
            n_axes = matrix_info['artifacts_count']

            # Assunzione base: 1 ascia = 1 fusione
            # (fusioni multiple da stessa colata sarebbero identiche)
            n_fusions_estimated = n_axes

            # Calcola micro-clusters all'interno della matrice
            # per identificare possibili fusioni multiple identiche
            # Converte "MAT_A" -> 0, "MAT_B" -> 1, etc.
            cluster_label = ord(matrix_id.split('_')[1]) - ord('A')
            matrix_axes = self.features_df[self.features_df['matrix_id'] == cluster_label]

            # Se variabilità molto bassa, possibili fusioni duplicate
            weight_var = matrix_info['weight_cv'] if matrix_info['weight_cv'] else 0
            length_var = matrix_info['length_cv']

            if weight_var < variance_threshold and length_var < variance_threshold:
                # Possibili fusioni multiple identiche
                # Usa clustering fine-grained
                logger.info(f"{matrix_id}: Bassa variabilità, verifica fusioni multiple")
                # Qui potrebbe essere implementato clustering secondario
                # Per ora, assumi 1 fusione = 1 ascia

            fusions_per_matrix[matrix_id] = n_fusions_estimated

            fusion_details[matrix_id] = {
                'estimated_fusions': n_fusions_estimated,
                'artifacts': matrix_axes['artifact_id'].tolist(),
                'inventory_numbers': matrix_axes['inventory_number'].tolist() if 'inventory_number' in matrix_axes.columns else [],
                'confidence': 'HIGH' if weight_var < variance_threshold else 'MEDIUM',
                'notes': (f"Variabilità peso CV={weight_var:.3f}, lunghezza CV={length_var:.3f}. "
                         f"Ogni ascia considerata fusione distinta.")
            }

            logger.info(f"{matrix_id}: {n_fusions_estimated} fusioni stimate")

        total_fusions = sum(fusions_per_matrix.values())

        return {
            'fusions_per_matrix': fusions_per_matrix,
            'fusion_details': fusion_details,
            'total_fusions': total_fusions
        }

    def get_matrix_assignments(self) -> pd.DataFrame:
        """
        Ritorna DataFrame con assegnazioni asce -> matrici.

        Returns:
            DataFrame con colonne:
            - artifact_id
            - inventory_number
            - matrix_id
            - distance_from_center (similarità al centroide matrice)
            - confidence
        """
        if self.cluster_labels is None:
            raise ValueError("Eseguire prima identify_matrices()")

        assignments = []

        for idx, row in self.features_df.iterrows():
            matrix_id = f"MAT_{chr(65 + int(row['matrix_id']))}"

            # Calcola distanza dal centroide matrice
            # (usando features standardizzate)
            X = self._prepare_feature_matrix()
            centroid = X[self.cluster_labels == row['matrix_id']].mean(axis=0)
            distance = np.linalg.norm(X[idx] - centroid)

            # Calcola confidence (inverso distanza normalizzato)
            max_distance = X.std(axis=0).sum()
            confidence = 1.0 / (1.0 + distance / max_distance)

            assignments.append({
                'artifact_id': row['artifact_id'],
                'inventory_number': row.get('inventory_number', ''),
                'matrix_id': matrix_id,
                'distance_from_center': float(distance),
                'similarity_to_matrix_center': float(confidence),
                'assignment_confidence': float(confidence)
            })

        return pd.DataFrame(assignments)

    def plot_dendrogram(self, output_path: Optional[str] = None):
        """
        Visualizza dendrogram hierarchical clustering.

        Args:
            output_path: Path per salvare figura (opzionale)
        """
        if self.linkage_matrix is None:
            raise ValueError("Linkage matrix non disponibile. "
                           "Eseguire identify_matrices(method='hierarchical')")

        plt.figure(figsize=(15, 8))
        dendrogram(
            self.linkage_matrix,
            labels=self.features_df['artifact_id'].values,
            leaf_rotation=90,
            leaf_font_size=8
        )
        plt.title('Dendrogram - Savignano Axes Matrices', fontsize=16)
        plt.xlabel('Artifact ID', fontsize=12)
        plt.ylabel('Distance', fontsize=12)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Dendrogram salvato: {output_path}")

        plt.close()  # Close figure to free memory (no plt.show() in server environment)

    def plot_pca_clusters(self, output_path: Optional[str] = None):
        """
        Visualizza clustering su spazio PCA 2D.

        Args:
            output_path: Path per salvare figura (opzionale)
        """
        if self.cluster_labels is None:
            raise ValueError("Clustering non eseguito")

        # PCA 2D
        X = self._prepare_feature_matrix()
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X)

        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(
            X_pca[:, 0],
            X_pca[:, 1],
            c=self.cluster_labels,
            cmap='tab20',
            s=100,
            alpha=0.7,
            edgecolors='black'
        )

        # Annotate alcuni punti
        for i, artifact_id in enumerate(self.features_df['artifact_id'].values):
            if i % 5 == 0:  # Annotate ogni 5
                plt.annotate(
                    artifact_id,
                    (X_pca[i, 0], X_pca[i, 1]),
                    fontsize=6,
                    alpha=0.7
                )

        plt.colorbar(scatter, label='Matrix ID')
        plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
        plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
        plt.title('Savignano Axes - PCA Clusters (Matrices)', fontsize=16)
        plt.grid(alpha=0.3)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"PCA plot salvato: {output_path}")

        plt.close()  # Close figure to free memory (no plt.show() in server environment)

    def export_results(self, output_dir: str):
        """
        Esporta risultati analisi in file JSON e CSV.

        Args:
            output_dir: Directory output

        Files generati:
        - matrices_summary.json: Info matrici
        - fusions_per_matrix.json: Fusioni per matrice
        - matrix_assignments.csv: Assegnazioni asce->matrici
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 1. Matrices summary
        with open(os.path.join(output_dir, 'matrices_summary.json'), 'w') as f:
            json.dump(self.matrices, f, indent=2)
        logger.info(f"Exported: matrices_summary.json")

        # 2. Fusions per matrix
        fusions = self.estimate_fusions_per_matrix()
        with open(os.path.join(output_dir, 'fusions_per_matrix.json'), 'w') as f:
            json.dump(fusions, f, indent=2)
        logger.info(f"Exported: fusions_per_matrix.json")

        # 3. Assignments CSV
        assignments_df = self.get_matrix_assignments()
        assignments_df.to_csv(
            os.path.join(output_dir, 'matrix_assignments.csv'),
            index=False
        )
        logger.info(f"Exported: matrix_assignments.csv")

        logger.info(f"Tutti i risultati esportati in: {output_dir}")