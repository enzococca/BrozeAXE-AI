#!/usr/bin/env python3
"""
Savignano Prompt Formatter
Formats Savignano morphometric features for AI analysis prompts.
"""

from typing import Dict, Any, Optional


class SavignanoPromptFormatter:
    """
    Formatter for Savignano morphometric features to be included in AI prompts.
    """

    @staticmethod
    def format_for_ai_prompt(features: Dict[str, Any]) -> str:
        """
        Format Savignano features into a human-readable text block for AI prompts.

        Args:
            features: Dictionary containing Savignano morphometric features

        Returns:
            Formatted string suitable for inclusion in AI prompts
        """
        sav = features.get('savignano', {})

        if not sav or not isinstance(sav, dict):
            return "No detailed morphometric analysis available."

        # Build formatted text
        lines = []
        lines.append("=== MORPHOMETRIC ANALYSIS (Savignano Method) ===")
        lines.append("")

        # 1. Socket (Incavo) Analysis
        incavo_presente = sav.get('incavo_presente', False)
        lines.append(f"**Socket (Incavo):** {'PRESENT' if incavo_presente else 'ABSENT'}")

        if incavo_presente:
            incavo_larghezza = sav.get('incavo_larghezza', 0)
            incavo_profondita = sav.get('incavo_profondita', 0)
            lines.append(f"  - Width: {incavo_larghezza:.2f} mm")
            lines.append(f"  - Depth: {incavo_profondita:.2f} mm")
        lines.append("")

        # 2. Raised Flanges (Margini Rialzati) Analysis
        margini_presenti = sav.get('margini_rialzati_presenti', False)
        lines.append(f"**Raised Flanges (Margini Rialzati):** {'PRESENT' if margini_presenti else 'ABSENT'}")

        if margini_presenti:
            margini_lunghezza = sav.get('margini_rialzati_lunghezza', 0)
            margini_spessore = sav.get('margini_rialzati_spessore_max', 0)
            lines.append(f"  - Length: {margini_lunghezza:.2f} mm")
            lines.append(f"  - Max thickness: {margini_spessore:.2f} mm")
        lines.append("")

        # 3. Blade (Tagliente) Analysis
        tagliente_forma = sav.get('tagliente_forma', 'unknown')
        tagliente_espanso = sav.get('tagliente_espanso', False)
        tagliente_larghezza = sav.get('tagliente_larghezza', 0)

        lines.append(f"**Blade (Tagliente):** {tagliente_forma.capitalize()}")
        lines.append(f"  - Width: {tagliente_larghezza:.2f} mm")
        lines.append(f"  - Expanded: {'Yes' if tagliente_espanso else 'No'}")
        lines.append("")

        # 4. Butt (Tallone) Measurements
        tallone_larghezza = sav.get('tallone_larghezza', 0)
        tallone_spessore = sav.get('tallone_spessore', 0)

        lines.append(f"**Butt (Tallone):**")
        lines.append(f"  - Width: {tallone_larghezza:.2f} mm")
        lines.append(f"  - Thickness: {tallone_spessore:.2f} mm")
        lines.append("")

        # 5. Overall Dimensions
        length = sav.get('length', 0)
        width = sav.get('width', 0)
        thickness = sav.get('thickness', 0)

        lines.append(f"**Overall Dimensions:**")
        lines.append(f"  - Length: {length:.2f} mm")
        lines.append(f"  - Max Width: {width:.2f} mm")
        lines.append(f"  - Max Thickness: {thickness:.2f} mm")
        lines.append("")

        # 6. Weight
        peso = sav.get('peso', 0)
        if peso > 0:
            lines.append(f"**Weight:** {peso:.1f} grams")
        else:
            lines.append(f"**Weight:** Not measured")
        lines.append("")

        # 7. Matrix Classification (if available)
        matrix_id = sav.get('matrix_id', 'Unknown')
        if matrix_id and matrix_id != 'Unknown':
            lines.append(f"**Matrix Classification:** {matrix_id}")
            lines.append("")

        # 8. Fusion Relationships (if available)
        fusion_estimates = sav.get('fusion_estimates', [])
        if fusion_estimates:
            lines.append(f"**Potential Matrix Relationships:**")
            for fusion in fusion_estimates[:3]:  # Show top 3
                related_axe = fusion.get('related_axe', 'Unknown')
                similarity = fusion.get('similarity_score', 0)
                lines.append(f"  - Related to {related_axe}: {similarity:.1%} similarity")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def get_classification_hints(features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key classification hints from Savignano features.

        Args:
            features: Dictionary containing Savignano morphometric features

        Returns:
            Dictionary with classification hints
        """
        sav = features.get('savignano', {})

        if not sav or not isinstance(sav, dict):
            return {
                'is_savignano_type': False,
                'confidence': 0.0,
                'characteristics': []
            }

        # Check for Savignano type characteristics
        has_socket = sav.get('incavo_presente', False)
        has_raised_flanges = sav.get('margini_rialzati_presenti', False)
        is_lunate_blade = sav.get('tagliente_forma') == 'lunato'

        characteristics = []
        confidence = 0.0

        if has_socket:
            characteristics.append('socket_present')
            confidence += 0.35

        if has_raised_flanges:
            characteristics.append('raised_flanges')
            confidence += 0.35

        if is_lunate_blade:
            characteristics.append('lunate_blade')
            confidence += 0.30

        is_savignano_type = has_socket and has_raised_flanges and is_lunate_blade

        return {
            'is_savignano_type': is_savignano_type,
            'confidence': confidence,
            'characteristics': characteristics,
            'matrix_id': sav.get('matrix_id', 'Unknown'),
            'socketed_axe_subtype': 'Savignano Type' if is_savignano_type else None
        }

    @staticmethod
    def create_classification_prompt_section(features: Dict[str, Any]) -> str:
        """
        Create a specific prompt section for classification guidance.

        Args:
            features: Dictionary containing Savignano morphometric features

        Returns:
            Formatted classification guidance string
        """
        hints = SavignanoPromptFormatter.get_classification_hints(features)

        if not hints['is_savignano_type']:
            return ""

        lines = []
        lines.append("=== CLASSIFICATION GUIDANCE ===")
        lines.append("")
        lines.append("Based on morphometric analysis, this artifact exhibits characteristics of:")
        lines.append("")
        lines.append("**Savignano Type Bronze Axe**")
        lines.append(f"Confidence: {hints['confidence']:.0%}")
        lines.append("")
        lines.append("Key characteristics detected:")

        for char in hints['characteristics']:
            char_display = char.replace('_', ' ').title()
            lines.append(f"  ✓ {char_display}")

        lines.append("")

        if hints['matrix_id'] and hints['matrix_id'] != 'Unknown':
            lines.append(f"Matrix Classification: {hints['matrix_id']}")
            lines.append("")

        lines.append("Please consider this morphometric evidence when classifying this artifact.")
        lines.append("If you determine this is indeed a Savignano type, suggest:")
        lines.append("  1. Primary Type: Socketed Axe")
        lines.append("  2. Subtype: Savignano Type")
        lines.append(f"  3. Matrix Subclass: {hints['matrix_id']}")
        lines.append("")

        return "\n".join(lines)


def format_savignano_features_for_ai(features: Dict[str, Any]) -> str:
    """
    Convenience function to format Savignano features for AI prompt.

    Args:
        features: Dictionary containing artifact features

    Returns:
        Formatted string for AI prompt
    """
    formatter = SavignanoPromptFormatter()
    return formatter.format_for_ai_prompt(features)


def get_savignano_classification_hints(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to get classification hints.

    Args:
        features: Dictionary containing artifact features

    Returns:
        Dictionary with classification hints
    """
    formatter = SavignanoPromptFormatter()
    return formatter.get_classification_hints(features)


# Example usage
if __name__ == "__main__":
    # Test with sample Savignano features
    sample_features = {
        'savignano': {
            'artifact_id': 'axe974',
            'incavo_presente': True,
            'incavo_larghezza': 45.2,
            'incavo_profondita': 12.3,
            'margini_rialzati_presenti': True,
            'margini_rialzati_lunghezza': 85.4,
            'margini_rialzati_spessore_max': 8.7,
            'tagliente_forma': 'lunato',
            'tagliente_espanso': True,
            'tagliente_larghezza': 98.6,
            'tallone_larghezza': 42.1,
            'tallone_spessore': 15.6,
            'length': 165.3,
            'width': 98.6,
            'thickness': 28.9,
            'peso': 387.0,
            'matrix_id': 'MAT_A'
        }
    }

    print("=== Savignano Prompt Formatter Test ===\n")

    # Format for AI prompt
    formatted = format_savignano_features_for_ai(sample_features)
    print(formatted)
    print("\n" + "=" * 60 + "\n")

    # Get classification hints
    hints = get_savignano_classification_hints(sample_features)
    print("Classification Hints:")
    print(f"  Is Savignano Type: {hints['is_savignano_type']}")
    print(f"  Confidence: {hints['confidence']:.0%}")
    print(f"  Characteristics: {', '.join(hints['characteristics'])}")
    print(f"  Matrix ID: {hints['matrix_id']}")
    print("\n" + "=" * 60 + "\n")

    # Create classification guidance
    formatter = SavignanoPromptFormatter()
    guidance = formatter.create_classification_prompt_section(sample_features)
    print(guidance)
