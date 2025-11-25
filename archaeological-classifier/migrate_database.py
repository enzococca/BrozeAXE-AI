#!/usr/bin/env python3
"""
Database Migration Script
==========================

Adds owner_id column to projects table and creates project_collaborators table.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'acs_artifacts.db')

def migrate():
    """Run database migration."""
    print("Starting database migration...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if owner_id column exists
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'owner_id' not in columns:
            print("Adding owner_id column to projects table...")
            cursor.execute('ALTER TABLE projects ADD COLUMN owner_id INTEGER')

            # Set owner_id to 1 (admin) for existing projects
            cursor.execute('UPDATE projects SET owner_id = 1 WHERE owner_id IS NULL')
            print("✅ owner_id column added")
        else:
            print("✅ owner_id column already exists")

        # Check if project_collaborators table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_collaborators'")
        if not cursor.fetchone():
            print("Creating project_collaborators table...")
            cursor.execute('''
                CREATE TABLE project_collaborators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    user_id INTEGER,
                    role TEXT DEFAULT 'collaborator',
                    invited_date TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(project_id, user_id)
                )
            ''')
            print("✅ project_collaborators table created")
        else:
            print("✅ project_collaborators table already exists")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
