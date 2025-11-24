#!/usr/bin/env python3
"""
Test Script for Technical Drawing Generation
=============================================

Generates technical drawings in both Italian and English for Savignano axes.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from acs.savignano.technical_drawings import generate_technical_drawings
from acs.core.database import get_database

def test_drawing_generation():
    """Test technical drawing generation for all Savignano axes."""

    print("=" * 70)
    print("TECHNICAL DRAWING GENERATION TEST")
    print("=" * 70)

    # Get database
    db = get_database()

    # Get all artifacts with Savignano features
    print("\n📋 Finding Savignano axes in database...")

    # List of known Savignano axes
    savignano_axes = [
        'axe936', 'axe940', 'axe942', 'axe957', 'axe965',
        'axe971', 'axe974', 'axe978', 'axe979', 'axe992'
    ]

    axes_to_process = []
    for artifact_id in savignano_axes:
        try:
            artifact = db.get_artifact(artifact_id)
            if artifact:
                features = db.get_features(artifact_id)
                if features and 'savignano' in features:
                    mesh_path = artifact.get('mesh_path')
                    if mesh_path and Path(mesh_path).exists():
                        axes_to_process.append({
                            'id': artifact_id,
                            'mesh_path': mesh_path,
                            'features': features['savignano']
                        })
                        print(f"  ✓ {artifact_id}: Found with Savignano features")
                    else:
                        print(f"  ⚠️  {artifact_id}: Mesh file not found")
                else:
                    print(f"  ⚠️  {artifact_id}: No Savignano features")
            else:
                print(f"  ⚠️  {artifact_id}: Not in database")
        except Exception as e:
            print(f"  ✗ {artifact_id}: Error - {e}")

    if not axes_to_process:
        print("\n❌ No axes found with Savignano features and mesh files!")
        print("\nTip: Run analyze_savignano_direct.py first to process the axes.")
        return

    print(f"\n✓ Found {len(axes_to_process)} axes ready for drawing generation")

    # Generate drawings for first axe in both languages
    test_axe = axes_to_process[0]
    artifact_id = test_axe['id']
    mesh_path = test_axe['mesh_path']
    features = test_axe['features']

    print(f"\n" + "=" * 70)
    print(f"GENERATING DRAWINGS FOR: {artifact_id}")
    print("=" * 70)

    # Output directory
    output_base = Path.home() / '.acs' / 'drawings'

    # Test both languages
    languages = ['it', 'en']

    for lang in languages:
        print(f"\n🌍 Language: {lang.upper()}")
        print("-" * 70)

        output_dir = output_base / artifact_id / lang

        try:
            # Generate drawings
            results = generate_technical_drawings(
                mesh_path=mesh_path,
                features=features,
                output_dir=str(output_dir),
                artifact_id=artifact_id,
                language=lang,
                export_pdf=True
            )

            print(f"\n✅ Drawings generated successfully!")
            print(f"\nGenerated files:")
            for view, path in results.items():
                file_size = Path(path).stat().st_size / 1024  # KB
                print(f"  {view:12s}: {path}")
                print(f"  {'':12s}  Size: {file_size:.1f} KB")

            # Summary
            print(f"\n📁 All files in: {output_dir}")

        except Exception as e:
            print(f"\n❌ Error generating drawings: {e}")
            import traceback
            traceback.print_exc()

    # Summary for all axes
    print(f"\n" + "=" * 70)
    print("SUMMARY: Axes Ready for Drawing Generation")
    print("=" * 70)

    for axe in axes_to_process:
        artifact_id = axe['id']
        peso = axe['features'].get('peso', 0)
        incavo = "✓" if axe['features'].get('incavo_presente') else "✗"
        margini = "✓" if axe['features'].get('margini_rialzati_presenti') else "✗"
        matrix_id = axe['features'].get('matrix_id', 'Unknown')

        print(f"  {artifact_id}: Peso={peso:.0f}g, Incavo={incavo}, Margini={margini}, Matrix={matrix_id}")

    print(f"\n💡 To generate drawings for other axes, use:")
    print(f"   python3 -c \"")
    print(f"   from acs.savignano.technical_drawings import generate_technical_drawings")
    print(f"   generate_technical_drawings(")
    print(f"       mesh_path='MESH_PATH',")
    print(f"       features=FEATURES,")
    print(f"       output_dir='OUTPUT_DIR',")
    print(f"       artifact_id='ARTIFACT_ID',")
    print(f"       language='it',  # or 'en'")
    print(f"       export_pdf=True")
    print(f"   )\"")

    print(f"\n" + "=" * 70)
    print("TEST COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    test_drawing_generation()
