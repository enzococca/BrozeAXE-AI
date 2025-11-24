#!/usr/bin/env python3
"""
Script per analizzare direttamente le mesh Savignano dal disco esterno
senza passare per upload HTTP (bypass limite 413).
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from acs.savignano.morphometric_extractor import batch_extract_savignano_features
from acs.core.database import get_database

# Configurazione
EXTERNAL_DRIVE = "/Volumes/extesione4T/3dasce"
PERMANENT_MESH_DIR = Path.home() / ".acs" / "savignano_meshes"

# Pesi manuali (opzionale - modifica se conosci i pesi)
WEIGHTS = {
    'axe936': 0,  # Inserisci peso in grammi se noto, altrimenti 0
    'axe940': 0,
    'axe942': 0,
    'axe957': 0,
    'axe965': 0,
    'axe971': 0,
    'axe974': 0,
    'axe978': 0,
    'axe979': 0,
    'axe992': 0,
}

def main():
    print("=" * 70)
    print("ANALISI SAVIGNANO DIRETTA (Bypass HTTP Upload)")
    print("=" * 70)

    # Verifica directory
    source_dir = Path(EXTERNAL_DRIVE)
    if not source_dir.exists():
        print(f"✗ Directory non trovata: {EXTERNAL_DRIVE}")
        print("  Verifica che il disco esterno sia connesso!")
        return

    # Crea temp directory per analisi
    with tempfile.TemporaryDirectory(prefix='savignano_direct_') as temp_dir:
        temp_path = Path(temp_dir)
        meshes_dir = temp_path / 'meshes'
        meshes_dir.mkdir()

        print(f"\n📁 Directory temporanea: {temp_dir}")

        # Copia mesh in temp dir
        axes = list(WEIGHTS.keys())
        print(f"\n📄 Copiando {len(axes)} mesh...")

        for axe_name in axes:
            source_obj = source_dir / axe_name / f"{axe_name}.obj"

            if not source_obj.exists():
                print(f"  ⚠️  {axe_name}: File non trovato")
                continue

            dest_obj = meshes_dir / f"{axe_name}.obj"
            print(f"  → {axe_name}.obj ({source_obj.stat().st_size / 1024 / 1024:.1f} MB)")

            shutil.copy2(source_obj, dest_obj)

        # Prepara file pesi (opzionale)
        weights_json = None
        if any(w > 0 for w in WEIGHTS.values()):
            import json
            weights_file = temp_path / 'weights.json'
            with open(weights_file, 'w') as f:
                json.dump(WEIGHTS, f)
            weights_json = str(weights_file)
            print(f"\n⚖️  File pesi: {sum(1 for w in WEIGHTS.values() if w > 0)} asce con peso")

        # Esegui estrazione features
        print(f"\n🔬 Estrazione features Savignano...")
        print("-" * 70)

        # Converti weights in dict per la funzione
        weights_dict = {k: v for k, v in WEIGHTS.items() if v > 0} if any(w > 0 for w in WEIGHTS.values()) else None

        results_list = batch_extract_savignano_features(
            mesh_directory=str(meshes_dir),
            weights_dict=weights_dict
        )

        print("-" * 70)
        print(f"\n✅ Estrazione completata!")
        print(f"   Processate: {len(results_list)} asce")

        # Salva nel database principale
        print(f"\n💾 Salvataggio nel database...")

        db = get_database()

        PERMANENT_MESH_DIR.mkdir(parents=True, exist_ok=True)

        saved = 0
        import sqlite3

        for features in results_list:
            artifact_id = features['artifact_id']

            # Copia mesh in directory permanente
            source_mesh = meshes_dir / f"{artifact_id}.obj"
            dest_mesh = PERMANENT_MESH_DIR / f"{artifact_id}.obj"

            if source_mesh.exists():
                shutil.copy2(source_mesh, dest_mesh)

            # Salva features
            db.add_features(artifact_id, {'savignano': features})

            # Aggiorna mesh_path nel database
            db_path = Path(__file__).parent / "acs_artifacts.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE artifacts SET mesh_path = ? WHERE artifact_id = ?",
                (str(dest_mesh), artifact_id)
            )
            conn.commit()
            conn.close()

            saved += 1
            print(f"  ✓ {artifact_id}: features salvate")

        print(f"\n✅ Salvati {saved} artifacts nel database")

        # Mostra summary
        print("\n" + "=" * 70)
        print("RIEPILOGO FEATURES ESTRATTE")
        print("=" * 70)

        for features in results_list:
            aid = features['artifact_id']
            peso = features.get('peso', 0)
            incavo = "SÌ" if features.get('incavo_presente', False) else "NO"
            tagliente = features.get('tagliente_forma', 'unknown')

            print(f"  {aid}: Peso={peso}g, Incavo={incavo}, Tagliente={tagliente}")

    print("\n" + "=" * 70)
    print("✅ ANALISI COMPLETATA!")
    print("=" * 70)
    print("\nOra puoi:")
    print("1. Riavviare il server Flask")
    print("2. Vai su /web/savignano-compare per comparare le asce")
    print("3. Tutte le features Savignano sono ora disponibili!")

if __name__ == "__main__":
    main()
