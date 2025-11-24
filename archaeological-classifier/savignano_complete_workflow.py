"""
Savignano Complete Workflow
============================

Script completo per analisi archeologica delle 96 asce di Savignano.

Questo script esegue l'intero workflow:
1. Importa dati pesi dalle note di scansione
2. Estrae parametri morfometrici dalle mesh 3D
3. Identifica matrici di fusione tramite clustering
4. Analizza fusioni per matrice
5. Risponde alle 6 domande archeologiche chiave
6. Genera interpretazione AI con Claude
7. Esporta tutti i risultati

Autore: Archaeological Classifier System
Data: Novembre 2025

Usage:
------
python savignano_complete_workflow.py \\
    --meshes /path/to/meshes/ \\
    --output /path/to/output/ \\
    --weights /path/to/weights.json \\
    --anthropic-api-key YOUR_KEY
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime

# Aggiungi path per import moduli
sys.path.insert(0, str(Path(__file__).parent))

from acs.savignano.morphometric_extractor import (
    batch_extract_savignano_features
)
from acs.savignano.matrix_analyzer import MatrixAnalyzer
from acs.savignano.archaeological_qa import SavignanoArchaeologicalQA

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SavignanoCompleteWorkflow:
    """
    Workflow completo per analisi asce Savignano.

    Coordina tutti i moduli e gestisce il flusso di dati completo.
    """

    def __init__(self,
                 mesh_directory: str,
                 output_directory: str,
                 weights_data: Optional[Dict] = None,
                 inventory_data: Optional[Dict] = None,
                 anthropic_api_key: Optional[str] = None):
        """
        Inizializza workflow.

        Args:
            mesh_directory: Directory contenente file mesh (.obj, .stl, .ply)
            output_directory: Directory per risultati
            weights_data: Dict {artifact_id: weight_grams} (opzionale)
            inventory_data: Dict {artifact_id: inventory_number} (opzionale)
            anthropic_api_key: API key Anthropic per AI (opzionale)
        """
        self.mesh_directory = Path(mesh_directory)
        self.output_directory = Path(output_directory)
        self.weights_data = weights_data or {}
        self.inventory_data = inventory_data or {}
        self.anthropic_api_key = anthropic_api_key

        # Crea output directory
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Sottodirectory per organizzazione
        self.features_dir = self.output_directory / 'features'
        self.matrices_dir = self.output_directory / 'matrices'
        self.qa_dir = self.output_directory / 'archaeological_qa'
        self.visualizations_dir = self.output_directory / 'visualizations'

        for dir in [self.features_dir, self.matrices_dir, self.qa_dir, self.visualizations_dir]:
            dir.mkdir(exist_ok=True)

        self.features_df = None
        self.matrix_analyzer = None
        self.qa_analyzer = None

        logger.info(f"SavignanoCompleteWorkflow inizializzato")
        logger.info(f"  Mesh directory: {self.mesh_directory}")
        logger.info(f"  Output directory: {self.output_directory}")

    def run_complete_analysis(self) -> Dict:
        """
        Esegue workflow completo.

        Steps:
        1. Estrazione features morfometriche
        2. Identificazione matrici
        3. Analisi fusioni
        4. Risposte domande archeologiche
        5. Interpretazione AI
        6. Export risultati

        Returns:
            Dict con tutti i risultati
        """
        logger.info("=" * 80)
        logger.info("INIZIO WORKFLOW COMPLETO - ASCE SAVIGNANO")
        logger.info("=" * 80)

        results = {}

        # STEP 1: Estrazione features
        logger.info("\n[STEP 1/5] Estrazione parametri morfometrici...")
        features_results = self._step_1_extract_features()
        results['features'] = features_results

        # STEP 2: Identificazione matrici
        logger.info("\n[STEP 2/5] Identificazione matrici di fusione...")
        matrices_results = self._step_2_identify_matrices()
        results['matrices'] = matrices_results

        # STEP 3: Analisi fusioni
        logger.info("\n[STEP 3/5] Analisi fusioni per matrice...")
        fusions_results = self._step_3_analyze_fusions()
        results['fusions'] = fusions_results

        # STEP 4: Domande archeologiche
        logger.info("\n[STEP 4/5] Risposta domande archeologiche...")
        qa_results = self._step_4_archaeological_questions()
        results['archaeological_qa'] = qa_results

        # STEP 5: Visualizzazioni
        logger.info("\n[STEP 5/5] Generazione visualizzazioni...")
        viz_results = self._step_5_visualizations()
        results['visualizations'] = viz_results

        # Export risultati finali
        logger.info("\nExport risultati finali...")
        self._export_final_results(results)

        logger.info("\n" + "=" * 80)
        logger.info("WORKFLOW COMPLETATO CON SUCCESSO")
        logger.info("=" * 80)
        logger.info(f"\nRisultati disponibili in: {self.output_directory}")

        return results

    def _step_1_extract_features(self) -> Dict:
        """
        STEP 1: Estrae features morfometriche da tutte le mesh.

        Returns:
            Dict con statistiche estrazione
        """
        logger.info(f"Scansionando directory mesh: {self.mesh_directory}")

        # Batch extraction
        features_list = batch_extract_savignano_features(
            str(self.mesh_directory),
            weights_dict=self.weights_data,
            inventory_dict=self.inventory_data
        )

        # Converti a DataFrame
        self.features_df = pd.DataFrame(features_list)

        logger.info(f"Estratte features per {len(self.features_df)} asce")

        # Export features
        features_csv = self.features_dir / 'savignano_morphometric_features.csv'
        self.features_df.to_csv(features_csv, index=False)
        logger.info(f"Features salvate: {features_csv}")

        # Export JSON
        features_json = self.features_dir / 'savignano_morphometric_features.json'
        with open(features_json, 'w') as f:
            json.dump(features_list, f, indent=2)

        # Statistiche descrittive
        stats = {
            'n_axes': len(self.features_df),
            'features_extracted': list(self.features_df.columns),
            'summary_statistics': {
                'peso_medio': float(self.features_df['peso'].mean()) if 'peso' in self.features_df.columns else None,
                'peso_min': float(self.features_df['peso'].min()) if 'peso' in self.features_df.columns else None,
                'peso_max': float(self.features_df['peso'].max()) if 'peso' in self.features_df.columns else None,
                'lunghezza_media': float(self.features_df['length'].mean()),
                'incavi_presenti': int(self.features_df['incavo_presente'].sum()),
                'margini_rialzati_presenti': int(self.features_df['margini_rialzati_presenti'].sum())
            }
        }

        return stats

    def _step_2_identify_matrices(self) -> Dict:
        """
        STEP 2: Identifica matrici di fusione tramite clustering.

        Returns:
            Dict con info matrici
        """
        # Inizializza analyzer
        self.matrix_analyzer = MatrixAnalyzer(self.features_df)

        # Identifica matrici (hierarchical clustering con auto-detection n_clusters)
        matrices_result = self.matrix_analyzer.identify_matrices(
            method='hierarchical',
            max_clusters=15
        )

        logger.info(f"Identificate {matrices_result['n_matrices']} matrici")
        logger.info(f"Silhouette score: {matrices_result['silhouette_score']:.3f}")

        # Export matrix info
        matrices_json = self.matrices_dir / 'matrices_summary.json'
        with open(matrices_json, 'w') as f:
            json.dump(self.matrix_analyzer.matrices, f, indent=2)

        # Export assignments
        assignments_df = self.matrix_analyzer.get_matrix_assignments()
        assignments_csv = self.matrices_dir / 'matrix_assignments.csv'
        assignments_df.to_csv(assignments_csv, index=False)

        logger.info(f"Info matrici salvate: {matrices_json}")
        logger.info(f"Assegnazioni salvate: {assignments_csv}")

        return matrices_result

    def _step_3_analyze_fusions(self) -> Dict:
        """
        STEP 3: Analizza numero fusioni per matrice.

        Returns:
            Dict con analisi fusioni
        """
        fusions_result = self.matrix_analyzer.estimate_fusions_per_matrix()

        # Export
        fusions_json = self.matrices_dir / 'fusions_per_matrix.json'
        with open(fusions_json, 'w') as f:
            json.dump(fusions_result, f, indent=2)

        logger.info(f"Analisi fusioni salvata: {fusions_json}")

        return fusions_result

    def _step_4_archaeological_questions(self) -> Dict:
        """
        STEP 4: Risponde alle 6 domande archeologiche chiave.

        Returns:
            Dict con tutte le risposte
        """
        # Inizializza QA analyzer
        self.qa_analyzer = SavignanoArchaeologicalQA(
            matrices_info=self.matrix_analyzer.matrices,
            features_df=self.features_df,
            tech_analysis_df=None,  # TODO: aggiungere se disponibile
            anthropic_api_key=self.anthropic_api_key
        )

        # Risponde a tutte le domande
        qa_results = self.qa_analyzer.answer_all_questions()

        # Export risposte JSON
        qa_json = self.qa_dir / 'archaeological_questions_answers.json'
        with open(qa_json, 'w', encoding='utf-8') as f:
            json.dump(qa_results, f, indent=2, ensure_ascii=False)

        logger.info(f"Risposte archeologiche salvate: {qa_json}")

        # Genera report Markdown
        report_md = self.qa_dir / 'SAVIGNANO_ARCHAEOLOGICAL_REPORT.md'
        self.qa_analyzer.generate_report(str(report_md), format='markdown')

        logger.info(f"Report archeologico generato: {report_md}")

        return qa_results

    def _step_5_visualizations(self) -> Dict:
        """
        STEP 5: Genera visualizzazioni (dendrogram, PCA, etc.).

        Returns:
            Dict con paths visualizzazioni
        """
        viz_paths = {}

        try:
            # Dendrogram
            dendrogram_path = self.visualizations_dir / 'matrices_dendrogram.png'
            self.matrix_analyzer.plot_dendrogram(str(dendrogram_path))
            viz_paths['dendrogram'] = str(dendrogram_path)
            logger.info(f"Dendrogram salvato: {dendrogram_path}")

            # PCA clusters
            pca_path = self.visualizations_dir / 'matrices_pca_clusters.png'
            self.matrix_analyzer.plot_pca_clusters(str(pca_path))
            viz_paths['pca_clusters'] = str(pca_path)
            logger.info(f"PCA clusters salvato: {pca_path}")

        except Exception as e:
            logger.warning(f"Errore generazione visualizzazioni: {e}")

        return viz_paths

    def _export_final_results(self, results: Dict):
        """
        Export risultati finali consolidati.

        Args:
            results: Dict con tutti i risultati
        """
        # Summary JSON
        summary = {
            'analysis_date': datetime.now().isoformat(),
            'n_axes_analyzed': len(self.features_df),
            'n_matrices_identified': results['matrices']['n_matrices'],
            'total_fusions_estimated': results['fusions']['total_fusions'],
            'silhouette_score': results['matrices']['silhouette_score'],
            'davies_bouldin_score': results['matrices']['davies_bouldin_score'],
            'output_directory': str(self.output_directory)
        }

        summary_json = self.output_directory / 'ANALYSIS_SUMMARY.json'
        with open(summary_json, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Summary salvato: {summary_json}")

        # README
        readme_path = self.output_directory / 'README.md'
        self._generate_readme(readme_path, summary)

    def _generate_readme(self, path: Path, summary: Dict):
        """
        Genera README con indice risultati.

        Args:
            path: Path README
            summary: Summary dati
        """
        readme = f"""# Analisi Archeologica - Ripostiglio di Savignano sul Panaro

