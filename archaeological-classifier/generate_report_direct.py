#!/usr/bin/env python3
"""Direct report generation script"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from acs.savignano.morphometric_extractor import extract_savignano_features
from acs.savignano.comprehensive_report import generate_comprehensive_report

# Configuration
ARTIFACT_ID = "axe974"
MESH_PATH = "/Users/enzo/.acs/savignano_meshes/axe974.obj"
OUTPUT_DIR = "/Users/enzo/.acs/reports/axe974"

def main():
    print(f"Generating comprehensive report for {ARTIFACT_ID}...")
    print(f"Mesh: {MESH_PATH}")
    print(f"Output dir: {OUTPUT_DIR}")

    # Extract features with latest code
    print("\nExtracting morphometric features...")
    features = extract_savignano_features(Path(MESH_PATH), ARTIFACT_ID)

    print("\nExtracted features:")
    print(f"  Incavo larghezza: {features.get('incavo_larghezza_mm', 'N/A')} mm")
    print(f"  Incavo profondità: {features.get('incavo_profondita_mm', 'N/A')} mm")
    print(f"  Tallone larghezza: {features.get('tallone_larghezza_mm', 'N/A')} mm")
    print(f"  Tallone spessore: {features.get('tallone_spessore_mm', 'N/A')} mm")
    print(f"  Tagliente larghezza: {features.get('tagliente_larghezza_mm', 'N/A')} mm")

    # Generate comprehensive report
    print("\nGenerating PDF report...")
    result = generate_comprehensive_report(
        mesh_path=MESH_PATH,
        features=features,
        output_dir=OUTPUT_DIR,
        artifact_id=ARTIFACT_ID,
        language='it'
    )

    pdf_path = Path(result['pdf_path'])
    print(f"\n✓ Report generated: {pdf_path}")
    print(f"  File size: {pdf_path.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
