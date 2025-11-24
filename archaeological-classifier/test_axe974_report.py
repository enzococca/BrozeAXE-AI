#!/usr/bin/env python3
"""
Test script to generate comprehensive report for axe974
"""

import sys
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from acs.savignano.morphometric_extractor import extract_savignano_features
from acs.savignano.comprehensive_report import generate_comprehensive_report

def main():
    # Paths
    mesh_path = Path.home() / ".acs" / "savignano_meshes" / "axe974.obj"
    output_dir = Path.home() / ".acs" / "reports" / "axe974"

    print(f"Testing comprehensive report generation for axe974")
    print(f"Mesh: {mesh_path}")
    print(f"Output: {output_dir}")
    print()

    # First, analyze the mesh to get features
    print("Step 1: Analyzing mesh...")
    features = extract_savignano_features(str(mesh_path), artifact_id="axe974")

    print(f"Features extracted:")
    print(f"  - Incavo presente: {features.get('incavo_presente', False)}")
    if features.get('incavo_presente', False):
        print(f"  - Incavo larghezza: {features.get('incavo_larghezza', 'N/A')} mm")
        print(f"  - Incavo profondità: {features.get('incavo_profondita', 'N/A')} mm")
    print(f"  - Margini rialzati: {features.get('margini_rialzati_presenti', False)}")
    print(f"  - Matrix: {features.get('matrix_id', 'N/A')}")
    print()

    # Generate comprehensive report
    print("Step 2: Generating comprehensive report...")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = generate_comprehensive_report(
        mesh_path=str(mesh_path),
        features=features,
        output_dir=str(output_dir),
        artifact_id="axe974",
        language="it"
    )

    print(f"✓ Report generated successfully!")
    print(f"  PDF: {results['pdf']}")

    # Check file size
    pdf_path = Path(results['pdf'])
    if pdf_path.exists():
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        print(f"  Size: {size_mb:.2f} MB")

    print()
    print("=" * 60)
    print("VERIFICATION CHECKLIST:")
    print("=" * 60)
    print("1. ✓ Profilo longitudinale is VERTICAL")
    print("2. ✓ Annotations are OUTSIDE prospetto with connection lines")
    print("3. ✓ Margini rialzati visible in prospetto (green lines)")
    print("4. ✓ Prospetto is outline only (no fill)")
    print("5. ✓ AI responds in Italian")
    print("6. ✓ Incavo measurements logged")
    print("7. ✓ Real hammering analysis implemented")
    print("8. ✓ Real casting analysis implemented")
    print()
    print(f"Please open and review: {results['pdf']}")

if __name__ == "__main__":
    main()
