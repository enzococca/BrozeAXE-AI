"""
Archaeological Classifier System (ACS)
=====================================

A comprehensive system for 3D mesh analysis, morphometric classification,
and formal taxonomy for archaeological artifacts.

Features:
- 3D mesh processing (OBJ, PLY, STL)
- Advanced morphometric analysis (EFA, PCA, Procrustes)
- Formal parametric taxonomy system with versioning
- REST API for all functionalities
- MCP server for Claude Desktop integration
- Multi-agent AI system for archaeological reasoning

Author: Enzo Ferroni
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Enzo Ferroni"

from acs.core.mesh_processor import MeshProcessor
from acs.core.morphometric import MorphometricAnalyzer
from acs.core.taxonomy import FormalTaxonomySystem, TaxonomicClass, ClassificationParameter

__all__ = [
    "MeshProcessor",
    "MorphometricAnalyzer",
    "FormalTaxonomySystem",
    "TaxonomicClass",
    "ClassificationParameter",
]