**Data analisi:** {summary['analysis_date']}

**N. asce analizzate:** {summary['n_axes_analyzed']}

## Risultati Principali

- **Matrici identificate:** {summary['n_matrices_identified']}
- **Fusioni totali stimate:** {summary['total_fusions_estimated']}
- **Qualità clustering (Silhouette):** {summary['silhouette_score']:.3f}

## Struttura Directory

```
{self.output_directory.name}/
├── features/
│   ├── savignano_morphometric_features.csv  # Features morfometriche
│   └── savignano_morphometric_features.json
│
├── matrices/
│   ├── matrices_summary.json                # Info matrici
│   ├── matrix_assignments.csv               # Assegnazioni asce->matrici
│   └── fusions_per_matrix.json              # Fusioni per matrice
│
├── archaeological_qa/
│   ├── archaeological_questions_answers.json  # Risposte 6 domande
│   └── SAVIGNANO_ARCHAEOLOGICAL_REPORT.md     # Report completo
│
├── visualizations/
│   ├── matrices_dendrogram.png              # Dendrogram clustering
│   └── matrices_pca_clusters.png            # PCA visualization
│
├── ANALYSIS_SUMMARY.json                    # Summary generale
└── README.md                                # Questo file
```

## Domande Archeologiche Affrontate

