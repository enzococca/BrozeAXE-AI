"""
Savignano Morphometric Extractor
==================================

Modulo per estrazione parametri morfometrici specifici delle asce di Savignano.

Parametri estratti (basati su schema Savignano):
- Tallone: larghezza, spessore, incavo (larghezza, profondità, profilo)
- Margini rialzati: lunghezza, spessore massimo
- Corpo: larghezza minima, spessore massimo con/senza margini
- Tagliente: larghezza, forma (arco ribassato/semicircolare/lunato), arco e corda

Autore: Archaeological Classifier System
Data: Novembre 2025
"""

import numpy as np
import trimesh
from typing import Dict, Tuple, Optional, List
from scipy.spatial import cKDTree, ConvexHull
from scipy.interpolate import splprep, splev
from sklearn.decomposition import PCA
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SavignanoMorphometricExtractor:
    """
    Estrattore di parametri morfometrici specifici per asce di Savignano.

    Metodi principali:
    ------------------
    - extract_all_features(): Estrae tutti i parametri morfometrici
    - analyze_butt(): Analizza tallone e incavo
    - analyze_raised_edges(): Analizza margini rialzati
    - analyze_blade(): Analizza tagliente
    """

    # Common scale factors for mesh units
    SCALE_FACTORS = {
        'mm': 1.0,          # Already in mm
        'cm': 10.0,         # Centimeters to mm
        'm': 1000.0,        # Meters to mm
        'in': 25.4,         # Inches to mm
        'auto': None        # Auto-detect (not implemented yet)
    }

    def __init__(self, mesh: trimesh.Trimesh, artifact_id: str, scale_factor: float = 1.0, mesh_units: str = None):
        """
        Inizializza extractor.

        Args:
            mesh: Mesh 3D dell'ascia
            artifact_id: ID univoco dell'artefatto
            scale_factor: Fattore di scala per convertire unità mesh in mm (default: 1.0)
                         Es: 10.0 per cm->mm, 1000.0 per m->mm
            mesh_units: Unità della mesh ('mm', 'cm', 'm', 'in'). Se specificato,
                       sovrascrive scale_factor con il valore appropriato.
        """
        self.mesh = mesh
        self.artifact_id = artifact_id

        # Determina fattore di scala
        if mesh_units and mesh_units in self.SCALE_FACTORS:
            self.scale_factor = self.SCALE_FACTORS[mesh_units]
            logger.info(f"{artifact_id}: Using mesh units '{mesh_units}' -> scale factor {self.scale_factor}")
        else:
            self.scale_factor = scale_factor

        # Applica fattore di scala ai vertici
        self.vertices = mesh.vertices * self.scale_factor
        self.faces = mesh.faces

        if self.scale_factor != 1.0:
            logger.info(f"{artifact_id}: Applied scale factor {self.scale_factor}x (mesh units -> mm)")

        # Identifica orientamento ascia (asse principale)
        self._identify_orientation()

    def _identify_orientation(self):
        """
        Identifica orientamento ascia usando PCA.

        Convenzione PCA (automatica, ordinata per varianza decrescente):
        - Asse X (PCA componente 0): lunghezza ascia (tallone -> tagliente) [~163mm]
        - Asse Y (PCA componente 1): larghezza (sinistra -> destra) [~56mm]
        - Asse Z (PCA componente 2): spessore/thickness (basso -> alto) [~15mm]

        Nota: La PCA ordina automaticamente per varianza, quindi la dimensione più lunga
        viene assegnata all'asse X, la media all'asse Y, e la più corta all'asse Z.
        """
        pca = PCA(n_components=3)
        pca.fit(self.vertices)

        # Componenti principali
        self.pca_components = pca.components_
        self.pca_center = pca.mean_

        # Proietta vertici su assi PCA
        self.vertices_pca = pca.transform(self.vertices)

        # Identifica estremità (tallone vs tagliente) usando X (lunghezza)
        # FIXED: Use X axis for length, not Z (Z is thickness!)
        x_values = self.vertices_pca[:, 0]
        self.x_min, self.x_max = x_values.min(), x_values.max()

        # Assumiamo: x_max = tallone, x_min = tagliente
        # (se invertito, cambiare convenzione)
        self.butt_end = self.x_max  # Tallone (estremità positiva X)
        self.blade_end = self.x_min  # Tagliente (estremità negativa X)

        logger.info(f"{self.artifact_id}: Orientamento identificato. "
                   f"Tallone={self.butt_end:.2f}, Tagliente={self.blade_end:.2f}")

    def extract_all_features(self) -> Dict:
        """
        Estrae tutti i parametri morfometrici Savignano.

        Returns:
            Dict con tutti i parametri estratti
        """
        logger.info(f"{self.artifact_id}: Inizio estrazione parametri morfometrici...")

        features = {}

        # 1. Analisi tallone e incavo
        butt_features = self.analyze_butt()
        features.update(butt_features)

        # 2. Analisi margini rialzati
        edges_features = self.analyze_raised_edges()
        features.update(edges_features)

        # 3. Analisi corpo
        body_features = self.analyze_body()
        features.update(body_features)

        # 4. Analisi tagliente
        blade_features = self.analyze_blade()
        features.update(blade_features)

        # 5. Dimensioni generali
        general_features = self._extract_general_dimensions()
        features.update(general_features)

        logger.info(f"{self.artifact_id}: Estrazione completata. "
                   f"Estratti {len(features)} parametri.")

        return features

    def analyze_butt(self) -> Dict:
        """
        Analizza tallone e incavo.

        Returns:
            Dict con:
            - tallone_larghezza (mm)
            - tallone_spessore (mm)
            - incavo_presente (bool)
            - incavo_larghezza (mm)
            - incavo_profondita (mm)
            - incavo_profilo ('rettangolare', 'circolare', 'assente')
        """
        logger.info(f"{self.artifact_id}: Analizzando tallone...")

        # Isola regione tallone (ultimi 10% lunghezza)
        # FIXED: Use X for length filtering (was Z)
        butt_threshold = self.butt_end - 0.1 * (self.butt_end - self.blade_end)
        butt_mask = self.vertices_pca[:, 0] >= butt_threshold
        butt_vertices = self.vertices[butt_mask]

        logger.info(f"{self.artifact_id}: DEBUG - Butt region vertices: {len(butt_vertices)} "
                   f"(X threshold: {butt_threshold:.2f}mm)")

        if len(butt_vertices) < 10:
            logger.warning(f"{self.artifact_id}: Regione tallone troppo piccola")
            return self._default_butt_features()

        # 1. Larghezza e spessore tallone
        # FIXED: tallone_larghezza = Y range (width), tallone_spessore = Z range (thickness)
        butt_vertices_pca = self.vertices_pca[butt_mask]
        y_values = butt_vertices_pca[:, 1]
        z_values = butt_vertices_pca[:, 2]

        tallone_larghezza = y_values.max() - y_values.min()  # Y is width
        tallone_spessore = z_values.max() - z_values.min()   # Z is thickness

        logger.info(f"{self.artifact_id}: DEBUG - Tallone Y range (larghezza): {tallone_larghezza:.2f}mm "
                   f"({y_values.min():.2f} to {y_values.max():.2f})")
        logger.info(f"{self.artifact_id}: DEBUG - Tallone Z range (spessore): {tallone_spessore:.2f}mm "
                   f"({z_values.min():.2f} to {z_values.max():.2f})")

        # 2. Rileva incavo (concavità sulla superficie superiore)
        incavo_result = self._detect_socket(butt_vertices_pca)

        features = {
            'tallone_larghezza': float(tallone_larghezza),
            'tallone_spessore': float(tallone_spessore),
            'incavo_presente': incavo_result['presente'],
            'incavo_larghezza': incavo_result['larghezza'],
            'incavo_profondita': incavo_result['profondita'],
            'incavo_profilo': incavo_result['profilo']
        }

        logger.info(f"{self.artifact_id}: Tallone - L={tallone_larghezza:.2f}mm, "
                   f"S={tallone_spessore:.2f}mm, Incavo={incavo_result['presente']}")

        return features

    def _detect_socket(self, butt_vertices_pca: np.ndarray) -> Dict:
        """
        Rileva presenza e caratteristiche incavo nel tallone.

        Metodo:
        1. Analizza curvatura locale sulla superficie superiore
        2. Identifica regioni concave (curvatura negativa)
        3. Classifica profilo (rettangolare vs circolare)

        Args:
            butt_vertices_pca: Vertici tallone in coordinate PCA

        Returns:
            Dict con presente, larghezza, profondità, profilo
        """
        logger.info(f"{self.artifact_id}: DEBUG - Tallone vertices count: {len(butt_vertices_pca)}")

        # Filtra superficie superiore (massimo Z - thickness/top surface)
        # FIXED: Use Z for top surface (was Y, which is width!)
        z_threshold = np.percentile(butt_vertices_pca[:, 2], 75)
        top_surface_mask = butt_vertices_pca[:, 2] >= z_threshold
        top_vertices = butt_vertices_pca[top_surface_mask]

        logger.info(f"{self.artifact_id}: DEBUG - Top surface vertices: {len(top_vertices)} "
                   f"(Z threshold: {z_threshold:.2f}mm)")

        if len(top_vertices) < 20:
            return {
                'presente': False,
                'larghezza': 0.0,
                'profondita': 0.0,
                'profilo': 'assente'
            }

        # Calcola curvatura locale (approssimazione con nearest neighbors)
        tree = cKDTree(top_vertices)
        curvatures = []

        for vertex in top_vertices:
            # Trova vicini entro raggio 3mm
            neighbors_idx = tree.query_ball_point(vertex, r=3.0)
            if len(neighbors_idx) < 5:
                continue

            neighbors = top_vertices[neighbors_idx]

            # Fit piano locale
            # FIXED: Use Z deviations for curvature (vertical depth, was Y which is width!)
            centroid = neighbors.mean(axis=0)
            deviations = neighbors[:, 2] - centroid[2]  # Z deviations (vertical/depth)

            # Curvatura = deviazione std
            curvature = np.std(deviations)
            curvatures.append(curvature)

        if not curvatures:
            return {
                'presente': False,
                'larghezza': 0.0,
                'profondita': 0.0,
                'profilo': 'assente'
            }

        mean_curvature = np.mean(curvatures)

        # Calcola anche la profondità della concavità come metodo alternativo
        # FIXED: Use Z for depth (was Y which is width!)
        z_min = top_vertices[:, 2].min()
        z_max = top_vertices[:, 2].max()
        depth_range = z_max - z_min

        logger.info(f"{self.artifact_id}: DEBUG - Depth range: {depth_range:.2f}mm "
                   f"(Z min: {z_min:.2f}, Z max: {z_max:.2f})")
        logger.info(f"{self.artifact_id}: DEBUG - Mean curvature: {mean_curvature:.4f}mm")

        # SOGLIA RIDOTTA: curvatura > 0.2mm O profondità > 1.0mm indica incavo
        CURVATURE_THRESHOLD = 0.2  # Ridotta da 0.5 per maggiore sensibilità
        DEPTH_THRESHOLD = 1.0  # Soglia alternativa basata su profondità

        # Rileva incavo se ALMENO UNA delle due condizioni è vera
        has_socket = (mean_curvature >= CURVATURE_THRESHOLD) or (depth_range >= DEPTH_THRESHOLD)

        if not has_socket:
            logger.info(f"{self.artifact_id}: DEBUG - No socket detected (curvature and depth below thresholds)")
            return {
                'presente': False,
                'larghezza': 0.0,
                'profondita': 0.0,
                'profilo': 'assente'
            }

        # Incavo rilevato - misura dimensioni
        incavo_profondita = depth_range

        # CRITICAL FIX: Larghezza incavo - trova la regione più depressa (cluster centrale)
        # L'incavo è una piccola cavità rettangolare localizzata, NON tutta la superficie depressa
        # Strategia: trova il cluster più denso di vertici più profondi

        # Usa soglia molto aggressiva per trovare solo la piccola cavità dell'incavo (3-9mm)
        # FIXED: Use Z for depth (was Y which is width!)
        # ULTRA-AGGRESSIVE: Use 0.5% to capture only the absolute deepest points
        SOCKET_PERCENTILE = 0.5  # Only deepest 0.5% of vertices for tiny socket cavity

        z_socket_threshold = np.percentile(top_vertices[:, 2], SOCKET_PERCENTILE)
        concave_mask = top_vertices[:, 2] < z_socket_threshold
        concave_vertices = top_vertices[concave_mask]

        logger.info(f"{self.artifact_id}: DEBUG - Socket detection using {SOCKET_PERCENTILE}th percentile")
        logger.info(f"{self.artifact_id}: DEBUG - Z socket threshold: {z_socket_threshold:.2f}mm")
        logger.info(f"{self.artifact_id}: DEBUG - Concave vertices: {len(concave_vertices)} "
                   f"(of {len(top_vertices)} top vertices = {100*len(concave_vertices)/len(top_vertices):.1f}%)")

        if len(concave_vertices) > 0:
            # Find the main cluster of concave vertices (in case there are outliers)
            # Use the centroid and find vertices within a reasonable radius
            # FIXED: Cluster in XY plane (top surface plane), not XZ!
            centroid_xy = np.array([
                np.median(concave_vertices[:, 0]),
                np.median(concave_vertices[:, 1])
            ])

            # Calculate distances from centroid in XY plane (top surface)
            distances_xy = np.sqrt(
                (concave_vertices[:, 0] - centroid_xy[0])**2 +
                (concave_vertices[:, 1] - centroid_xy[1])**2
            )

            # Keep vertices within 60th percentile distance (looser for elongated sockets)
            # This allows capturing rectangular sockets (8-9mm) better than 50th percentile
            dist_threshold = np.percentile(distances_xy, 60)
            cluster_mask = distances_xy <= dist_threshold
            socket_vertices = concave_vertices[cluster_mask]

            logger.info(f"{self.artifact_id}: DEBUG - Socket cluster vertices: {len(socket_vertices)} "
                       f"(filtered from {len(concave_vertices)} concave vertices)")

            if len(socket_vertices) > 5:
                # Misura l'estensione X e Y del cluster socket (in piano superiore)
                # FIXED: Measure X and Y ranges (was X and Z)
                x_range = socket_vertices[:, 0].max() - socket_vertices[:, 0].min()
                y_range = socket_vertices[:, 1].max() - socket_vertices[:, 1].min()

                logger.info(f"{self.artifact_id}: DEBUG - Socket X range: {x_range:.2f}mm "
                           f"({socket_vertices[:, 0].min():.2f} to {socket_vertices[:, 0].max():.2f})")
                logger.info(f"{self.artifact_id}: DEBUG - Socket Y range: {y_range:.2f}mm "
                           f"({socket_vertices[:, 1].min():.2f} to {socket_vertices[:, 1].max():.2f})")

                # ITERATIVE REFINEMENT: Disabled - geometric mean works better without refinement
                # For rectangular sockets, geometric mean of initial clustering gives accurate results
                MAX_SOCKET_SIZE = 11.0  # mm - kept for potential future use
                current_size = max(x_range, y_range)

                if False and current_size > MAX_SOCKET_SIZE and len(socket_vertices) > 10:
                    logger.info(f"{self.artifact_id}: DEBUG - Socket size {current_size:.2f}mm > {MAX_SOCKET_SIZE}mm, "
                               f"applying iterative refinement...")

                    # Tighten to 45th percentile (balanced for 8-9mm target)
                    dist_threshold_tight = np.percentile(distances_xy[cluster_mask], 45)
                    cluster_mask_tight = distances_xy <= dist_threshold_tight
                    socket_vertices_tight = concave_vertices[cluster_mask_tight]

                    if len(socket_vertices_tight) > 5:
                        x_range_tight = socket_vertices_tight[:, 0].max() - socket_vertices_tight[:, 0].min()
                        y_range_tight = socket_vertices_tight[:, 1].max() - socket_vertices_tight[:, 1].min()

                        logger.info(f"{self.artifact_id}: DEBUG - After refinement: X={x_range_tight:.2f}mm, "
                                   f"Y={y_range_tight:.2f}mm, vertices={len(socket_vertices_tight)}")

                        # Use refined measurement if it's reasonable
                        if max(x_range_tight, y_range_tight) >= 3.0:
                            socket_vertices = socket_vertices_tight
                            x_range = x_range_tight
                            y_range = y_range_tight
                            logger.info(f"{self.artifact_id}: DEBUG - ✓ Using refined measurement")

                # FIXED: For elongated rectangular sockets, use geometric mean instead of max
                # This balances X and Y dimensions (max overestimates, min underestimates)
                # Geometric mean: sqrt(X * Y) provides balanced measurement for rectangles
                import math
                incavo_larghezza = math.sqrt(x_range * y_range)

                logger.info(f"{self.artifact_id}: DEBUG - Socket measurement method: geometric mean")
                logger.info(f"{self.artifact_id}: DEBUG - √({x_range:.2f} × {y_range:.2f}) = {incavo_larghezza:.2f}mm")
            else:
                # Fallback if clustering fails
                x_range = concave_vertices[:, 0].max() - concave_vertices[:, 0].min()
                y_range = concave_vertices[:, 1].max() - concave_vertices[:, 1].min()
                incavo_larghezza = max(x_range, y_range)
                socket_vertices = concave_vertices

            # Classifica profilo: circolare se aspect ratio ~1, altrimenti rettangolare
            aspect_ratio = x_range / (y_range + 1e-6)

            logger.info(f"{self.artifact_id}: DEBUG - Socket aspect ratio: {aspect_ratio:.2f} "
                       f"(X/Y = {x_range:.2f}/{y_range:.2f})")

            if 0.7 <= aspect_ratio <= 1.3:
                incavo_profilo = 'circolare'
            else:
                incavo_profilo = 'rettangolare'
        else:
            incavo_larghezza = 0.0
            incavo_profilo = 'indeterminato'

        logger.info(f"{self.artifact_id}: Incavo rilevato - "
                   f"L={incavo_larghezza:.2f}mm, P={incavo_profondita:.2f}mm, "
                   f"Profilo={incavo_profilo}")

        return {
            'presente': True,
            'larghezza': float(incavo_larghezza),
            'profondita': float(incavo_profondita),
            'profilo': incavo_profilo
        }

    def analyze_raised_edges(self) -> Dict:
        """
        Analizza margini rialzati (raised edges).

        Returns:
            Dict con:
            - margini_rialzati_presenti (bool)
            - margini_rialzati_lunghezza (mm)
            - margini_rialzati_spessore_max (mm)
        """
        logger.info(f"{self.artifact_id}: Analizzando margini rialzati...")

        # Regione centrale (escludi tallone e tagliente)
        # FIXED: Use X for length (was Z)
        x_range = self.butt_end - self.blade_end
        central_start = self.blade_end + 0.2 * x_range
        central_end = self.butt_end - 0.2 * x_range

        central_mask = ((self.vertices_pca[:, 0] >= central_start) &
                       (self.vertices_pca[:, 0] <= central_end))
        central_vertices_pca = self.vertices_pca[central_mask]

        if len(central_vertices_pca) < 50:
            return self._default_edges_features()

        # Identifica margini (bordi laterali)
        # FIXED: Margini = vertici con Y estremo (sinistro e destro), not X!
        y_values = central_vertices_pca[:, 1]
        y_threshold_left = np.percentile(y_values, 5)
        y_threshold_right = np.percentile(y_values, 95)

        left_edge_mask = central_vertices_pca[:, 1] <= y_threshold_left
        right_edge_mask = central_vertices_pca[:, 1] >= y_threshold_right

        left_edge_vertices = central_vertices_pca[left_edge_mask]
        right_edge_vertices = central_vertices_pca[right_edge_mask]

        # Rileva se margini sono "rialzati" (elevazione Z maggiore)
        # FIXED: Confronta Z margini vs Z corpo centrale (Z is thickness/height, not Y!)

        # Z corpo centrale (mediana)
        central_z_median = np.median(central_vertices_pca[:, 2])

        # Z margini (media)
        left_z_mean = left_edge_vertices[:, 2].mean() if len(left_edge_vertices) > 0 else 0
        right_z_mean = right_edge_vertices[:, 2].mean() if len(right_edge_vertices) > 0 else 0

        # Soglia: margini rialzati se Z > mediana + 0.5mm
        RAISE_THRESHOLD = 0.5

        left_raised = (left_z_mean - central_z_median) > RAISE_THRESHOLD
        right_raised = (right_z_mean - central_z_median) > RAISE_THRESHOLD

        margini_presenti = left_raised or right_raised

        if not margini_presenti:
            return self._default_edges_features()

        # Misura lunghezza margini (estensione X - along length)
        # FIXED: Use X for length (was Z)
        all_edges = np.vstack([left_edge_vertices, right_edge_vertices])
        if len(all_edges) > 0:
            x_edges = all_edges[:, 0]
            margini_lunghezza = x_edges.max() - x_edges.min()

            # Spessore massimo margini (massima elevazione Z - height/thickness)
            # FIXED: Use Z for elevation (was Y)
            z_raise_left = left_z_mean - central_z_median if left_raised else 0
            z_raise_right = right_z_mean - central_z_median if right_raised else 0

            margini_spessore_max = max(z_raise_left, z_raise_right)
        else:
            margini_lunghezza = 0.0
            margini_spessore_max = 0.0

        logger.info(f"{self.artifact_id}: Margini rialzati - Presenti={margini_presenti}, "
                   f"L={margini_lunghezza:.2f}mm, Smax={margini_spessore_max:.2f}mm")

        return {
            'margini_rialzati_presenti': margini_presenti,
            'margini_rialzati_lunghezza': float(margini_lunghezza),
            'margini_rialzati_spessore_max': float(margini_spessore_max)
        }

    def analyze_body(self) -> Dict:
        """
        Analizza corpo ascia.

        Returns:
            Dict con:
            - larghezza_minima (mm)
            - spessore_massimo_con_margini (mm)
            - spessore_massimo_senza_margini (mm)
        """
        logger.info(f"{self.artifact_id}: Analizzando corpo...")

        # Regione corpo (centrale, escludi tallone 15% e tagliente 15%)
        # FIXED: Use X for length (was Z)
        x_range = self.butt_end - self.blade_end
        body_start = self.blade_end + 0.15 * x_range
        body_end = self.butt_end - 0.15 * x_range

        body_mask = ((self.vertices_pca[:, 0] >= body_start) &
                    (self.vertices_pca[:, 0] <= body_end))
        body_vertices_pca = self.vertices_pca[body_mask]

        if len(body_vertices_pca) < 20:
            return {
                'larghezza_minima': 0.0,
                'spessore_massimo_con_margini': 0.0,
                'spessore_massimo_senza_margini': 0.0
            }

        # 1. Larghezza minima (minimo range Y lungo X)
        # FIXED: Divide corpo in sezioni lungo X (length) e trova minima larghezza (Y)
        x_sections = np.linspace(body_start, body_end, 20)
        widths = []

        for i in range(len(x_sections) - 1):
            section_mask = ((body_vertices_pca[:, 0] >= x_sections[i]) &
                          (body_vertices_pca[:, 0] < x_sections[i+1]))
            section_vertices = body_vertices_pca[section_mask]

            if len(section_vertices) > 5:
                # FIXED: Measure Y range (width), not X!
                width = section_vertices[:, 1].max() - section_vertices[:, 1].min()
                widths.append(width)

        larghezza_minima = min(widths) if widths else 0.0

        # 2. Spessore massimo con margini
        # FIXED: Use Z for thickness (was Y which is width!)
        spessore_max_con_margini = (body_vertices_pca[:, 2].max() -
                                    body_vertices_pca[:, 2].min())

        # 3. Spessore massimo senza margini (corpo centrale, escludi bordi laterali)
        # FIXED: Exclude edges based on Y (width), not X (length)
        y_central_mask = ((body_vertices_pca[:, 1] > np.percentile(body_vertices_pca[:, 1], 25)) &
                         (body_vertices_pca[:, 1] < np.percentile(body_vertices_pca[:, 1], 75)))
        central_body = body_vertices_pca[y_central_mask]

        if len(central_body) > 10:
            # FIXED: Measure Z range (thickness), not Y (width)!
            spessore_max_senza_margini = (central_body[:, 2].max() -
                                          central_body[:, 2].min())
        else:
            spessore_max_senza_margini = spessore_max_con_margini

        logger.info(f"{self.artifact_id}: Corpo - Lmin={larghezza_minima:.2f}mm, "
                   f"Smax(con margini)={spessore_max_con_margini:.2f}mm, "
                   f"Smax(senza margini)={spessore_max_senza_margini:.2f}mm")

        return {
            'larghezza_minima': float(larghezza_minima),
            'spessore_massimo_con_margini': float(spessore_max_con_margini),
            'spessore_massimo_senza_margini': float(spessore_max_senza_margini)
        }

    def analyze_blade(self) -> Dict:
        """
        Analizza tagliente (cutting edge).

        Returns:
            Dict con:
            - tagliente_larghezza (mm)
            - tagliente_forma ('arco_ribassato', 'semicircolare', 'lunato')
            - tagliente_arco_misura (mm)
            - tagliente_corda_misura (mm)
            - tagliente_espanso (bool)
        """
        logger.info(f"{self.artifact_id}: Analizzando tagliente...")

        # Isola regione tagliente (ultimi 10% lunghezza)
        # FIXED: Use X for length (was Z)
        blade_threshold = self.blade_end + 0.1 * (self.butt_end - self.blade_end)
        blade_mask = self.vertices_pca[:, 0] <= blade_threshold
        blade_vertices_pca = self.vertices_pca[blade_mask]

        logger.info(f"{self.artifact_id}: DEBUG - Blade region vertices: {len(blade_vertices_pca)} "
                   f"(X threshold: {blade_threshold:.2f}mm)")

        if len(blade_vertices_pca) < 20:
            return self._default_blade_features()

        # 1. Larghezza tagliente (range Y - width)
        # FIXED: Measure Y range (width), not X (length)!
        tagliente_larghezza = (blade_vertices_pca[:, 1].max() -
                              blade_vertices_pca[:, 1].min())

        logger.info(f"{self.artifact_id}: DEBUG - Tagliente Y range (larghezza): {tagliente_larghezza:.2f}mm "
                   f"({blade_vertices_pca[:, 1].min():.2f} to {blade_vertices_pca[:, 1].max():.2f})")

        # 2. Rileva se tagliente è espanso (larghezza > larghezza corpo)
        # Confronta con larghezza medio corpo
        # FIXED: Filter by X (length), measure Y (width)
        body_mask = ((self.vertices_pca[:, 0] > blade_threshold) &
                    (self.vertices_pca[:, 0] < blade_threshold + 0.3 * (self.butt_end - self.blade_end)))
        body_vertices_pca = self.vertices_pca[body_mask]

        if len(body_vertices_pca) > 10:
            # FIXED: Measure Y range (width), not X!
            body_width = (body_vertices_pca[:, 1].max() -
                         body_vertices_pca[:, 1].min())
            tagliente_espanso = tagliente_larghezza > (body_width * 1.1)
        else:
            tagliente_espanso = False

        # 3. Analizza forma tagliente (profilo curvo)
        # Estrai curva del bordo tagliente (punti estremi X - length)
        # FIXED: Use X for length edge (was Z)
        x_min = blade_vertices_pca[:, 0].min()
        edge_threshold = x_min + 0.05 * (blade_vertices_pca[:, 0].max() - x_min)
        edge_mask = blade_vertices_pca[:, 0] <= edge_threshold

        edge_vertices = blade_vertices_pca[edge_mask]

        if len(edge_vertices) < 10:
            return self._default_blade_features()

        # Ordina edge vertices per Y (across width)
        # FIXED: Sort by Y (width), not X (length)
        sorted_idx = np.argsort(edge_vertices[:, 1])
        edge_sorted = edge_vertices[sorted_idx]

        # Misura arco e corda
        # Corda = distanza estremi (in piano YZ - width and thickness)
        # FIXED: Use (Y, Z) not (X, Y)!
        point_start = edge_sorted[0, 1:]  # (Y, Z) primo punto
        point_end = edge_sorted[-1, 1:]   # (Y, Z) ultimo punto

        tagliente_corda = np.linalg.norm(point_end - point_start)

        # Arco = somma distanze tra punti consecutivi (in piano YZ)
        # FIXED: Use columns 1: (Y, Z), not :2 which was (X, Y)!
        distances = np.linalg.norm(np.diff(edge_sorted[:, 1:], axis=0), axis=1)
        tagliente_arco = distances.sum()

        # Classifica forma basandosi su rapporto arco/corda
        arc_chord_ratio = tagliente_arco / (tagliente_corda + 1e-6)

        # Soglie empiriche:
        # - Arco ribassato: ratio ~ 1.0-1.15
        # - Semicircolare: ratio ~ 1.15-1.4
        # - Lunato: ratio > 1.4

        if arc_chord_ratio < 1.15:
            tagliente_forma = 'arco_ribassato'
        elif arc_chord_ratio < 1.4:
            tagliente_forma = 'semicircolare'
        else:
            tagliente_forma = 'lunato'

        logger.info(f"{self.artifact_id}: Tagliente - L={tagliente_larghezza:.2f}mm, "
                   f"Forma={tagliente_forma}, Arco={tagliente_arco:.2f}mm, "
                   f"Corda={tagliente_corda:.2f}mm, Espanso={tagliente_espanso}")

        return {
            'tagliente_larghezza': float(tagliente_larghezza),
            'tagliente_forma': tagliente_forma,
            'tagliente_arco_misura': float(tagliente_arco),
            'tagliente_corda_misura': float(tagliente_corda),
            'tagliente_espanso': tagliente_espanso
        }

    def _extract_general_dimensions(self) -> Dict:
        """
        Estrae dimensioni generali (lunghezza, larghezza, spessore totali).

        Returns:
            Dict con length, width, thickness
        """
        bounds_pca = np.array([
            self.vertices_pca[:, 0].max() - self.vertices_pca[:, 0].min(),
            self.vertices_pca[:, 1].max() - self.vertices_pca[:, 1].min(),
            self.vertices_pca[:, 2].max() - self.vertices_pca[:, 2].min()
        ])

        # Ordina per dimensione (maggiore = lunghezza, minore = spessore)
        sorted_bounds = np.sort(bounds_pca)[::-1]

        return {
            'length': float(sorted_bounds[0]),
            'width': float(sorted_bounds[1]),
            'thickness': float(sorted_bounds[2])
        }

    # =========================================================================
    # Metodi di default per casi edge
    # =========================================================================

    def _default_butt_features(self) -> Dict:
        return {
            'tallone_larghezza': 0.0,
            'tallone_spessore': 0.0,
            'incavo_presente': False,
            'incavo_larghezza': 0.0,
            'incavo_profondita': 0.0,
            'incavo_profilo': 'assente'
        }

    def _default_edges_features(self) -> Dict:
        return {
            'margini_rialzati_presenti': False,
            'margini_rialzati_lunghezza': 0.0,
            'margini_rialzati_spessore_max': 0.0
        }

    def _default_blade_features(self) -> Dict:
        return {
            'tagliente_larghezza': 0.0,
            'tagliente_forma': 'indeterminato',
            'tagliente_arco_misura': 0.0,
            'tagliente_corda_misura': 0.0,
            'tagliente_espanso': False
        }


