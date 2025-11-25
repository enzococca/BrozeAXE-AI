"""
Authentication Blueprint
========================

REST API endpoints for user authentication and management.
"""

from flask import Blueprint, request, jsonify, g
from acs.core.auth import (
    authenticate_user,
    register_user,
    login_required,
    role_required,
    JWTManager,
    PasswordHasher
)
from acs.core.database import get_database
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint.

    Request JSON:
    {
        "username": "user123",
        "password": "password123"
    }

    Response:
    {
        "status": "success",
        "user": {
            "user_id": 1,
            "username": "user123",
            "email": "user@example.com",
            "role": "archaeologist",
            "full_name": "John Doe"
        },
        "token": "eyJ..."
    }
    """
    try:
        data = request.get_json()

        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Missing username or password',
                'code': 'MISSING_CREDENTIALS'
            }), 400

        username = data['username']
        password = data['password']

        # Authenticate
        user = authenticate_user(username, password)

        if not user:
            logger.warning(f"Failed login attempt for username: {username}")
            return jsonify({
                'status': 'error',
                'error': 'Invalid username or password',
                'code': 'INVALID_CREDENTIALS'
            }), 401

        # Generate token
        token = JWTManager.generate_token(
            user['user_id'],
            user['username'],
            user['role']
        )

        logger.info(f"User logged in: {username} (role: {user['role']})")

        return jsonify({
            'status': 'success',
            'user': user,
            'token': token
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Login failed',
            'details': str(e)
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user endpoint.

    Request JSON:
    {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "full_name": "John Doe",  // optional
        "role": "viewer"  // optional, default: viewer
    }

    Response:
    {
        "status": "success",
        "user": {
            "user_id": 2,
            "username": "newuser",
            "email": "newuser@example.com",
            "role": "viewer",
            "full_name": "John Doe"
        },
        "token": "eyJ..."
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['username', 'email', 'password']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'status': 'error',
                'error': f'Missing required fields: {", ".join(missing)}',
                'code': 'MISSING_FIELDS'
            }), 400

        # Extract data
        username = data['username']
        email = data['email']
        password = data['password']
        role = data.get('role', 'viewer')
        full_name = data.get('full_name')

        # Validate username length
        if len(username) < 3:
            return jsonify({
                'status': 'error',
                'error': 'Username must be at least 3 characters',
                'code': 'INVALID_USERNAME'
            }), 400

        # Validate password strength
        if len(password) < 6:
            return jsonify({
                'status': 'error',
                'error': 'Password must be at least 6 characters',
                'code': 'WEAK_PASSWORD'
            }), 400

        # Register user
        result = register_user(
            username=username,
            email=email,
            password=password,
            role=role,
            full_name=full_name
        )

        logger.info(f"New user registered: {username} (role: {role})")

        return jsonify({
            'status': 'success',
            'user': {
                'user_id': result['user_id'],
                'username': result['username'],
                'email': result['email'],
                'role': result['role'],
                'full_name': result['full_name']
            },
            'token': result['token']
        }), 201

    except ValueError as e:
        # Username/email already exists
        return jsonify({
            'status': 'error',
            'error': str(e),
            'code': 'VALIDATION_ERROR'
        }), 400

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Registration failed',
            'details': str(e)
        }), 500


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current authenticated user info.

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "user": {
            "user_id": 1,
            "username": "user123",
            "role": "archaeologist"
        }
    }
    """
    return jsonify({
        'status': 'success',
        'user': g.current_user
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout endpoint.

    Note: With JWT, logout is typically handled client-side by
    discarding the token. This endpoint is provided for logging purposes.

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "message": "Logged out successfully"
    }
    """
    logger.info(f"User logged out: {g.current_user['username']}")

    return jsonify({
        'status': 'success',
        'message': 'Logged out successfully'
    }), 200


@auth_bp.route('/users', methods=['GET'])
@role_required('admin')
def list_users():
    """List all users (admin only).

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "users": [
            {
                "user_id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "role": "admin",
                "full_name": "Admin User",
                "created_date": "2025-11-24T10:00:00",
                "last_login": "2025-11-24T12:00:00"
            },
            ...
        ]
    }
    """
    try:
        db = get_database()
        users = db.get_all_users()

        return jsonify({
            'status': 'success',
            'users': users
        }), 200

    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to retrieve users',
            'details': str(e)
        }), 500


@auth_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@role_required('admin')
def update_user_role(user_id):
    """Update user role (admin only).

    Headers:
        Authorization: Bearer <token>

    Request JSON:
    {
        "role": "archaeologist"
    }

    Response:
    {
        "status": "success",
        "message": "User role updated successfully"
    }
    """
    try:
        data = request.get_json()

        if not data or 'role' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Missing role field',
                'code': 'MISSING_ROLE'
            }), 400

        new_role = data['role']
        valid_roles = ['admin', 'archaeologist', 'viewer']

        if new_role not in valid_roles:
            return jsonify({
                'status': 'error',
                'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}',
                'code': 'INVALID_ROLE'
            }), 400

        db = get_database()

        # Check if user exists
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404

        # Update role
        db.update_user_role(user_id, new_role)

        logger.info(f"User role updated: user_id={user_id}, new_role={new_role} (by {g.current_user['username']})")

        return jsonify({
            'status': 'success',
            'message': 'User role updated successfully'
        }), 200

    except Exception as e:
        logger.error(f"Update role error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to update user role',
            'details': str(e)
        }), 500


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@role_required('admin')
def deactivate_user(user_id):
    """Deactivate user (admin only).

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "message": "User deactivated successfully"
    }
    """
    try:
        db = get_database()

        # Check if user exists
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404

        # Prevent self-deactivation
        if user_id == g.current_user['user_id']:
            return jsonify({
                'status': 'error',
                'error': 'Cannot deactivate your own account',
                'code': 'SELF_DEACTIVATION'
            }), 400

        # Deactivate user
        db.deactivate_user(user_id)

        logger.info(f"User deactivated: user_id={user_id}, username={user['username']} (by {g.current_user['username']})")

        return jsonify({
            'status': 'success',
            'message': 'User deactivated successfully'
        }), 200

    except Exception as e:
        logger.error(f"Deactivate user error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to deactivate user',
            'details': str(e)
        }), 500


@auth_bp.route('/users/<int:user_id>/activate', methods=['PUT'])
@role_required('admin')
def activate_user(user_id):
    """Activate user (admin only).

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "message": "User activated successfully"
    }
    """
    try:
        db = get_database()

        # Check if user exists
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404

        # Activate user
        db.activate_user(user_id)

        logger.info(f"User activated: user_id={user_id}, username={user.get('username')} (by {g.current_user['username']})")

        return jsonify({
            'status': 'success',
            'message': 'User activated successfully'
        }), 200

    except Exception as e:
        logger.error(f"Activate user error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to activate user',
            'details': str(e)
        }), 500


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@role_required('admin')
def update_user(user_id):
    """Update user information (admin only).

    Headers:
        Authorization: Bearer <token>

    Request JSON:
    {
        "email": "new@example.com",  // optional
        "full_name": "New Name",  // optional
        "role": "archaeologist",  // optional
        "password": "newpassword"  // optional
    }

    Response:
    {
        "status": "success",
        "message": "User updated successfully"
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

        # Check if user exists
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404

        # Hash password if provided
        password_hash = None
        if 'password' in data:
            password_hash = PasswordHasher.hash_password(data['password'])

        # Update user
        db.update_user(
            user_id=user_id,
            email=data.get('email'),
            full_name=data.get('full_name'),
            role=data.get('role'),
            password_hash=password_hash
        )

        logger.info(f"User updated: user_id={user_id} (by {g.current_user['username']})")

        return jsonify({
            'status': 'success',
            'message': 'User updated successfully'
        }), 200

    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'code': 'VALIDATION_ERROR'
        }), 400

    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to update user',
            'details': str(e)
        }), 500