1. **Matrici di fusione:** Numero matrici, caratteristiche tecniche (mono/bivalva, incavo, margini)
2. **Fusioni per matrice:** Quante fusioni da ogni matrice
3. **Trattamenti post-fusione:** Martellatura, barra centrale, tallone
4. **Rifinitura finale:** Tagliente e tallone
5. **Funzione incavo tallone:** Ipotesi funzionali
6. **Intensità uso:** Tracce d'uso e stato conservazione

## Files Principali

### Features Morfometriche
- `features/savignano_morphometric_features.csv` - Tutti i parametri estratti

### Analisi Matrici
- `matrices/matrices_summary.json` - Dettagli matrici identificate
- `matrices/matrix_assignments.csv` - Quale ascia appartiene a quale matrice

### Report Archeologico
- `archaeological_qa/SAVIGNANO_ARCHAEOLOGICAL_REPORT.md` - **LEGGI QUESTO FILE** per interpretazione completa

## Utilizzo Dati

I dati sono strutturati per:
- Analisi statistiche avanzate
- Confronti con altri ripostigli
- Pubblicazioni scientifiche
- Integrazione con database regionali

## Contatti

Per informazioni su questa analisi, contattare:
[Inserire contatto]

## Citazione

```
Archaeological Classifier System (2025). Analisi archeologica quantitativa
del ripostiglio di Savignano sul Panaro. [Software]. Version 1.0.
```
"""

        with open(path, 'w', encoding='utf-8') as f:
            f.write(readme)

        logger.info(f"README generato: {path}")


# =============================================================================
# UTILITÀ PER IMPORTAZIONE DATI PESI
# =============================================================================

def parse_weights_from_scan_notes(notes_text: str) -> Dict[str, float]:
    """
    Estrae pesi dalle note di scansione.

    Args:
        notes_text: Testo completo note scansioni

    Returns:
        Dict {inventory_number: weight_grams}

    Example:
        >>> notes = "974: elaborazione completa. 387 g\\n942: completa. 413 g"
        >>> weights = parse_weights_from_scan_notes(notes)
        >>> print(weights)
        {'974': 387.0, '942': 413.0}
    """
    import re

    weights = {}

    # Pattern: numero inventario seguito da peso in grammi
    # Es: "974: elaborazione completa. 387 g"
    pattern = r'(\d+)(?:/\d+)?:.*?(\d+)\s*g'

    for match in re.finditer(pattern, notes_text):
        inventory_num = match.group(1)
        weight = float(match.group(2))
        weights[inventory_num] = weight

    logger.info(f"Estratti pesi per {len(weights)} asce dalle note")

    return weights


def load_weights_from_docx(docx_path: str) -> Dict[str, float]:
    """
    Carica pesi da file .docx delle note di scansione.

    Args:
        docx_path: Path al file .docx

    Returns:
        Dict {inventory_number: weight_grams}
    """
    import docx

    doc = docx.Document(docx_path)
    text = '\n'.join([p.text for p in doc.paragraphs])

    return parse_weights_from_scan_notes(text)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """
    Entry point script.
    """
    parser = argparse.ArgumentParser(
        description='Workflow completo analisi asce Savignano'
    )

    parser.add_argument(
        '--meshes',
        type=str,
        required=True,
        help='Directory contenente file mesh (.obj, .stl, .ply)'
    )

    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Directory output per risultati'
    )

    parser.add_argument(
        '--weights',
        type=str,
        help='Path file JSON con pesi {inventory_number: weight_grams} (opzionale)'
    )

    parser.add_argument(
        '--weights-docx',
        type=str,
        help='Path file DOCX note scansioni per estrarre pesi (opzionale)'
    )

    parser.add_argument(
        '--anthropic-api-key',
        type=str,
        help='API key Anthropic per interpretazione AI (opzionale, usa ANTHROPIC_API_KEY env var se non specificato)'
    )

    args = parser.parse_args()

    # Carica pesi
    weights_data = {}

    if args.weights:
        with open(args.weights, 'r') as f:
            weights_data = json.load(f)
        logger.info(f"Caricati pesi da: {args.weights}")

    elif args.weights_docx:
        weights_data = load_weights_from_docx(args.weights_docx)
        logger.info(f"Estratti pesi da: {args.weights_docx}")

    # API key
    api_key = args.anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')

    # Inizializza workflow
    workflow = SavignanoCompleteWorkflow(
        mesh_directory=args.meshes,
        output_directory=args.output,
        weights_data=weights_data,
        anthropic_api_key=api_key
    )

    # Esegui analisi completa
    try:
        results = workflow.run_complete_analysis()
        logger.info("\n✓ Analisi completata con successo!")
        return 0

    except Exception as e:
        logger.error(f"\n✗ Errore durante analisi: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())