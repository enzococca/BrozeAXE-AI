"""
SQLite Database Module
======================

Persistent storage for artifacts, classifications, and ML training data.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


class ArtifactDatabase:
    """
    SQLite database for archaeological artifact data persistence.
    """

    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        if db_path is None:
            # Check DATABASE_PATH first (Railway standard), then ACS_DB_PATH for backwards compatibility
            db_path = os.getenv('DATABASE_PATH') or os.getenv('ACS_DB_PATH', '/data/acs_artifacts.db')

        self.db_path = db_path

        # Ensure parent directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        """Create database schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Projects table (for multi-project management)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    project_name TEXT,
                    description TEXT,
                    owner_id INTEGER,
                    created_date TEXT,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (owner_id) REFERENCES users(user_id)
                )
            ''')

            # Project collaborators table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_collaborators (
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

            # Artifacts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    project_id TEXT DEFAULT 'default',
                    mesh_path TEXT,
                    upload_date TEXT,
                    n_vertices INTEGER,
                    n_faces INTEGER,
                    is_watertight INTEGER,
                    metadata TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                )
            ''')

            # Features table (morphometric)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_id TEXT,
                    feature_name TEXT,
                    feature_value REAL,
                    extraction_date TEXT,
                    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
                )
            ''')

            # Stylistic features table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stylistic_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_id TEXT,
                    feature_category TEXT,
                    features_json TEXT,
                    extraction_date TEXT,
                    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
                )
            ''')

            # Classifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_id TEXT,
                    class_id TEXT,
                    class_name TEXT,
                    confidence REAL,
                    classification_date TEXT,
                    validated INTEGER DEFAULT 0,
                    validator_notes TEXT,
                    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
                )
            ''')

            # Training data table (for ML)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_id TEXT,
                    class_label TEXT,
                    features_json TEXT,
                    validation_score REAL,
                    added_date TEXT,
                    is_validated INTEGER DEFAULT 1,
                    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
                )
            ''')

            # Analysis results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT,
                    artifact_ids TEXT,
                    results_json TEXT,
                    analysis_date TEXT
                )
            ''')

            # Comparisons table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact1_id TEXT,
                    artifact2_id TEXT,
                    similarity_score REAL,
                    comparison_data TEXT,
                    comparison_date TEXT,
                    FOREIGN KEY (artifact1_id) REFERENCES artifacts(artifact_id),
                    FOREIGN KEY (artifact2_id) REFERENCES artifacts(artifact_id)
                )
            ''')

            # Users table (for authentication)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'viewer',
                    full_name TEXT,
                    created_date TEXT,
                    last_login TEXT,
                    is_active INTEGER DEFAULT 1
                )
            ''')

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_artifact_id ON features(artifact_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_class_id ON classifications(class_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_validated ON classifications(validated)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_training_class ON training_data(class_label)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON users(email)')

            conn.commit()

    # ========== ARTIFACT OPERATIONS ==========

    def add_artifact(self, artifact_id: str, mesh_path: str, n_vertices: int,
                     n_faces: int, is_watertight: bool, metadata: Dict = None,
                     project_id: str = 'default'):
        """Add a new artifact to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO artifacts
                (artifact_id, project_id, mesh_path, upload_date, n_vertices, n_faces, is_watertight, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                artifact_id,
                project_id,
                mesh_path,
                datetime.now().isoformat(),
                n_vertices,
                n_faces,
                1 if is_watertight else 0,
                json.dumps(metadata) if metadata else None
            ))

    def get_artifact(self, artifact_id: str) -> Optional[Dict]:
        """Retrieve artifact data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM artifacts WHERE artifact_id = ?', (artifact_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_all_artifacts(self) -> List[Dict]:
        """Get all artifacts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM artifacts ORDER BY upload_date DESC')
            return [dict(row) for row in cursor.fetchall()]

    def get_artifacts_paginated(self, page: int = 1, per_page: int = 20) -> Dict:
        """
        Get paginated artifacts.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page

        Returns:
            Dictionary with:
            - artifacts: List of artifacts for current page
            - total: Total number of artifacts
            - page: Current page
            - per_page: Items per page
            - pages: Total number of pages
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get total count
            cursor.execute('SELECT COUNT(*) as count FROM artifacts')
            total = cursor.fetchone()['count']

            # Calculate pagination
            pages = (total + per_page - 1) // per_page  # Ceiling division
            offset = (page - 1) * per_page

            # Get paginated results
            cursor.execute('''
                SELECT * FROM artifacts
                ORDER BY upload_date DESC
                LIMIT ? OFFSET ?
            ''', (per_page, offset))

            artifacts = [dict(row) for row in cursor.fetchall()]

            return {
                'artifacts': artifacts,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': pages
            }

    def delete_artifact(self, artifact_id: str) -> bool:
        """
        Delete an artifact and all associated data (CASCADE).

        This will delete:
        - Artifact record
        - All features
        - All classifications
        - All training samples
        - All comparisons
        - All stylistic features

        Args:
            artifact_id: ID of the artifact to delete

        Returns:
            True if artifact was deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if artifact exists
            cursor.execute('SELECT artifact_id FROM artifacts WHERE artifact_id = ?', (artifact_id,))
            if not cursor.fetchone():
                return False

            # Delete from all related tables (CASCADE should handle this automatically,
            # but we do it explicitly for clarity and to handle any non-CASCADE constraints)

            # Delete features
            cursor.execute('DELETE FROM features WHERE artifact_id = ?', (artifact_id,))

            # Delete stylistic features
            cursor.execute('DELETE FROM stylistic_features WHERE artifact_id = ?', (artifact_id,))

            # Delete classifications
            cursor.execute('DELETE FROM classifications WHERE artifact_id = ?', (artifact_id,))

            # Delete training samples
            cursor.execute('DELETE FROM training_data WHERE artifact_id = ?', (artifact_id,))

            # Delete comparisons where this artifact is involved
            cursor.execute('''
                DELETE FROM comparisons
                WHERE artifact1_id = ? OR artifact2_id = ?
            ''', (artifact_id, artifact_id))

            # Delete the artifact itself
            cursor.execute('DELETE FROM artifacts WHERE artifact_id = ?', (artifact_id,))

            conn.commit()
            return True

    # ========== FEATURE OPERATIONS ==========

    def add_features(self, artifact_id: str, features: Dict[str, float]):
        """Store features for an artifact."""
        import json
        import numpy as np

        def convert_numpy_types(obj):
            """Convert numpy types to Python native types for JSON serialization."""
            if isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj

        with self.get_connection() as conn:
            cursor = conn.cursor()
            extraction_date = datetime.now().isoformat()

            # Delete existing features for this artifact
            cursor.execute('DELETE FROM features WHERE artifact_id = ?', (artifact_id,))

            # Insert new features
            for feature_name, feature_value in features.items():
                # Handle nested dictionaries (e.g., 'savignano' features)
                if isinstance(feature_value, dict):
                    # Convert numpy types before JSON serialization
                    feature_value = convert_numpy_types(feature_value)
                    # Store in stylistic_features table
                    cursor.execute('DELETE FROM stylistic_features WHERE artifact_id = ? AND feature_category = ?',
                                 (artifact_id, feature_name))
                    cursor.execute('''
                        INSERT INTO stylistic_features (artifact_id, feature_category, features_json, extraction_date)
                        VALUES (?, ?, ?, ?)
                    ''', (artifact_id, feature_name, json.dumps(feature_value), extraction_date))
                elif isinstance(feature_value, (int, float)):
                    cursor.execute('''
                        INSERT INTO features (artifact_id, feature_name, feature_value, extraction_date)
                        VALUES (?, ?, ?, ?)
                    ''', (artifact_id, feature_name, float(feature_value), extraction_date))

    def get_features(self, artifact_id: str) -> Dict[str, float]:
        """Retrieve features for an artifact."""
        import json
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get numeric features
            cursor.execute('''
                SELECT feature_name, feature_value
                FROM features
                WHERE artifact_id = ?
            ''', (artifact_id,))
            result = {row['feature_name']: row['feature_value'] for row in cursor.fetchall()}

            # Get stylistic features (e.g., savignano)
            cursor.execute('''
                SELECT feature_category, features_json
                FROM stylistic_features
                WHERE artifact_id = ?
            ''', (artifact_id,))

            for row in cursor.fetchall():
                result[row['feature_category']] = json.loads(row['features_json'])

            return result

    def get_all_features(self) -> Dict[str, Dict[str, float]]:
        """Get features for all artifacts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT artifact_id, feature_name, feature_value FROM features')

            result = {}
            for row in cursor.fetchall():
                artifact_id = row['artifact_id']
                if artifact_id not in result:
                    result[artifact_id] = {}
                result[artifact_id][row['feature_name']] = row['feature_value']

            return result

    # ========== CLASSIFICATION OPERATIONS ==========

    def add_classification(self, artifact_id: str, class_id: str, class_name: str,
                          confidence: float, validated: bool = False, notes: str = None):
        """Store a classification result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO classifications
                (artifact_id, class_id, class_name, confidence, classification_date, validated, validator_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                artifact_id,
                class_id,
                class_name,
                confidence,
                datetime.now().isoformat(),
                1 if validated else 0,
                notes
            ))

    def get_classifications(self, artifact_id: str) -> List[Dict]:
        """Get all classifications for an artifact."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM classifications
                WHERE artifact_id = ?
                ORDER BY classification_date DESC
            ''', (artifact_id,))

            return [dict(row) for row in cursor.fetchall()]

    def validate_classification(self, classification_id: int, notes: str = None):
        """Mark a classification as validated."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE classifications
                SET validated = 1, validator_notes = ?
                WHERE id = ?
            ''', (notes, classification_id))

    def get_validated_classifications(self) -> List[Dict]:
        """Get all validated classifications for ML training."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM classifications
                WHERE validated = 1
                ORDER BY classification_date DESC
            ''')

            return [dict(row) for row in cursor.fetchall()]

    # ========== TRAINING DATA OPERATIONS ==========

    def add_training_sample(self, artifact_id: str, class_label: str,
                           features: Dict, validation_score: float = 1.0):
        """Add a validated sample to training data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO training_data
                (artifact_id, class_label, features_json, validation_score, added_date, is_validated)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (
                artifact_id,
                class_label,
                json.dumps(features),
                validation_score,
                datetime.now().isoformat()
            ))

    def get_training_data(self, class_label: str = None) -> List[Dict]:
        """Retrieve training data, optionally filtered by class."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if class_label:
                cursor.execute('''
                    SELECT * FROM training_data
                    WHERE class_label = ? AND is_validated = 1
                    ORDER BY added_date DESC
                ''', (class_label,))
            else:
                cursor.execute('''
                    SELECT * FROM training_data
                    WHERE is_validated = 1
                    ORDER BY added_date DESC
                ''')

            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data['features'] = json.loads(data['features_json'])
                del data['features_json']
                results.append(data)

            return results

    def get_training_statistics(self) -> Dict:
        """Get statistics about training data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Count by class
            cursor.execute('''
                SELECT class_label, COUNT(*) as count
                FROM training_data
                WHERE is_validated = 1
                GROUP BY class_label
            ''')

            class_counts = {row['class_label']: row['count'] for row in cursor.fetchall()}

            # Total count
            cursor.execute('SELECT COUNT(*) as total FROM training_data WHERE is_validated = 1')
            total = cursor.fetchone()['total']

            return {
                'total_samples': total,
                'class_distribution': class_counts,
                'n_classes': len(class_counts)
            }

    # ========== ANALYSIS OPERATIONS ==========

    def save_analysis_result(self, analysis_type: str, artifact_ids: List[str], results: Dict):
        """Save analysis results (PCA, clustering, etc.)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analysis_results
                (analysis_type, artifact_ids, results_json, analysis_date)
                VALUES (?, ?, ?, ?)
            ''', (
                analysis_type,
                json.dumps(artifact_ids),
                json.dumps(results),
                datetime.now().isoformat()
            ))

    def get_analysis_results(self, analysis_type: str = None, limit: int = 10) -> List[Dict]:
        """Retrieve analysis results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if analysis_type:
                cursor.execute('''
                    SELECT * FROM analysis_results
                    WHERE analysis_type = ?
                    ORDER BY analysis_date DESC
                    LIMIT ?
                ''', (analysis_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM analysis_results
                    ORDER BY analysis_date DESC
                    LIMIT ?
                ''', (limit,))

            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data['artifact_ids'] = json.loads(data['artifact_ids'])
                data['results'] = json.loads(data['results_json'])
                del data['results_json']
                results.append(data)

            return results

    # ========== COMPARISON OPERATIONS ==========

    def save_comparison(self, artifact1_id: str, artifact2_id: str,
                       similarity_score: float, comparison_data: Dict):
        """Save a comparison result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO comparisons
                (artifact1_id, artifact2_id, similarity_score, comparison_data, comparison_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                artifact1_id,
                artifact2_id,
                similarity_score,
                json.dumps(comparison_data),
                datetime.now().isoformat()
            ))

    def get_comparison(self, artifact1_id: str, artifact2_id: str) -> Optional[Dict]:
        """Retrieve cached comparison result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM comparisons
                WHERE (artifact1_id = ? AND artifact2_id = ?)
                   OR (artifact1_id = ? AND artifact2_id = ?)
                ORDER BY comparison_date DESC
                LIMIT 1
            ''', (artifact1_id, artifact2_id, artifact2_id, artifact1_id))

            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['comparison_data'] = json.loads(data['comparison_data'])
                return data
            return None

    # ========== PROJECT MANAGEMENT OPERATIONS ==========

    def create_project(self, project_id: str, name: str, owner_id: int, description: str = None):
        """Create a new project owned by a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects (project_id, project_name, description, owner_id, created_date, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            ''', (project_id, name, description, owner_id, datetime.now().isoformat()))

    def update_project_owner(self, project_id: str, new_owner_id: int):
        """Update the owner of a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects SET owner_id = ? WHERE project_id = ?
            ''', (new_owner_id, project_id))

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project information."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def list_projects(self, status: str = None) -> List[Dict]:
        """List all projects, optionally filtered by status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute('''
                    SELECT * FROM projects WHERE status = ? ORDER BY created_date DESC
                ''', (status,))
            else:
                cursor.execute('SELECT * FROM projects ORDER BY created_date DESC')

            return [dict(row) for row in cursor.fetchall()]

    def update_project_status(self, project_id: str, status: str):
        """Update project status (active, archived, etc.)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects SET status = ? WHERE project_id = ?
            ''', (status, project_id))

    def get_project_artifacts(self, project_id: str) -> List[Dict]:
        """Get all artifacts for a specific project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM artifacts WHERE project_id = ? ORDER BY upload_date DESC
            ''', (project_id,))

            return [dict(row) for row in cursor.fetchall()]

    def assign_artifact_to_project(self, artifact_id: str, project_id: str):
        """Assign an artifact to a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE artifacts SET project_id = ? WHERE artifact_id = ?
            ''', (project_id, artifact_id))

    def merge_projects(self, source_project_ids: List[str], target_project_id: str,
                      target_name: str, target_description: str = None):
        """Merge multiple projects into a new or existing project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create target project if it doesn't exist
            cursor.execute('SELECT project_id FROM projects WHERE project_id = ?', (target_project_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO projects (project_id, project_name, description, created_date, status)
                    VALUES (?, ?, ?, ?, 'active')
                ''', (target_project_id, target_name, target_description, datetime.now().isoformat()))

            # Move all artifacts from source projects to target
            for source_id in source_project_ids:
                cursor.execute('''
                    UPDATE artifacts SET project_id = ? WHERE project_id = ?
                ''', (target_project_id, source_id))

            # Archive source projects
            for source_id in source_project_ids:
                cursor.execute('''
                    UPDATE projects SET status = 'merged' WHERE project_id = ?
                ''', (source_id,))

            conn.commit()

    def get_project_statistics(self, project_id: str) -> Dict:
        """Get statistics for a specific project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {'project_id': project_id}

            # Artifact count
            cursor.execute('''
                SELECT COUNT(*) as count FROM artifacts WHERE project_id = ?
            ''', (project_id,))
            stats['total_artifacts'] = cursor.fetchone()['count']

            # Classifications count
            cursor.execute('''
                SELECT COUNT(*) as count FROM classifications c
                JOIN artifacts a ON c.artifact_id = a.artifact_id
                WHERE a.project_id = ?
            ''', (project_id,))
            stats['total_classifications'] = cursor.fetchone()['count']

            # Validated classifications
            cursor.execute('''
                SELECT COUNT(*) as count FROM classifications c
                JOIN artifacts a ON c.artifact_id = a.artifact_id
                WHERE a.project_id = ? AND c.validated = 1
            ''', (project_id,))
            stats['validated_classifications'] = cursor.fetchone()['count']

            return stats

    # ========== UTILITY OPERATIONS ==========

    def get_statistics(self) -> Dict:
        """Get overall database statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Artifact count
            cursor.execute('SELECT COUNT(*) as count FROM artifacts')
            stats['total_artifacts'] = cursor.fetchone()['count']

            # Classification count
            cursor.execute('SELECT COUNT(*) as count FROM classifications')
            stats['total_classifications'] = cursor.fetchone()['count']

            # Validated classifications
            cursor.execute('SELECT COUNT(*) as count FROM classifications WHERE validated = 1')
            stats['validated_classifications'] = cursor.fetchone()['count']

            # Training samples
            cursor.execute('SELECT COUNT(*) as count FROM training_data WHERE is_validated = 1')
            stats['training_samples'] = cursor.fetchone()['count']

            # Analysis results
            cursor.execute('SELECT COUNT(*) as count FROM analysis_results')
            stats['analysis_results'] = cursor.fetchone()['count']

            # Comparisons
            cursor.execute('SELECT COUNT(*) as count FROM comparisons')
            stats['comparisons'] = cursor.fetchone()['count']

            return stats

    def export_data(self, output_path: str):
        """Export entire database to JSON."""
        data = {
            'artifacts': self.get_all_artifacts(),
            'features': self.get_all_features(),
            'validated_classifications': self.get_validated_classifications(),
            'training_data': self.get_training_data(),
            'statistics': self.get_statistics()
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        return output_path

    # ========== USER OPERATIONS ==========

    def add_user(self, username: str, email: str, password_hash: str,
                 role: str = 'viewer', full_name: str = None) -> int:
        """Add a new user to the database.

        Args:
            username: Unique username
            email: Unique email address
            password_hash: Hashed password (use bcrypt)
            role: User role ('admin', 'archaeologist', 'viewer')
            full_name: Optional full name

        Returns:
            user_id of created user

        Raises:
            sqlite3.IntegrityError: If username or email already exists
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role, full_name, created_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (username, email, password_hash, role, full_name, datetime.now().isoformat()))
            return cursor.lastrowid

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (email,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def update_last_login(self, user_id: int):
        """Update user's last login timestamp."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))

    def get_all_users(self) -> List[Dict]:
        """Get all active users (exclude password hashes)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, email, role, full_name, created_date, last_login
                FROM users WHERE is_active = 1
                ORDER BY created_date DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def update_user_role(self, user_id: int, new_role: str):
        """Update user's role."""
        valid_roles = ['admin', 'archaeologist', 'viewer']
        if new_role not in valid_roles:
            raise ValueError(f"Invalid role: {new_role}. Must be one of {valid_roles}")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', (new_role, user_id))

    def deactivate_user(self, user_id: int):
        """Deactivate user (soft delete)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))

    def activate_user(self, user_id: int):
        """Reactivate a deactivated user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_active = 1 WHERE user_id = ?', (user_id,))

    def update_user(self, user_id: int, email: str = None, full_name: str = None,
                    role: str = None, password_hash: str = None):
        """Update user information (admin only)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if email:
                updates.append('email = ?')
                params.append(email)
            if full_name:
                updates.append('full_name = ?')
                params.append(full_name)
            if role:
                valid_roles = ['admin', 'archaeologist', 'viewer']
                if role not in valid_roles:
                    raise ValueError(f"Invalid role: {role}")
                updates.append('role = ?')
                params.append(role)
            if password_hash:
                updates.append('password_hash = ?')
                params.append(password_hash)

            if updates:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                cursor.execute(query, params)

    def delete_user(self, user_id: int):
        """Permanently delete user (hard delete). Admin only."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))

    def get_all_users_including_inactive(self) -> List[Dict]:
        """Get all users including inactive ones (admin only)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, email, role, full_name, created_date, last_login, is_active
                FROM users
                ORDER BY created_date DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    # ========== PROJECT COLLABORATORS OPERATIONS ==========

    def add_collaborator(self, project_id: str, user_id: int, role: str = 'collaborator'):
        """Add a collaborator to a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO project_collaborators (project_id, user_id, role, invited_date)
                    VALUES (?, ?, ?, ?)
                ''', (project_id, user_id, role, datetime.now().isoformat()))
            except sqlite3.IntegrityError:
                # User already a collaborator
                raise ValueError(f"User {user_id} is already a collaborator on project {project_id}")

    def remove_collaborator(self, project_id: str, user_id: int):
        """Remove a collaborator from a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM project_collaborators
                WHERE project_id = ? AND user_id = ?
            ''', (project_id, user_id))

    def get_project_collaborators(self, project_id: str) -> List[Dict]:
        """Get all collaborators for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pc.*, u.username, u.email, u.full_name
                FROM project_collaborators pc
                JOIN users u ON pc.user_id = u.user_id
                WHERE pc.project_id = ? AND u.is_active = 1
                ORDER BY pc.invited_date DESC
            ''', (project_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_user_projects(self, user_id: int) -> List[Dict]:
        """Get all projects where user is owner or collaborator."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get owned projects
            cursor.execute('''
                SELECT p.*, 'owner' as user_role
                FROM projects p
                WHERE p.owner_id = ? AND p.status = 'active'
            ''', (user_id,))
            owned = [dict(row) for row in cursor.fetchall()]

            # Get collaborated projects
            cursor.execute('''
                SELECT p.*, pc.role as user_role
                FROM projects p
                JOIN project_collaborators pc ON p.project_id = pc.project_id
                WHERE pc.user_id = ? AND p.status = 'active'
            ''', (user_id,))
            collaborated = [dict(row) for row in cursor.fetchall()]

            return owned + collaborated

    def is_project_owner(self, project_id: str, user_id: int) -> bool:
        """Check if user is the owner of a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT owner_id FROM projects WHERE project_id = ?
            ''', (project_id,))
            row = cursor.fetchone()
            return row and row['owner_id'] == user_id

    def is_project_collaborator(self, project_id: str, user_id: int) -> bool:
        """Check if user is a collaborator on a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM project_collaborators
                WHERE project_id = ? AND user_id = ?
            ''', (project_id, user_id))
            return cursor.fetchone() is not None

    def can_access_project(self, project_id: str, user_id: int) -> bool:
        """Check if user can access a project (owner or collaborator)."""
        return self.is_project_owner(project_id, user_id) or \
               self.is_project_collaborator(project_id, user_id)


# Global database instance
_db_instance = None


def get_database() -> ArtifactDatabase:
    """Get or create global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ArtifactDatabase()
    return _db_instance


