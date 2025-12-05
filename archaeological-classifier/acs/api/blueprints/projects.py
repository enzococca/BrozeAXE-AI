"""
Projects Blueprint
==================

REST API endpoints for project management and collaboration.
"""

from flask import Blueprint, request, jsonify, g
from acs.core.auth import login_required, role_required
from acs.core.database import get_database
import logging
import uuid

logger = logging.getLogger(__name__)

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


@projects_bp.route('/', methods=['GET'])
@login_required
def list_projects():
    """List all projects accessible by current user.

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "projects": [
            {
                "project_id": "proj-123",
                "project_name": "Site A Excavation",
                "description": "...",
                "owner_id": 1,
                "user_role": "owner",  // or "collaborator"
                "created_date": "2025-11-24T10:00:00",
                "status": "active"
            },
            ...
        ]
    }
    """
    try:
        db = get_database()
        user_id = g.current_user['user_id']

        # Admin can see all projects
        if g.current_user['role'] == 'admin':
            projects = db.list_projects(status='active')
            for project in projects:
                project['user_role'] = 'admin'
        else:
            # Get user's projects (owned + collaborated)
            projects = db.get_user_projects(user_id)

        return jsonify({
            'status': 'success',
            'projects': projects
        }), 200

    except Exception as e:
        logger.error(f"List projects error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to retrieve projects',
            'details': str(e)
        }), 500


@projects_bp.route('/', methods=['POST'])
@login_required
def create_project():
    """Create a new project.

    Headers:
        Authorization: Bearer <token>

    Request JSON:
    {
        "project_name": "Site B Analysis",
        "description": "Analysis of artifacts from Site B"
    }

    Response:
    {
        "status": "success",
        "project": {
            "project_id": "proj-456",
            "project_name": "Site B Analysis",
            "description": "...",
            "owner_id": 1,
            "created_date": "...",
            "status": "active"
        }
    }
    """
    try:
        data = request.get_json()

        if not data or 'project_name' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Missing project_name field',
                'code': 'MISSING_NAME'
            }), 400

        project_name = data['project_name']
        description = data.get('description', '')

        # Generate unique project ID
        project_id = f"proj-{uuid.uuid4().hex[:8]}"

        db = get_database()
        db.create_project(
            project_id=project_id,
            name=project_name,
            owner_id=g.current_user['user_id'],
            description=description
        )

        # Get created project
        project = db.get_project(project_id)

        logger.info(f"Project created: {project_id} by user {g.current_user['username']}")

        return jsonify({
            'status': 'success',
            'project': project
        }), 201

    except Exception as e:
        logger.error(f"Create project error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to create project',
            'details': str(e)
        }), 500


@projects_bp.route('/<project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    """Get project details.

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "project": {...},
        "collaborators": [...]
    }
    """
    try:
        db = get_database()
        user_id = g.current_user['user_id']
        role = g.current_user['role']

        # Check access
        if role != 'admin' and not db.can_access_project(project_id, user_id):
            return jsonify({
                'status': 'error',
                'error': 'Access denied',
                'code': 'ACCESS_DENIED'
            }), 403

        project = db.get_project(project_id)
        if not project:
            return jsonify({
                'status': 'error',
                'error': 'Project not found',
                'code': 'PROJECT_NOT_FOUND'
            }), 404

        # Get collaborators
        collaborators = db.get_project_collaborators(project_id)

        return jsonify({
            'status': 'success',
            'project': project,
            'collaborators': collaborators
        }), 200

    except Exception as e:
        logger.error(f"Get project error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to retrieve project',
            'details': str(e)
        }), 500


@projects_bp.route('/<project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    """Update project (owner only).

    Headers:
        Authorization: Bearer <token>

    Request JSON:
    {
        "project_name": "Updated Name",  // optional
        "description": "Updated description",  // optional
        "status": "archived"  // optional
    }

    Response:
    {
        "status": "success",
        "message": "Project updated successfully"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'error': 'No data provided',
                'code': 'MISSING_DATA'
            }), 400

        db = get_database()
        user_id = g.current_user['user_id']
        role = g.current_user['role']

        # Check if project exists
        project = db.get_project(project_id)
        if not project:
            return jsonify({
                'status': 'error',
                'error': 'Project not found',
                'code': 'PROJECT_NOT_FOUND'
            }), 404

        # Only owner or admin can update
        if role != 'admin' and not db.is_project_owner(project_id, user_id):
            return jsonify({
                'status': 'error',
                'error': 'Only project owner can update project',
                'code': 'ACCESS_DENIED'
            }), 403

        # Update project
        with db.get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if 'project_name' in data:
                updates.append('project_name = ?')
                params.append(data['project_name'])

            if 'description' in data:
                updates.append('description = ?')
                params.append(data['description'])

            if 'status' in data:
                updates.append('status = ?')
                params.append(data['status'])

            if updates:
                params.append(project_id)
                query = f"UPDATE projects SET {', '.join(updates)} WHERE project_id = ?"
                cursor.execute(query, params)

        logger.info(f"Project updated: {project_id} by {g.current_user['username']}")

        return jsonify({
            'status': 'success',
            'message': 'Project updated successfully'
        }), 200

    except Exception as e:
        logger.error(f"Update project error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to update project',
            'details': str(e)
        }), 500


