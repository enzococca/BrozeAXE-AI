#!/usr/bin/env python3
"""
Savignano Taxonomy Rules
========================

Formal taxonomic classification rules for Savignano type Bronze Age axes.

This module defines the formal parametric taxonomy for Savignano axes
based on morphometric features extracted from 3D meshes.
"""

from typing import Dict, Optional, Tuple, List
from acs.core.taxonomy import TaxonomicClass, ClassificationParameter
from datetime import datetime


class SavignanoTaxonomy:
    """
    Taxonomy system for Savignano Bronze Age axes.

    Defines formal classification rules based on morphometric parameters.
    """

    @staticmethod
    def create_savignano_base_class() -> TaxonomicClass:
        """
        Create the base Savignano Type taxonomic class.

        Savignano Type is characterized by:
        1. Socket (incavo) present
        2. Raised flanges (margini rialzati) along body
        3. Lunate (crescent-shaped) blade
        4. Specific proportions and measurements

        Returns:
            TaxonomicClass for Savignano Type
        """
        # Morphometric parameters based on statistical analysis of known Savignano axes
        morphometric_params = {
            # Tallone (Butt) measurements
            'tallone_larghezza': ClassificationParameter(
                name='tallone_larghezza',
                value=42.0,  # Ideal value (mm)
                min_threshold=35.0,  # Min acceptable
                max_threshold=55.0,  # Max acceptable
                weight=1.0,
                measurement_unit='mm',
                tolerance=8.0  # ±8mm tolerance
            ),
            'tallone_spessore': ClassificationParameter(
                name='tallone_spessore',
                value=15.0,
                min_threshold=10.0,
                max_threshold=22.0,
                weight=1.0,
                measurement_unit='mm',
                tolerance=5.0
            ),

            # Incavo (Socket) measurements
            'incavo_larghezza': ClassificationParameter(
                name='incavo_larghezza',
                value=45.0,
                min_threshold=30.0,
                max_threshold=60.0,
                weight=1.5,  # Higher weight - critical feature
                measurement_unit='mm',
                tolerance=10.0
            ),
            'incavo_profondita': ClassificationParameter(
                name='incavo_profondita',
                value=12.0,
                min_threshold=5.0,  # Minimum depth to be considered socket
                max_threshold=25.0,
                weight=1.5,  # Higher weight - critical feature
                measurement_unit='mm',
                tolerance=7.0
            ),

            # Margini Rialzati (Raised Flanges) measurements
            'margini_rialzati_lunghezza': ClassificationParameter(
                name='margini_rialzati_lunghezza',
                value=85.0,
                min_threshold=60.0,
                max_threshold=120.0,
                weight=1.2,
                measurement_unit='mm',
                tolerance=20.0
            ),
            'margini_rialzati_spessore_max': ClassificationParameter(
                name='margini_rialzati_spessore_max',
                value=8.0,
                min_threshold=4.0,
                max_threshold=15.0,
                weight=0.8,
                measurement_unit='mm',
                tolerance=4.0
            ),

            # Tagliente (Blade) measurements
            'tagliente_larghezza': ClassificationParameter(
                name='tagliente_larghezza',
                value=95.0,
                min_threshold=75.0,
                max_threshold=130.0,
                weight=1.0,
                measurement_unit='mm',
                tolerance=15.0
            ),

            # Overall dimensions
            'length': ClassificationParameter(
                name='length',
                value=165.0,
                min_threshold=140.0,
                max_threshold=200.0,
                weight=0.8,
                measurement_unit='mm',
                tolerance=20.0
            ),
        }

        # Technological parameters (casting technique indicators)
        technological_params = {}

        # Optional boolean features (CRITICAL for Savignano type)
        optional_features = {
            'incavo_presente': True,  # Socket MUST be present
            'margini_rialzati_presenti': True,  # Raised flanges MUST be present
            'tagliente_espanso': True,  # Expanded blade typical but not mandatory
        }

        return TaxonomicClass(
            class_id='SAVIGNANO_TYPE',
            name='Savignano Type Bronze Axe',
            description=(
                'Bronze Age socketed axe characterized by socket (incavo), '
                'raised flanges (margini rialzati), and typically lunate blade. '
                'Associated with Italian Bronze Age cultures.'
            ),
            morphometric_params=morphometric_params,
            technological_params=technological_params,
            optional_features=optional_features,
            confidence_threshold=0.65,  # 65% match required
            created_date=datetime.now(),
            created_by='ACS Savignano Integration v1.0',
            validated_samples=[
                'axe936', 'axe940', 'axe942', 'axe957', 'axe965',
                'axe971', 'axe974', 'axe978', 'axe979', 'axe992'
            ]
        )

    @staticmethod
    def create_matrix_a_class() -> TaxonomicClass:
        """
        Create Matrix A subclass of Savignano Type.

        Matrix A represents a specific production matrix/mold.
        Axes from same matrix have very similar dimensions.

        Returns:
            TaxonomicClass for Savignano Matrix A
        """
        # More restrictive parameters for matrix identification
        morphometric_params = {
            'tallone_larghezza': ClassificationParameter(
                name='tallone_larghezza',
                value=42.1,
                min_threshold=40.0,
                max_threshold=44.0,
                weight=1.5,
                measurement_unit='mm',
                tolerance=1.5
            ),
            'incavo_larghezza': ClassificationParameter(
                name='incavo_larghezza',
                value=45.2,
                min_threshold=43.0,
                max_threshold=47.5,
                weight=2.0,
                measurement_unit='mm',
                tolerance=2.0
            ),
            'tagliente_larghezza': ClassificationParameter(
                name='tagliente_larghezza',
                value=98.6,
                min_threshold=95.0,
                max_threshold=102.0,
                weight=1.5,
                measurement_unit='mm',
                tolerance=3.0
            ),
            'length': ClassificationParameter(
                name='length',
                value=165.3,
                min_threshold=160.0,
                max_threshold=170.0,
                weight=1.2,
                measurement_unit='mm',
                tolerance=4.0
            ),
        }

        optional_features = {
            'incavo_presente': True,
            'margini_rialzati_presenti': True,
            'tagliente_espanso': True,
        }

        return TaxonomicClass(
            class_id='SAVIGNANO_MATRIX_A',
            name='Savignano Type - Matrix A',
            description=(
                'Savignano axes from Matrix A production mold. '
                'Characterized by specific dimensional consistency.'
            ),
            morphometric_params=morphometric_params,
            technological_params={},
            optional_features=optional_features,
            confidence_threshold=0.80,  # Higher threshold for matrix match
            created_date=datetime.now(),
            created_by='ACS Savignano Integration v1.0',
            validated_samples=['axe974', 'axe942']  # Known Matrix A examples
        )

    @staticmethod
    def create_all_classes() -> Dict[str, TaxonomicClass]:
        """
        Create all Savignano taxonomic classes.

        Returns:
            Dictionary mapping class_id to TaxonomicClass
        """
        return {
            'SAVIGNANO_TYPE': SavignanoTaxonomy.create_savignano_base_class(),
            'SAVIGNANO_MATRIX_A': SavignanoTaxonomy.create_matrix_a_class(),
            # More matrices can be added as they are identified:
            # 'SAVIGNANO_MATRIX_B': ...
            # 'SAVIGNANO_MATRIX_C': ...
        }