def backup_database_to_storage(db_path: str = None) -> dict:
    """Backup database to configured storage (Google Drive or local).

    Args:
        db_path: Path to database file (default: from environment)

    Returns:
        dict with backup info: {'status': 'success', 'backup_path': '...', 'timestamp': '...'}
    """
    import os
    import shutil
    from datetime import datetime
    from acs.core.storage import get_default_storage
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Get database path
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', '/data/acs_artifacts.db')

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")

        # Check if backups are enabled
        if os.getenv('DB_BACKUP_ENABLED', 'true').lower() not in ('true', '1', 'yes'):
            logger.info("Database backups are disabled")
            return {'status': 'disabled', 'message': 'DB_BACKUP_ENABLED is false'}

        # Create backup filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"acs_artifacts_backup_{timestamp}.db"
        remote_path = f"backups/database/{backup_filename}"

        # Get storage backend
        storage = get_default_storage()

        # Upload to storage
        logger.info(f"Backing up database to storage: {remote_path}")
        storage_id = storage.upload_file(db_path, remote_path)

        logger.info(f"✅ Database backup successful: {backup_filename}")

        return {
            'status': 'success',
            'backup_path': remote_path,
            'backup_filename': backup_filename,
            'timestamp': timestamp,
            'storage_backend': os.getenv('STORAGE_BACKEND', 'local'),
            'storage_id': storage_id
        }

    except Exception as e:
        logger.error(f"Database backup failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def restore_database_from_storage(db_path: str = None) -> dict:
    """Restore database from cloud storage (Dropbox/Google Drive).

    Finds the most recent backup and restores it if local DB is empty or missing.

    Args:
        db_path: Path to restore database to (default: from environment)

    Returns:
        dict with restore info: {'status': 'success'/'skipped'/'error', ...}
    """
    import os
    import shutil
    import tempfile
    from datetime import datetime
    from acs.core.storage import get_default_storage, LocalStorage
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Get database path
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', '/data/acs_artifacts.db')

        # Check if restore is enabled
        if os.getenv('DB_RESTORE_ENABLED', 'true').lower() not in ('true', '1', 'yes'):
            logger.info("Database restore is disabled")
            return {'status': 'disabled', 'message': 'DB_RESTORE_ENABLED is false'}

        # Check if local DB already has ACTUAL DATA (not just schema)
        local_artifact_count = 0
        if os.path.exists(db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM artifacts')
                local_artifact_count = cursor.fetchone()[0]
                conn.close()
                logger.info(f"Local database has {local_artifact_count} artifacts")
            except Exception as e:
                logger.warning(f"Could not count local artifacts: {e}")
                local_artifact_count = 0

        # Only skip restore if local DB has actual artifacts
        if local_artifact_count > 0:
            logger.info(f"Local database has {local_artifact_count} artifacts, skipping restore")
            return {'status': 'skipped', 'reason': 'local_db_has_data', 'artifact_count': local_artifact_count}

        # Get storage backend
        storage = get_default_storage()

        # Skip if using local storage (nothing to restore from)
        if isinstance(storage, LocalStorage):
            logger.info("Using local storage, no cloud backup to restore from")
            return {'status': 'skipped', 'reason': 'local_storage'}

        # List backups and find the most recent
        logger.info("Looking for database backups in cloud storage...")
        try:
            backups = storage.list_files('backups/database')
        except Exception as e:
            logger.warning(f"Could not list backups: {e}")
            return {'status': 'skipped', 'reason': 'no_backups_found', 'error': str(e)}

        if not backups:
            logger.info("No backups found in cloud storage")
            return {'status': 'skipped', 'reason': 'no_backups'}

        # Sort by name (timestamp) to get most recent
        db_backups = [b for b in backups if b['name'].endswith('.db')]
        if not db_backups:
            logger.info("No database backups found")
            return {'status': 'skipped', 'reason': 'no_db_backups'}

        db_backups.sort(key=lambda x: x['name'], reverse=True)
        latest_backup = db_backups[0]

        logger.info(f"Found latest backup: {latest_backup['name']}")

        # Download to temp file first
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = tmp.name

        try:
            remote_path = f"backups/database/{latest_backup['name']}"
            storage.download_file(remote_path, tmp_path)

            # Verify downloaded file
            if os.path.getsize(tmp_path) < 1000:
                raise ValueError("Downloaded backup file is too small, may be corrupted")

            # Ensure target directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            # Move temp file to target location
            shutil.move(tmp_path, db_path)

            logger.info(f"✅ Database restored from: {latest_backup['name']}")

            return {
                'status': 'success',
                'restored_from': latest_backup['name'],
                'restored_to': db_path,
                'backup_size': latest_backup.get('size', 0),
                'storage_backend': os.getenv('STORAGE_BACKEND', 'local')
            }

        finally:
            # Clean up temp file if it still exists
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Database restore failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def auto_sync_database() -> dict:
    """Automatically sync database with cloud storage.

    On startup:
    1. Try to restore from cloud if local DB is empty/missing
    2. If local DB has data, backup to cloud

    Returns:
        dict with sync results
    """
    import os
    import logging

    logger = logging.getLogger(__name__)
    results = {'restore': None, 'backup': None}

    try:
        db_path = os.getenv('DATABASE_PATH', '/data/acs_artifacts.db')

        # Step 1: Try to restore if needed
        logger.info("🔄 Auto-sync: Checking if restore is needed...")
        restore_result = restore_database_from_storage(db_path)
        results['restore'] = restore_result

        if restore_result.get('status') == 'success':
            logger.info(f"✅ Restored database from cloud: {restore_result.get('restored_from')}")
        elif restore_result.get('status') == 'skipped':
            skip_reason = restore_result.get('reason', '')

            # Backup to cloud if:
            # 1. Local DB exists with data
            # 2. No backups found in cloud (create first backup)
            # 3. Folder doesn't exist yet
            should_backup = skip_reason in ('local_db_has_data', 'no_backups', 'no_db_backups', 'no_backups_found')

            if should_backup:
                if not os.path.exists(db_path):
                    logger.info(f"ℹ️ No local database yet at {db_path}, nothing to backup")
                else:
                    # Check if local DB has actual artifacts before backing up
                    local_artifact_count = 0
                    try:
                        import sqlite3
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute('SELECT COUNT(*) FROM artifacts')
                        local_artifact_count = cursor.fetchone()[0]
                        conn.close()
                    except:
                        pass

                    if local_artifact_count == 0:
                        logger.info(f"ℹ️ Local database has 0 artifacts, skipping backup to avoid overwriting good data")
                    else:
                        logger.info(f"🔄 Auto-sync: Backing up local database ({local_artifact_count} artifacts) to cloud...")
                        backup_result = backup_database_to_storage(db_path)
                        results['backup'] = backup_result

                        if backup_result.get('status') == 'success':
                            logger.info(f"✅ Backed up database to cloud: {backup_result.get('backup_filename')}")
                        elif backup_result.get('status') == 'error':
                            logger.warning(f"⚠️ Backup failed: {backup_result.get('error')}")
            else:
                logger.info(f"ℹ️ Skipping sync: {skip_reason}")

        return results

    except Exception as e:
        logger.error(f"Auto-sync failed: {e}", exc_info=True)
        results['error'] = str(e)
        return results
