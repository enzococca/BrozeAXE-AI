#!/usr/bin/env python3
"""
Quick script to save Savignano features for one axe for testing.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from acs.core.database import get_database
from acs.savignano.morphometric_extractor import extract_savignano_features

# Configuration
MESH_PATH = "/Users/enzo/.acs/savignano_meshes/axe936.obj"
ARTIFACT_ID = "axe936"

def main():
    print("Quick Save Savignano Features for Testing")
    print("=" * 60)

    # Check if mesh exists
    if not Path(MESH_PATH).exists():
        print(f"❌ Mesh not found: {MESH_PATH}")
        return

    print(f"\n✓ Mesh found: {MESH_PATH}")
    print(f"  Artifact ID: {ARTIFACT_ID}")

    # Extract features
    print(f"\n🔬 Extracting Savignano features...")
    try:
        features = extract_savignano_features(
            mesh_path=MESH_PATH,
            artifact_id=ARTIFACT_ID,
            weight=0
        )
        print(f"✓ Extracted {len(features)} features")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Save to database
    print(f"\n💾 Saving to database...")
    try:
        db = get_database()

        # Save features with 'savignano' key
        db.add_features(ARTIFACT_ID, {'savignano': features})
        print(f"✓ Features saved")

        # Verify retrieval
        print(f"\n🔍 Verifying retrieval...")
        retrieved = db.get_features(ARTIFACT_ID)

        if 'savignano' in retrieved:
            print(f"✅ SUCCESS! Savignano features retrieved")
            print(f"   Features in savignano dict: {len(retrieved['savignano'])}")
            print(f"   Sample features:")
            for i, (k, v) in enumerate(list(retrieved['savignano'].items())[:5]):
                print(f"     - {k}: {v}")
        else:
            print(f"❌ FAILED! No 'savignano' key in retrieved features")
            print(f"   Retrieved keys: {list(retrieved.keys())}")

    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"\n" + "=" * 60)
    print("✅ TEST COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