# =============================================================================
# Funzioni di utilità
# =============================================================================

def extract_savignano_features(mesh_path: str, artifact_id: str,
                               weight: Optional[float] = None,
                               inventory_number: Optional[str] = None,
                               mesh_units: Optional[str] = None,
                               scale_factor: Optional[float] = None) -> Dict:
    """
    Wrapper function per estrarre features da mesh file.

    Args:
        mesh_path: Path al file mesh (.obj, .stl, .ply)
        artifact_id: ID univoco artefatto
        weight: Peso ascia in grammi (opzionale)
        inventory_number: Numero inventario (opzionale)
        mesh_units: Unità della mesh ('mm', 'cm', 'm', 'in'). Se specificato,
                   applica automaticamente il fattore di scala appropriato.
        scale_factor: Fattore di scala manuale (sovrascrive mesh_units se specificato insieme)

    Returns:
        Dict con tutti i parametri morfometrici

    Example:
        >>> # Mesh in centimetri
        >>> features = extract_savignano_features(
        ...     'axe_974.obj',
        ...     'AXE_974',
        ...     weight=387.0,
        ...     mesh_units='cm'  # Converte automaticamente cm -> mm
        ... )
        >>> print(features['incavo_presente'])
        True
    """
    try:
        logger.info(f"{artifact_id}: Loading mesh from {mesh_path}")

        # Verifica che il file esista
        import os
        if not os.path.exists(mesh_path):
            raise FileNotFoundError(f"Mesh file not found: {mesh_path}")

        # Carica mesh
        try:
            mesh = trimesh.load(mesh_path)
            logger.info(f"{artifact_id}: Mesh loaded successfully. Vertices: {len(mesh.vertices)}, Faces: {len(mesh.faces)}")
        except Exception as e:
            logger.error(f"{artifact_id}: Failed to load mesh with trimesh: {e}")
            raise ValueError(f"Could not load mesh file {mesh_path}: {e}")

        # Verifica che la mesh non sia vuota
        if len(mesh.vertices) == 0:
            raise ValueError(f"Mesh {mesh_path} is empty (0 vertices)")

        # Determina fattore di scala
        # Priorità: scale_factor > mesh_units > auto-detect
        effective_scale = 1.0

        if scale_factor is not None:
            effective_scale = scale_factor
            logger.info(f"{artifact_id}: Using manual scale factor: {effective_scale}x")
        elif mesh_units is not None:
            # Usa classe per lookup
            effective_scale = SavignanoMorphometricExtractor.SCALE_FACTORS.get(mesh_units, 1.0)
            logger.info(f"{artifact_id}: Using mesh_units='{mesh_units}' -> scale factor {effective_scale}x")
        else:
            # Auto-detect: se max dimension < 1.0, probabilmente in metri
            # NumPy 2.0 compatibility: use np.ptp() instead of .ptp()
            max_dimension = np.ptp(mesh.bounds, axis=0).max()
            logger.info(f"{artifact_id}: Max dimension before scaling: {max_dimension:.4f}")

            if max_dimension < 1.0:  # Probabilmente in metri
                effective_scale = 1000.0
                logger.info(f"{artifact_id}: Auto-detected meters, applying 1000x scale")
            elif max_dimension < 10.0:  # Probabilmente in centimetri
                effective_scale = 10.0
                logger.info(f"{artifact_id}: Auto-detected centimeters, applying 10x scale")

        # Applica scala alla mesh
        if effective_scale != 1.0:
            mesh.apply_scale(effective_scale)
            logger.info(f"{artifact_id}: Mesh scalata (new max: {np.ptp(mesh.bounds, axis=0).max():.2f}mm)")

        # Estrai features (non passiamo scale_factor perché già applicato alla mesh)
        logger.info(f"{artifact_id}: Starting feature extraction...")
        extractor = SavignanoMorphometricExtractor(mesh, artifact_id)
        features = extractor.extract_all_features()

        # Aggiungi metadati
        features['artifact_id'] = artifact_id

        if weight is not None:
            features['peso'] = float(weight)
        else:
            logger.warning(f"{artifact_id}: No weight provided, setting peso=0")
            features['peso'] = 0.0

        if inventory_number is not None:
            features['inventory_number'] = inventory_number
        else:
            features['inventory_number'] = artifact_id

        logger.info(f"{artifact_id}: Feature extraction completed successfully")
        return features

    except Exception as e:
        logger.error(f"{artifact_id}: Errore estrazione features: {type(e).__name__}: {e}", exc_info=True)
        raise