@projects_bp.route('/<project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Archive project (owner only).

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "message": "Project archived successfully"
    }
    """
    try:
        db = get_database()
        user_id = g.current_user['user_id']
        role = g.current_user['role']

        # Check if project exists
        project = db.get_project(project_id)
        if not project:
            return jsonify({
                'status': 'error',
                'error': 'Project not found',
                'code': 'PROJECT_NOT_FOUND'
            }), 404

        # Only owner or admin can delete
        if role != 'admin' and not db.is_project_owner(project_id, user_id):
            return jsonify({
                'status': 'error',
                'error': 'Only project owner can delete project',
                'code': 'ACCESS_DENIED'
            }), 403

        # Archive project (soft delete)
        db.update_project_status(project_id, 'archived')

        logger.info(f"Project archived: {project_id} by {g.current_user['username']}")

        return jsonify({
            'status': 'success',
            'message': 'Project archived successfully'
        }), 200

    except Exception as e:
        logger.error(f"Delete project error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to delete project',
            'details': str(e)
        }), 500


# ============ COLLABORATORS ============

@projects_bp.route('/<project_id>/collaborators', methods=['POST'])
@login_required
def add_collaborator(project_id):
    """Add collaborator to project (owner only).

    Headers:
        Authorization: Bearer <token>

    Request JSON:
    {
        "user_id": 2,
        "role": "collaborator"  // optional
    }

    Response:
    {
        "status": "success",
        "message": "Collaborator added successfully"
    }
    """
    try:
        data = request.get_json()

        if not data or 'user_id' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Missing user_id field',
                'code': 'MISSING_USER_ID'
            }), 400

        collaborator_user_id = data['user_id']
        collab_role = data.get('role', 'collaborator')

        db = get_database()
        current_user_id = g.current_user['user_id']
        current_user_role = g.current_user['role']

        # Check if project exists
        project = db.get_project(project_id)
        if not project:
            return jsonify({
                'status': 'error',
                'error': 'Project not found',
                'code': 'PROJECT_NOT_FOUND'
            }), 404

        # Only owner or admin can add collaborators
        if current_user_role != 'admin' and not db.is_project_owner(project_id, current_user_id):
            return jsonify({
                'status': 'error',
                'error': 'Only project owner can add collaborators',
                'code': 'ACCESS_DENIED'
            }), 403

        # Check if user exists
        user = db.get_user_by_id(collaborator_user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404

        # Add collaborator
        db.add_collaborator(project_id, collaborator_user_id, collab_role)

        logger.info(f"Collaborator added to project {project_id}: user_id={collaborator_user_id} by {g.current_user['username']}")

        return jsonify({
            'status': 'success',
            'message': 'Collaborator added successfully'
        }), 201

    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'code': 'VALIDATION_ERROR'
        }), 400

    except Exception as e:
        logger.error(f"Add collaborator error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to add collaborator',
            'details': str(e)
        }), 500


@projects_bp.route('/<project_id>/collaborators/<int:user_id>', methods=['DELETE'])
@login_required
def remove_collaborator(project_id, user_id):
    """Remove collaborator from project (owner only).

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "message": "Collaborator removed successfully"
    }
    """
    try:
        db = get_database()
        current_user_id = g.current_user['user_id']
        current_user_role = g.current_user['role']

        # Check if project exists
        project = db.get_project(project_id)
        if not project:
            return jsonify({
                'status': 'error',
                'error': 'Project not found',
                'code': 'PROJECT_NOT_FOUND'
            }), 404

        # Only owner or admin can remove collaborators
        if current_user_role != 'admin' and not db.is_project_owner(project_id, current_user_id):
            return jsonify({
                'status': 'error',
                'error': 'Only project owner can remove collaborators',
                'code': 'ACCESS_DENIED'
            }), 403

        # Remove collaborator
        db.remove_collaborator(project_id, user_id)

        logger.info(f"Collaborator removed from project {project_id}: user_id={user_id} by {g.current_user['username']}")

        return jsonify({
            'status': 'success',
            'message': 'Collaborator removed successfully'
        }), 200

    except Exception as e:
        logger.error(f"Remove collaborator error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to remove collaborator',
            'details': str(e)
        }), 500


@projects_bp.route('/<project_id>/collaborators', methods=['GET'])
@login_required
def list_collaborators(project_id):
    """List all collaborators for a project.

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "collaborators": [
            {
                "user_id": 2,
                "username": "user2",
                "email": "user2@example.com",
                "full_name": "User Two",
                "role": "collaborator",
                "invited_date": "2025-11-24T10:00:00"
            },
            ...
        ]
    }
    """
    try:
        db = get_database()
        user_id = g.current_user['user_id']
        role = g.current_user['role']

        # Check access
        if role != 'admin' and not db.can_access_project(project_id, user_id):
            return jsonify({
                'status': 'error',
                'error': 'Access denied',
                'code': 'ACCESS_DENIED'
            }), 403

        collaborators = db.get_project_collaborators(project_id)

        return jsonify({
            'status': 'success',
            'collaborators': collaborators
        }), 200

    except Exception as e:
        logger.error(f"List collaborators error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to retrieve collaborators',
            'details': str(e)
        }), 500
