#!/usr/bin/env python3
"""
Reset Database Script
======================

Questo script resetta il database mantenendo solo l'utente admin.

ATTENZIONE: Questo script cancella TUTTI i dati tranne l'utente admin!

Usage:
    python reset_database.py [--force]

Options:
    --force     Skip confirmation prompt
"""

import os
import sys
import sqlite3
from datetime import datetime
import bcrypt

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'acs_artifacts.db')

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@brozeaxe.com"
ADMIN_PASSWORD = "admin123"  # Change this in production!
ADMIN_ROLE = "admin"
ADMIN_FULL_NAME = "System Administrator"


def reset_database(force=False):
    """Reset database keeping only admin user."""

    print("=" * 60)
    print("DATABASE RESET TOOL")
    print("=" * 60)
    print(f"\nDatabase: {DB_PATH}")
    print("\n⚠️  WARNING: This will DELETE ALL DATA except admin user!")
    print("\nThis will:")
    print("  • Delete all artifacts and uploads")
    print("  • Delete all projects")
    print("  • Delete all classifications and training data")
    print("  • Delete all users except admin")
    print("  • Reset admin password to default")

    # Confirm
    if not force:
        response = input("\nAre you sure you want to continue? (type 'YES' to confirm): ")
        if response != "YES":
            print("\n❌ Operation cancelled.")
            return
    else:
        print("\n⚠️  Running in --force mode, skipping confirmation...")

    print("\n🔄 Starting database reset...")

    # Backup old database
    if os.path.exists(DB_PATH):
        backup_path = f"{DB_PATH}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Backup created: {backup_path}")

    # Delete database file
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"✅ Old database deleted")

    # Recreate database with schema
    print("✅ Creating new database schema...")
    from acs.core.database import ArtifactDatabase
    db = ArtifactDatabase(DB_PATH)

    # Add admin user
    print("✅ Creating admin user...")
    password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        db.add_user(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=password_hash,
            role=ADMIN_ROLE,
            full_name=ADMIN_FULL_NAME
        )
        print(f"✅ Admin user created successfully")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return

    # Get admin user to verify
    admin = db.get_user_by_username(ADMIN_USERNAME)
    if admin:
        print(f"\n✅ Database reset complete!")
        print(f"\n{'=' * 60}")
        print("ADMIN USER CREDENTIALS")
        print(f"{'=' * 60}")
        print(f"Username: {ADMIN_USERNAME}")
        print(f"Email:    {ADMIN_EMAIL}")
        print(f"Password: {ADMIN_PASSWORD}")
        print(f"Role:     {ADMIN_ROLE}")
        print(f"{'=' * 60}")
        print("\n⚠️  IMPORTANT: Change the admin password after first login!")
        print()
    else:
        print("❌ Error: Could not verify admin user creation")


if __name__ == '__main__':
    force = '--force' in sys.argv
    reset_database(force=force)
