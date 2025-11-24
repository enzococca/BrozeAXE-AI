"""
Savignano Analysis Package
===========================

Sistema completo per analisi archeologica delle asce del ripostiglio di Savignano.

Moduli:
-------
- morphometric_extractor: Estrazione parametri morfometrici specifici
- matrix_analyzer: Identificazione matrici e analisi fusioni
- archaeological_qa: Risposte alle 6 domande archeologiche chiave

Usage:
------
```python
from acs.savignano import SavignanoWorkflow

# Workflow completo
workflow = SavignanoWorkflow(
    mesh_directory='/path/to/meshes',
    weights_file='/path/to/weights.json',
    output_directory='/path/to/output'
)

# Esegui analisi completa
results = workflow.run_complete_analysis()

# Esporta risultati
workflow.export_results()
```

Autore: Archaeological Classifier System
Data: Novembre 2025
"""

from .morphometric_extractor import (
    SavignanoMorphometricExtractor,
    extract_savignano_features,
    batch_extract_savignano_features
)

from .matrix_analyzer import MatrixAnalyzer

from .archaeological_qa import SavignanoArchaeologicalQA

__all__ = [
    'SavignanoMorphometricExtractor',
    'extract_savignano_features',
    'batch_extract_savignano_features',
    'MatrixAnalyzer',
    'SavignanoArchaeologicalQA',
    'SavignanoWorkflow'
]

__version__ = '1.0.0'