class SavignanoClassifier:
    """
    Classifier for Savignano axes using formal taxonomy rules.
    """

    def __init__(self):
        """Initialize classifier with Savignano taxonomic classes."""
        self.classes = SavignanoTaxonomy.create_all_classes()

    def classify_from_savignano_features(self, savignano_features: Dict) -> Dict:
        """
        Classify artifact using Savignano morphometric features.

        Args:
            savignano_features: Dictionary of Savignano morphometric features

        Returns:
            Classification result with type, confidence, and diagnostics
        """
        if not savignano_features:
            return {
                'classified': False,
                'reason': 'No Savignano features available',
                'confidence': 0.0
            }

        # Quick pre-check: Must have socket, flanges, and lunate blade
        if not self._passes_savignano_criteria(savignano_features):
            return {
                'classified': False,
                'reason': 'Does not meet basic Savignano criteria',
                'type': None,
                'confidence': 0.0,
                'missing_features': self._get_missing_features(savignano_features)
            }

        # Try to classify - start with most specific (Matrix A) then base type
        results = []

        for class_id, taxonomic_class in self.classes.items():
            is_member, confidence, diagnostic = taxonomic_class.classify_object(
                savignano_features
            )

            results.append({
                'class_id': class_id,
                'class_name': taxonomic_class.name,
                'is_member': is_member,
                'confidence': confidence,
                'diagnostic': diagnostic
            })

        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)

        # Find best match
        best_match = results[0]

        if best_match['is_member']:
            return {
                'classified': True,
                'type': best_match['class_name'],
                'class_id': best_match['class_id'],
                'confidence': best_match['confidence'],
                'diagnostic': best_match['diagnostic'],
                'all_results': results
            }
        else:
            # Check if it's close to being Savignano type
            base_type_result = next(
                (r for r in results if r['class_id'] == 'SAVIGNANO_TYPE'),
                None
            )

            if base_type_result and base_type_result['confidence'] >= 0.5:
                return {
                    'classified': False,
                    'type': 'Possible Savignano Type',
                    'class_id': 'SAVIGNANO_TYPE',
                    'confidence': base_type_result['confidence'],
                    'reason': 'Below confidence threshold but shows Savignano characteristics',
                    'diagnostic': base_type_result['diagnostic'],
                    'all_results': results
                }
            else:
                return {
                    'classified': False,
                    'type': None,
                    'confidence': best_match['confidence'],
                    'reason': 'Does not match Savignano type parameters',
                    'all_results': results
                }

    def classify_from_full_features(self, features: Dict) -> Dict:
        """
        Classify from full feature dictionary (extracts Savignano features).

        Args:
            features: Full feature dictionary

        Returns:
            Classification result
        """
        savignano_features = features.get('savignano', {})
        return self.classify_from_savignano_features(savignano_features)

    def _passes_savignano_criteria(self, features: Dict) -> bool:
        """
        Check if artifact meets basic Savignano criteria.

        Args:
            features: Savignano features dictionary

        Returns:
            True if meets basic criteria
        """
        # Must have socket
        if not features.get('incavo_presente', False):
            return False

        # Must have raised flanges
        if not features.get('margini_rialzati_presenti', False):
            return False

        # Blade shape should be lunate (preferred but not absolutely required)
        # tagliente_forma = features.get('tagliente_forma', '')
        # if tagliente_forma != 'lunato':
        #     return False

        return True

    def _get_missing_features(self, features: Dict) -> List[str]:
        """
        Get list of missing critical features.

        Args:
            features: Savignano features dictionary

        Returns:
            List of missing feature names
        """
        missing = []

        if not features.get('incavo_presente', False):
            missing.append('socket (incavo)')

        if not features.get('margini_rialzati_presenti', False):
            missing.append('raised flanges (margini rialzati)')

        if features.get('tagliente_forma', '') != 'lunato':
            missing.append('lunate blade (tagliente lunato)')

        return missing


