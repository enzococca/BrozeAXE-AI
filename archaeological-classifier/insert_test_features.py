#!/usr/bin/env python3
"""
Insert realistic test Savignano features for web GUI testing.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from acs.core.database import get_database

# Realistic Savignano features based on actual measurements
TEST_FEATURES = {
    'axe974': {
        'artifact_id': 'axe974',
        'peso': 0.0,
        'incavo_presente': True,
        'incavo_larghezza': 54.77,
        'incavo_profondita': 5.12,
        'incavo_profilo': 'rettangolare',
        'tallone_larghezza': 82.44,
        'tallone_spessore': 34.65,
        'margini_rialzati_presenti': True,
        'margini_rialzati_lunghezza': 7.21,
        'margini_rialzati_spessore_max': 0.91,
        'corpo_lunghezza_minima': 117.28,
        'corpo_spessore_max_con_margini': 56.28,
        'corpo_spessore_max_senza_margini': 42.67,
        'tagliente_larghezza': 85.78,
        'tagliente_forma': 'lunato',
        'tagliente_arco': 6.48,
        'tagliente_corda': 3.27,
        'tagliente_espanso': False,
        'lunghezza_totale': 163.28,
        'matrix_id': 'MAT_A',
        'inventory_number': 'axe974'
    },
    'axe936': {
        'artifact_id': 'axe936',
        'peso': 0.0,
        'incavo_presente': True,
        'incavo_larghezza': 82.71,
        'incavo_profondita': 5.35,
        'incavo_profilo': 'rettangolare',
        'tallone_larghezza': 102.44,
        'tallone_spessore': 33.02,
        'margini_rialzati_presenti': False,
        'margini_rialzati_lunghezza': 0.0,
        'margini_rialzati_spessore_max': 0.0,
        'corpo_lunghezza_minima': 129.35,
        'corpo_spessore_max_con_margini': 60.16,
        'corpo_spessore_max_senza_margini': 44.89,
        'tagliente_larghezza': 107.85,
        'tagliente_forma': 'lunato',
        'tagliente_arco': 535.30,
        'tagliente_corda': 40.22,
        'tagliente_espanso': False,
        'lunghezza_totale': 181.92,
        'matrix_id': 'MAT_B',
        'inventory_number': 'axe936'
    }
}

def main():
    print("=" * 70)
    print("INSERT TEST SAVIGNANO FEATURES")
    print("=" * 70)

    db = get_database()

    for artifact_id, features in TEST_FEATURES.items():
        print(f"\n📝 Inserting features for {artifact_id}...")

        try:
            # Save features with 'savignano' key
            db.add_features(artifact_id, {'savignano': features})
            print(f"  ✓ Features saved")

            # Verify
            retrieved = db.get_features(artifact_id)
            if 'savignano' in retrieved:
                print(f"  ✅ Verified - {len(retrieved['savignano'])} parameters")
                print(f"     Incavo: {'SÌ' if features['incavo_presente'] else 'NO'}")
                print(f"     Tagliente: {features['tagliente_forma']}")
                print(f"     Matrix: {features['matrix_id']}")
            else:
                print(f"  ❌ Verification failed!")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n" + "=" * 70)
    print("✅ TEST FEATURES INSERTED!")
    print("=" * 70)
    print("\nReady to test from web GUI:")
    print("1. Start server: python app.py")
    print("2. Navigate to Savignano drawing generation")
    print("3. Select axe974 or axe936")
    print("4. Choose language (IT/EN)")
    print("5. Generate PDF!")

if __name__ == "__main__":
    main()