@auth_bp.route('/users/<int:user_id>/delete-permanently', methods=['DELETE'])
@role_required('admin')
def delete_user_permanently(user_id):
    """Permanently delete user (admin only). WARNING: This cannot be undone!

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "message": "User permanently deleted"
    }
    """
    try:
        db = get_database()

        # Check if user exists
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404

        # Prevent self-deletion
        if user_id == g.current_user['user_id']:
            return jsonify({
                'status': 'error',
                'error': 'Cannot delete your own account',
                'code': 'SELF_DELETION'
            }), 400

        # Delete user permanently
        db.delete_user(user_id)

        logger.warning(f"User permanently deleted: user_id={user_id}, username={user['username']} (by {g.current_user['username']})")

        return jsonify({
            'status': 'success',
            'message': 'User permanently deleted'
        }), 200

    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to delete user',
            'details': str(e)
        }), 500


@auth_bp.route('/users/all', methods=['GET'])
@role_required('admin')
def list_all_users():
    """List all users including inactive (admin only).

    Headers:
        Authorization: Bearer <token>

    Response:
    {
        "status": "success",
        "users": [...]
    }
    """
    try:
        db = get_database()
        users = db.get_all_users_including_inactive()

        return jsonify({
            'status': 'success',
            'users': users
        }), 200

    except Exception as e:
        logger.error(f"List all users error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to retrieve users',
            'details': str(e)
        }), 500


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change password for current user.

    Headers:
        Authorization: Bearer <token>

    Request JSON:
    {
        "current_password": "oldpass123",
        "new_password": "newpass123"
    }

    Response:
    {
        "status": "success",
        "message": "Password changed successfully"
    }
    """
    try:
        data = request.get_json()

        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Missing current_password or new_password',
                'code': 'MISSING_FIELDS'
            }), 400

        current_password = data['current_password']
        new_password = data['new_password']

        # Validate new password strength
        if len(new_password) < 6:
            return jsonify({
                'status': 'error',
                'error': 'New password must be at least 6 characters',
                'code': 'WEAK_PASSWORD'
            }), 400

        db = get_database()
        user = db.get_user_by_id(g.current_user['user_id'])

        # Verify current password
        if not PasswordHasher.verify_password(current_password, user['password_hash']):
            return jsonify({
                'status': 'error',
                'error': 'Current password is incorrect',
                'code': 'INVALID_PASSWORD'
            }), 401

        # Hash new password
        new_hash = PasswordHasher.hash_password(new_password)

        # Update password in database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET password_hash = ? WHERE user_id = ?',
                (new_hash, g.current_user['user_id'])
            )

        logger.info(f"Password changed for user: {g.current_user['username']}")

        return jsonify({
            'status': 'success',
            'message': 'Password changed successfully'
        }), 200

    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Failed to change password',
            'details': str(e)
        }), 500
