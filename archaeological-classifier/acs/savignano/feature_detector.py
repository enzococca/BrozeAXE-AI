#!/usr/bin/env python3
"""
Savignano Feature Detector
Automatically determines if an artifact should undergo Savignano morphometric analysis.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SavignanoFeatureDetector:
    """
    Detector to automatically identify artifacts that should undergo Savignano analysis.
    """

    # Keywords indicating Bronze Age axe
    AXE_KEYWORDS = ['axe', 'ascia', 'hache', 'axt', 'hacha']
    BRONZE_KEYWORDS = ['bronze', 'bronzo', 'bronce', 'edad del bronce', 'bronze age']

    # Keywords indicating Savignano type characteristics
    SAVIGNANO_KEYWORDS = ['savignano', 'incavo', 'socket', 'socketed', 'tallone', 'margini rialzati']

    def should_extract_savignano(
        self,
        artifact_data: Optional[Dict[str, Any]] = None,
        artifact_id: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        material: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Determine if Savignano morphometric analysis should be performed.

        Args:
            artifact_data: Complete artifact data dict (optional)
            artifact_id: Artifact identifier (optional)
            category: Artifact category (optional)
            description: Artifact description (optional)
            material: Artifact material (optional)
            **kwargs: Additional metadata

        Returns:
            Dict with keys:
                - should_extract (bool): True if Savignano analysis should run
                - confidence (float): Confidence level (0.0 to 1.0)
                - reason (str): Human-readable reason for decision
                - criteria_matched (list): List of matched criteria
        """
        # Parse input
        if artifact_data:
            artifact_id = artifact_data.get('artifact_id') or artifact_data.get('id')
            category = artifact_data.get('category')
            description = artifact_data.get('description', '')
            material = artifact_data.get('material', '')

        # Normalize strings
        artifact_id_lower = (artifact_id or '').lower()
        category_lower = (category or '').lower()
        description_lower = (description or '').lower()
        material_lower = (material or '').lower()

        # Combine all text for analysis
        all_text = f"{artifact_id_lower} {category_lower} {description_lower} {material_lower}"

        # Criteria scoring
        criteria_matched = []
        confidence_score = 0.0

        # 1. Check if it's an axe (REQUIRED)
        is_axe = any(kw in all_text for kw in self.AXE_KEYWORDS)

        if not is_axe:
            return {
                'should_extract': False,
                'confidence': 0.0,
                'reason': 'Not an axe artifact',
                'criteria_matched': []
            }

        criteria_matched.append('is_axe')
        confidence_score += 0.3

        # 2. Check if Bronze Age (HIGHLY RECOMMENDED)
        is_bronze = any(kw in all_text for kw in self.BRONZE_KEYWORDS)

        if is_bronze:
            criteria_matched.append('bronze_age_material')
            confidence_score += 0.4
        else:
            # Still proceed if other criteria match, but lower confidence
            logger.info(f"Artifact {artifact_id}: Bronze material not explicitly mentioned")

        # 3. Check for Savignano-specific indicators (OPTIONAL BUT STRONG)
        has_savignano_indicators = any(kw in all_text for kw in self.SAVIGNANO_KEYWORDS)

        if has_savignano_indicators:
            criteria_matched.append('savignano_indicators')
            confidence_score += 0.3

        # 4. Check for explicit mesh availability
        if kwargs.get('has_3d_mesh') or kwargs.get('mesh_path'):
            criteria_matched.append('has_3d_mesh')
            confidence_score += 0.1
        else:
            # Still can proceed, but note this
            logger.warning(f"Artifact {artifact_id}: No 3D mesh confirmation")

        # 5. Filename pattern check (e.g., "axe936", "ascia_974")
        if artifact_id and any(kw in artifact_id_lower for kw in self.AXE_KEYWORDS):
            criteria_matched.append('filename_pattern')
            confidence_score += 0.1

        # Decision logic
        should_extract = False
        reason = ""

        if confidence_score >= 0.7:
            # High confidence - definitely extract
            should_extract = True
            reason = "High confidence: Bronze Age axe with clear indicators"
        elif confidence_score >= 0.4:
            # Medium confidence - extract with caution
            should_extract = True
            reason = "Medium confidence: Axe artifact, Savignano analysis recommended"
        elif is_axe and confidence_score >= 0.3:
            # Low confidence - extract anyway (benefit of the doubt)
            should_extract = True
            reason = "Low confidence: Axe detected, running precautionary analysis"
        else:
            # Don't extract
            should_extract = False
            reason = "Insufficient criteria: Not likely a Bronze Age axe"

        # Log decision
        logger.info(
            f"Savignano detection for '{artifact_id}': "
            f"should_extract={should_extract}, confidence={confidence_score:.2f}, "
            f"criteria={criteria_matched}"
        )

        return {
            'should_extract': should_extract,
            'confidence': confidence_score,
            'reason': reason,
            'criteria_matched': criteria_matched
        }

    def should_extract_from_file(self, mesh_path: str, artifact_id: str) -> Dict[str, Any]:
        """
        Simplified detection based only on filename/artifact ID.
        Useful when no metadata is available yet.

        Args:
            mesh_path: Path to mesh file
            artifact_id: Artifact identifier from filename

        Returns:
            Detection result dict
        """
        mesh_path_obj = Path(mesh_path)
        filename = mesh_path_obj.stem  # filename without extension

        # Use filename as proxy for category
        return self.should_extract_savignano(
            artifact_id=artifact_id,
            category=filename,  # Use filename as category hint
            has_3d_mesh=True
        )


# Global detector instance
_detector_instance = None


def get_detector() -> SavignanoFeatureDetector:
    """Get global detector instance (singleton pattern)."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SavignanoFeatureDetector()
    return _detector_instance


def should_extract_savignano_features(
    artifact_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> bool:
    """
    Convenience function for quick detection.

    Args:
        artifact_data: Artifact data dict
        **kwargs: Additional parameters

    Returns:
        True if Savignano analysis should be performed
    """
    detector = get_detector()
    result = detector.should_extract_savignano(artifact_data=artifact_data, **kwargs)
    return result['should_extract']


# Example usage
if __name__ == "__main__":
    # Test cases
    detector = SavignanoFeatureDetector()

    test_cases = [
        {
            'artifact_id': 'axe974',
            'category': 'axe',
            'description': 'Bronze Age socketed axe from Savignano',
            'material': 'bronze'
        },
        {
            'artifact_id': 'pottery_shard_123',
            'category': 'ceramic',
            'description': 'Neolithic pottery fragment',
            'material': 'clay'
        },
        {
            'artifact_id': 'ascia_942',
            'category': 'weapon',
            'description': 'Ascia di bronzo con incavo',
            'material': 'bronzo'
        },
        {
            'artifact_id': 'generic_axe',
            'category': 'axe',
            'description': 'Generic axe',
            'material': 'unknown'
        }
    ]

    print("=== Savignano Feature Detector Test ===\n")
    for i, test in enumerate(test_cases, 1):
        result = detector.should_extract_savignano(artifact_data=test)
        print(f"Test Case {i}: {test['artifact_id']}")
        print(f"  Should Extract: {result['should_extract']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Reason: {result['reason']}")
        print(f"  Criteria: {result['criteria_matched']}")
        print()
