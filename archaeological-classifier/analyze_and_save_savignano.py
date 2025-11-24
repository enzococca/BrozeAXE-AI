#!/usr/bin/env python3
"""
Optimized script to analyze and save Savignano features with progress tracking.
Saves features incrementally to avoid data loss.
"""

import os
import sys
import shutil
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from acs.savignano.morphometric_extractor import extract_savignano_features
from acs.core.database import get_database
import sqlite3

# Configuration
EXTERNAL_DRIVE = "/Volumes/extesione4T/3dasce"
PERMANENT_MESH_DIR = Path.home() / ".acs" / "savignano_meshes"

# List of axes to process
SAVIGNANO_AXES = [
    'axe936', 'axe940', 'axe942', 'axe957', 'axe965',
    'axe971', 'axe974', 'axe978', 'axe979', 'axe992'
]

def process_single_axe(artifact_id: str, mesh_path: Path, db):
    """Process a single axe and save to database."""
    print(f"\n{'='*70}")
    print(f"Processing: {artifact_id}")
    print(f"{'='*70}")

    try:
        # Extract features
        print(f"  🔬 Extracting features...")
        features = extract_savignano_features(
            mesh_path=str(mesh_path),
            artifact_id=artifact_id,
            weight=0
        )

        print(f"  ✓ Extracted {len(features)} parameters")

        # Save to database
        print(f"  💾 Saving to database...")
        db.add_features(artifact_id, {'savignano': features})

        # Update mesh_path
        db_path = Path(__file__).parent / "acs_artifacts.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE artifacts SET mesh_path = ? WHERE artifact_id = ?",
            (str(mesh_path), artifact_id)
        )
        conn.commit()
        conn.close()

        print(f"  ✅ {artifact_id} COMPLETE!")
        print(f"     Incavo: {'SÌ' if features.get('incavo_presente') else 'NO'}")
        print(f"     Tagliente: {features.get('tagliente_forma', 'unknown')}")
        print(f"     Tallone Width: {features.get('tallone_larghezza', 0):.1f}mm")

        return True, features

    except Exception as e:
        print(f"  ❌ Error processing {artifact_id}: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    print("=" * 70)
    print("SAVIGNANO ANALYSIS - GPU ACCELERATED (Apple Accelerate)")
    print("=" * 70)
    print(f"\nProcessing {len(SAVIGNANO_AXES)} axes...")
    print("Using Apple Silicon hardware acceleration (12 cores + GPU)")

    # Ensure permanent mesh directory exists
    PERMANENT_MESH_DIR.mkdir(parents=True, exist_ok=True)

    # Get database
    db = get_database()

    # Process each axe
    processed = []
    failed = []

    for i, artifact_id in enumerate(SAVIGNANO_AXES, 1):
        print(f"\n\n📊 PROGRESS: {i}/{len(SAVIGNANO_AXES)}")

        # Check if already processed
        existing_features = db.get_features(artifact_id)
        if existing_features and 'savignano' in existing_features:
            print(f"  ⚠️  {artifact_id}: Already has Savignano features - SKIPPING")
            processed.append(artifact_id)
            continue

        # Get mesh path
        mesh_path = PERMANENT_MESH_DIR / f"{artifact_id}.obj"

        if not mesh_path.exists():
            # Try to copy from external drive
            source_path = Path(EXTERNAL_DRIVE) / artifact_id / f"{artifact_id}.obj"
            if source_path.exists():
                print(f"  📄 Copying from external drive...")
                print(f"     Size: {source_path.stat().st_size / 1024 / 1024:.1f} MB")
                shutil.copy2(source_path, mesh_path)
            else:
                print(f"  ❌ Mesh not found: {artifact_id}")
                failed.append(artifact_id)
                continue

        # Process the axe
        success, features = process_single_axe(artifact_id, mesh_path, db)

        if success:
            processed.append(artifact_id)
        else:
            failed.append(artifact_id)

    # Final summary
    print(f"\n\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"\n✅ Successfully processed: {len(processed)}/{len(SAVIGNANO_AXES)}")
    for aid in processed:
        print(f"   ✓ {aid}")

    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for aid in failed:
            print(f"   ✗ {aid}")

    print(f"\n{'='*70}")
    print("✅ ANALYSIS COMPLETE!")
    print(f"{'='*70}")
    print("\nNext steps:")
    print("1. Run: python3 test_drawing_generation.py")
    print("2. Technical drawings will be generated in IT and EN")

if __name__ == "__main__":
    main()
