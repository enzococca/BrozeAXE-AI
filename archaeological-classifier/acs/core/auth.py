"""
Authentication Module
=====================

JWT-based authentication with password hashing for BrozeAXE-AI.
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from typing import Optional, Dict, Callable
from .database import get_database


# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24  # Token expires after 24 hours


class PasswordHasher:
    """Password hashing utilities using bcrypt."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password as string
        """
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash.

        Args:
            password: Plain text password to verify
            password_hash: Stored password hash

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False


class JWTManager:
    """JWT token management."""

    @staticmethod
    def generate_token(user_id: int, username: str, role: str) -> str:
        """Generate JWT token for authenticated user.

        Args:
            user_id: User ID
            username: Username
            role: User role

        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dict, or None if invalid/expired
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.InvalidTokenError:
            return None  # Invalid token

    @staticmethod
    def get_token_from_request() -> Optional[str]:
        """Extract JWT token from request headers or query parameters.

        Looks for token in:
        1. Authorization header: "Bearer <token>"
        2. X-Access-Token header: "<token>"
        3. Query parameter: "?token=<token>" (for EventSource/SSE compatibility)

        Returns:
            Token string or None
        """
        # Check Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove "Bearer " prefix

        # Check X-Access-Token header
        token = request.headers.get('X-Access-Token')
        if token:
            return token

        # Check query parameter (for EventSource/SSE which can't send custom headers)
        token = request.args.get('token')
        if token:
            return token

        return None


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password.

    Args:
        username: Username
        password: Plain text password

    Returns:
        User dict (without password_hash) if authenticated, None otherwise
    """
    db = get_database()
    user = db.get_user_by_username(username)

    if not user:
        return None

    # Verify password
    if not PasswordHasher.verify_password(password, user['password_hash']):
        return None

    # Update last login
    db.update_last_login(user['user_id'])

    # Remove password hash from returned user
    user_safe = {k: v for k, v in user.items() if k != 'password_hash'}

    return user_safe


def login_required(f: Callable) -> Callable:
    """Decorator to protect routes requiring authentication.

    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            user = g.current_user
            return jsonify({'message': f'Hello {user["username"]}'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = JWTManager.get_token_from_request()

        if not token:
            return jsonify({'error': 'Authentication required', 'code': 'NO_TOKEN'}), 401

        payload = JWTManager.decode_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token', 'code': 'INVALID_TOKEN'}), 401

        # Store user info in Flask's g object for access in route
        g.current_user = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role']
        }

        return f(*args, **kwargs)

    return decorated_function


def role_required(*allowed_roles: str):
    """Decorator to protect routes requiring specific roles.

    Args:
        allowed_roles: Tuple of allowed role strings ('admin', 'archaeologist', 'viewer')

    Usage:
        @app.route('/admin-only')
        @role_required('admin')
        def admin_route():
            return jsonify({'message': 'Admin area'})

        @app.route('/expert-area')
        @role_required('admin', 'archaeologist')
        def expert_route():
            return jsonify({'message': 'Expert area'})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = JWTManager.get_token_from_request()

            if not token:
                return jsonify({'error': 'Authentication required', 'code': 'NO_TOKEN'}), 401

            payload = JWTManager.decode_token(token)

            if not payload:
                return jsonify({'error': 'Invalid or expired token', 'code': 'INVALID_TOKEN'}), 401

            user_role = payload['role']

            if user_role not in allowed_roles:
                return jsonify({
                    'error': f'Access denied. Required roles: {", ".join(allowed_roles)}',
                    'code': 'INSUFFICIENT_PERMISSIONS'
                }), 403

            # Store user info in Flask's g object
            g.current_user = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'role': payload['role']
            }

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def register_user(username: str, email: str, password: str,
                  role: str = 'viewer', full_name: str = None) -> Dict:
    """Register a new user.

    Args:
        username: Unique username
        email: Unique email
        password: Plain text password (will be hashed)
        role: User role (default: 'viewer')
        full_name: Optional full name

    Returns:
        Dict with user info and token

    Raises:
        ValueError: If username/email already exists or invalid role
    """
    valid_roles = ['admin', 'archaeologist', 'viewer']
    if role not in valid_roles:
        raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")

    db = get_database()

    # Check if username exists
    if db.get_user_by_username(username):
        raise ValueError(f"Username '{username}' already exists")

    # Check if email exists
    if db.get_user_by_email(email):
        raise ValueError(f"Email '{email}' already registered")

    # Hash password
    password_hash = PasswordHasher.hash_password(password)

    # Create user
    user_id = db.add_user(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
        full_name=full_name
    )

    # Generate token
    token = JWTManager.generate_token(user_id, username, role)

    return {
        'user_id': user_id,
        'username': username,
        'email': email,
        'role': role,
        'full_name': full_name,
        'token': token
    }


def create_default_admin():
    """Create default admin user if no users exist.

    Default credentials:
    - Username: admin
    - Password: admin123 (CHANGE IMMEDIATELY IN PRODUCTION)
    - Role: admin
    """
    db = get_database()

    # Check if any users exist
    users = db.get_all_users()
    if len(users) > 0:
        return None  # Users already exist

    # Create default admin
    try:
        admin = register_user(
            username='admin',
            email='admin@brozeaxe.local',
            password='admin123',
            role='admin',
            full_name='Default Administrator'
        )
        return admin
    except ValueError:
        return None  # Admin already exists