def batch_extract_savignano_features(mesh_directory: str,
                                     weights_dict: Optional[Dict[str, float]] = None,
                                     inventory_dict: Optional[Dict[str, str]] = None) -> List[Dict]:
    """
    Estrae features da multiple mesh in batch.

    Args:
        mesh_directory: Directory contenente file mesh
        weights_dict: Dict {artifact_id: weight_in_grams}
        inventory_dict: Dict {artifact_id: inventory_number}

    Returns:
        List di Dict con features per ogni ascia

    Example:
        >>> weights = {'AXE_974': 387.0, 'AXE_942': 413.0}
        >>> inventory = {'AXE_974': '974', 'AXE_942': '942'}
        >>> results = batch_extract_savignano_features(
        ...     '/path/to/meshes/',
        ...     weights_dict=weights,
        ...     inventory_dict=inventory
        ... )
    """
    import os
    from pathlib import Path

    mesh_dir = Path(mesh_directory)
    results = []
    errors = []  # Track errors for summary

    # Verifica che la directory esista
    if not mesh_dir.exists():
        raise ValueError(f"Mesh directory does not exist: {mesh_directory}")

    if not mesh_dir.is_dir():
        raise ValueError(f"Path is not a directory: {mesh_directory}")

    # Trova tutti i file mesh
    mesh_files = list(mesh_dir.glob('*.obj')) + list(mesh_dir.glob('*.stl')) + list(mesh_dir.glob('*.ply'))

    logger.info(f"Trovati {len(mesh_files)} file mesh in {mesh_directory}")

    if len(mesh_files) == 0:
        logger.warning(f"No mesh files found in {mesh_directory}. Looking for .obj, .stl, .ply files.")
        # List all files to help debug
        all_files = list(mesh_dir.glob('*'))
        logger.warning(f"All files in directory: {[f.name for f in all_files[:10]]}")

    for i, mesh_file in enumerate(mesh_files, 1):
        # Estrai artifact_id da nome file
        artifact_id = mesh_file.stem

        logger.info(f"Processing {i}/{len(mesh_files)}: {artifact_id}")

        weight = weights_dict.get(artifact_id) if weights_dict else None
        inventory_num = inventory_dict.get(artifact_id) if inventory_dict else None

        if weights_dict and weight is None:
            logger.warning(f"{artifact_id}: No weight found in weights_dict")

        try:
            features = extract_savignano_features(
                str(mesh_file),
                artifact_id,
                weight=weight,
                inventory_number=inventory_num
            )
            results.append(features)
            logger.info(f"{artifact_id}: ✓ Features estratte con successo")

        except Exception as e:
            error_msg = f"{artifact_id}: ✗ ERRORE: {type(e).__name__}: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append({'artifact_id': artifact_id, 'error': str(e), 'error_type': type(e).__name__})
            continue

    logger.info(f"Batch completato: {len(results)}/{len(mesh_files)} successo, {len(errors)} falliti")

    if errors:
        logger.error(f"Errori durante estrazione:")
        for error in errors:
            logger.error(f"  - {error['artifact_id']}: {error['error_type']}: {error['error']}")

    if len(results) == 0 and len(mesh_files) > 0:
        raise ValueError(
            f"Feature extraction failed for all {len(mesh_files)} meshes. "
            f"Check the logs above for detailed error messages. "
            f"Common issues: mesh files corrupted, wrong format, or missing dependencies."
        )

    return results