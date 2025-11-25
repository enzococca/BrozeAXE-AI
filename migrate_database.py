#!/usr/bin/env python3
"""
Database Migration Script
=========================

Adds owner_id column to projects table and creates project_collaborators table.
Run this script ONCE to migrate your existing database.

Usage:
    python migrate_database.py
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime


def migrate_database(db_path=None):
    """Add owner_id and collaborators table to existing database."""

    # Get database path from environment or use default
    if db_path is None:
        db_path = os.getenv('DATABASE_PATH', '/data/acs_artifacts.db')

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("   No migration needed - database will be created with correct schema on first use.")
        return

    print(f"🔧 Migrating database: {db_path}")

    # Backup database before migration
    backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
        response = input("Continue without backup? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Migration cancelled")
            return

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if owner_id column exists
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'owner_id' not in columns:
            print("📝 Adding owner_id column to projects table...")

            # Add owner_id column
            cursor.execute('ALTER TABLE projects ADD COLUMN owner_id INTEGER')

            # Set default owner to user_id 1 (admin) for existing projects
            cursor.execute('UPDATE projects SET owner_id = 1 WHERE owner_id IS NULL')

            print("✅ owner_id column added successfully")
        else:
            print("✓ owner_id column already exists")

        # Check if project_collaborators table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='project_collaborators'
        """)

        if not cursor.fetchone():
            print("📝 Creating project_collaborators table...")

            # Create project_collaborators table
            cursor.execute('''
                CREATE TABLE project_collaborators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'collaborator',
                    invited_date TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    UNIQUE(project_id, user_id)
                )
            ''')

            print("✅ project_collaborators table created successfully")
        else:
            print("✓ project_collaborators table already exists")

        # Commit changes
        conn.commit()

        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM projects WHERE owner_id IS NOT NULL")
        projects_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM project_collaborators")
        collaborators_count = cursor.fetchone()[0]

        print("\n✅ Migration completed successfully!")
        print(f"   Projects with owners: {projects_count}")
        print(f"   Collaborators: {collaborators_count}")
        print(f"   Backup: {backup_path}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"   Database restored from backup: {backup_path}")
        raise

    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("BrozeAXE-AI Database Migration")
    print("=" * 60)
    print()

    migrate_database()

    print()
    print("=" * 60)
    print("Migration process completed!")
    print("=" * 60)
