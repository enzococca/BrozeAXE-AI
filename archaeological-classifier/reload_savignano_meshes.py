#!/usr/bin/env python3
"""
Script per ricaricare le mesh Savignano nella directory permanente
e aggiornare i path nel database.
"""

import os
import shutil
import sqlite3
from pathlib import Path

# Configurazione
EXTERNAL_DRIVE = "/Volumes/extesione4T/3dasce"
PERMANENT_MESH_DIR = Path.home() / ".acs" / "savignano_meshes"
DATABASE_PATH = Path(__file__).parent / "acs_artifacts.db"

def main():
    print("=" * 60)
    print("Ricaricamento Mesh Savignano")
    print("=" * 60)

    # Crea directory permanente
    PERMANENT_MESH_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Directory permanente: {PERMANENT_MESH_DIR}")

    # Trova tutti i file .obj
    source_dir = Path(EXTERNAL_DRIVE)
    if not source_dir.exists():
        print(f"✗ Directory non trovata: {EXTERNAL_DRIVE}")
        print("  Verifica che il disco esterno sia connesso!")
        return

    # Lista asce da processare
    axes = [
        'axe936', 'axe940', 'axe942', 'axe957', 'axe965',
        'axe971', 'axe974', 'axe978', 'axe979', 'axe992'
    ]

    copied = []
    for axe_name in axes:
        # Path sorgente: /Volumes/extesione4T/3dasce/axe936/axe936.obj
        source_obj = source_dir / axe_name / f"{axe_name}.obj"

        if not source_obj.exists():
            print(f"⚠️  {axe_name}: File non trovato in {source_obj}")
            continue

        # Path destinazione: ~/.acs/savignano_meshes/axe936.obj
        dest_obj = PERMANENT_MESH_DIR / f"{axe_name}.obj"

        # Copia file
        print(f"📄 Copiando {axe_name}.obj...")
        shutil.copy2(source_obj, dest_obj)

        copied.append((axe_name, str(dest_obj)))

    print(f"\n✓ Copiati {len(copied)} file mesh")

    # Aggiorna database
    if not DATABASE_PATH.exists():
        print(f"✗ Database non trovato: {DATABASE_PATH}")
        return

    print(f"\n📊 Aggiornamento database: {DATABASE_PATH}")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    updated = 0
    for axe_name, new_path in copied:
        cursor.execute(
            "UPDATE artifacts SET mesh_path = ? WHERE artifact_id = ?",
            (new_path, axe_name)
        )
        if cursor.rowcount > 0:
            updated += 1
            print(f"  ✓ {axe_name}: path aggiornato")

    conn.commit()
    conn.close()

    print(f"\n✓ Database aggiornato: {updated} artifacts")

    print("\n" + "=" * 60)
    print("✅ COMPLETATO!")
    print("=" * 60)
    print("\nOra puoi:")
    print("1. Riavviare il server Flask")
    print("2. Le mesh appariranno nel 3D viewer")
    print("3. Vai su /web/savignano-compare per comparare le asce")
    print("\nNOTA: Per estrarre le features Savignano complete,")
    print("      usa /web/savignano-analysis con questi file.")

if __name__ == "__main__":
    main()