def classify_savignano_artifact(artifact_id: str, features: Dict) -> Dict:
    """
    Convenience function to classify a Savignano artifact.

    Args:
        artifact_id: Artifact identifier
        features: Feature dictionary (can be full features or just Savignano)

    Returns:
        Classification result dictionary
    """
    classifier = SavignanoClassifier()

    # Check if features contain 'savignano' key or are already Savignano features
    if 'savignano' in features:
        result = classifier.classify_from_full_features(features)
    else:
        result = classifier.classify_from_savignano_features(features)

    result['artifact_id'] = artifact_id
    return result


# Example usage and testing
if __name__ == "__main__":
    print("=== Savignano Taxonomy Rules Test ===\n")

    # Test with known Savignano axe (axe974 features)
    test_features = {
        'tallone_larghezza': 42.1,
        'tallone_spessore': 15.6,
        'incavo_presente': True,
        'incavo_larghezza': 45.2,
        'incavo_profondita': 12.3,
        'margini_rialzati_presenti': True,
        'margini_rialzati_lunghezza': 85.4,
        'margini_rialzati_spessore_max': 8.7,
        'tagliente_forma': 'lunato',
        'tagliente_espanso': True,
        'tagliente_larghezza': 98.6,
        'length': 165.3,
        'peso': 387.0
    }

    result = classify_savignano_artifact('test_axe_974', test_features)

    print(f"Artifact: {result['artifact_id']}")
    print(f"Classified: {result['classified']}")
    print(f"Type: {result.get('type', 'N/A')}")
    print(f"Confidence: {result['confidence']:.2%}")

    if result.get('diagnostic'):
        print("\nDiagnostic Details:")
        for param, details in result['diagnostic'].items():
            print(f"  {param}: {details}")

    print("\n" + "=" * 60)

    # Test with non-Savignano axe (missing socket)
    test_features_2 = {
        'tallone_larghezza': 42.0,
        'incavo_presente': False,  # No socket!
        'margini_rialzati_presenti': True,
        'tagliente_forma': 'dritto',
        'tagliente_larghezza': 85.0,
        'length': 150.0
    }

    result2 = classify_savignano_artifact('test_generic_axe', test_features_2)

    print(f"\nArtifact: {result2['artifact_id']}")
    print(f"Classified: {result2['classified']}")
    print(f"Reason: {result2.get('reason', 'N/A')}")
    print(f"Missing Features: {result2.get('missing_features', [])}")
