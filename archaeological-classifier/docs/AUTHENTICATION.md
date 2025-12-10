# Authentication System

## Overview

BrozeAXE-AI now includes a complete JWT-based authentication system with role-based access control (RBAC).

## Features

- ✅ **JWT Token Authentication** - Secure token-based auth
- ✅ **Password Hashing** - Bcrypt encryption for passwords
- ✅ **Role-Based Access Control** - Three roles: admin, archaeologist, viewer
- ✅ **User Management** - Create, list, update, deactivate users
- ✅ **Password Change** - Users can change their own password
- ✅ **Default Admin** - Auto-created on first run

## User Roles

| Role | Permissions |
|------|-------------|
| **admin** | Full access - manage users, all artifacts, classifications |
| **archaeologist** | Upload artifacts, classify, validate, generate reports |
| **viewer** | Read-only access - view artifacts and reports |

## Quick Start

### 1. Install Dependencies

```bash
cd archaeological-classifier
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python -m acs.api.app
```

The server will automatically create a default admin user on first run:
- **Username:** `admin`
- **Password:** `admin123`

⚠️ **IMPORTANT:** Change this password immediately!

### 3. Test the System

```bash
cd ..
python test_auth.py
```

## API Endpoints

### Authentication

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "status": "success",
  "user": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin"
  },
  "token": "eyJ..."
}
```

#### Register New User
```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "archaeologist1",
  "email": "user@example.com",
  "password": "password123",
  "role": "archaeologist",
  "full_name": "John Doe"
}

Response:
{
  "status": "success",
  "user": {...},
  "token": "eyJ..."
}
```

#### Get Current User
```bash
GET /api/auth/me
Authorization: Bearer <token>

Response:
{
  "status": "success",
  "user": {
    "user_id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

#### Change Password
```bash
POST /api/auth/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "old123",
  "new_password": "new123"
}
```

### User Management (Admin Only)

#### List All Users
```bash
GET /api/auth/users
Authorization: Bearer <admin-token>
```

#### Update User Role
```bash
PUT /api/auth/users/<user_id>/role
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "role": "archaeologist"
}
```

#### Deactivate User
```bash
DELETE /api/auth/users/<user_id>
Authorization: Bearer <admin-token>
```

## Using Authentication in Code

### Protect a Route

```python
from flask import Blueprint, jsonify
from acs.core.auth import login_required, role_required, g

bp = Blueprint('example', __name__)

# Require any authenticated user
@bp.route('/protected')
@login_required
def protected_route():
    user = g.current_user
    return jsonify({'message': f'Hello {user["username"]}'})

# Require specific role(s)
@bp.route('/admin-only')
@role_required('admin')
def admin_route():
    return jsonify({'message': 'Admin area'})

@bp.route('/expert-area')
@role_required('admin', 'archaeologist')
def expert_route():
    return jsonify({'message': 'Expert area'})
```

### Get Current User in Route

```python
from flask import g

@app.route('/my-artifacts')
@login_required
def my_artifacts():
    user_id = g.current_user['user_id']
    username = g.current_user['username']
    role = g.current_user['role']

    # Use user info...
    artifacts = get_user_artifacts(user_id)
    return jsonify(artifacts)
```

### Manually Verify Token

```python
from acs.core.auth import JWTManager

token = "eyJ..."
payload = JWTManager.decode_token(token)

if payload:
    user_id = payload['user_id']
    username = payload['username']
    role = payload['role']
else:
    # Token invalid or expired
    pass
```

## Frontend Integration

### Store Token

```javascript
// After login
const response = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});

const data = await response.json();
if (data.status === 'success') {
  // Store token in localStorage or sessionStorage
  localStorage.setItem('token', data.token);
  localStorage.setItem('user', JSON.stringify(data.user));
}
```

### Use Token in Requests

```javascript
// Get token
const token = localStorage.getItem('token');

// Make authenticated request
const response = await fetch('http://localhost:5000/api/auth/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Handle Token Expiration

```javascript
const response = await fetch(url, {
  headers: {'Authorization': `Bearer ${token}`}
});

if (response.status === 401) {
  // Token expired or invalid
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  // Redirect to login
  window.location.href = '/login';
}
```

## Security Best Practices

### For Production

1. **Change SECRET_KEY:**
   ```bash
   export SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **Use HTTPS:** Always use HTTPS in production

3. **Secure CORS:**
   ```bash
   export CORS_ORIGINS=https://yourdomain.com
   ```

4. **Change Default Admin Password:**
   ```bash
   curl -X POST http://localhost:5000/api/auth/change-password \
     -H "Authorization: Bearer <admin-token>" \
     -H "Content-Type: application/json" \
     -d '{"current_password": "admin123", "new_password": "secure-password"}'
   ```

5. **Database Backup:** Regularly backup `acs_artifacts.db`

6. **Rate Limiting:** Add rate limiting to auth endpoints (future)

### Password Requirements

- Minimum 6 characters (enforced)
- Recommended: 12+ characters with mixed case, numbers, symbols
- Stored as bcrypt hash (never plaintext)

### Token Expiration

- Default: 24 hours
- Configurable via `JWT_EXPIRATION_HOURS` environment variable
- Client should handle expiration gracefully

## Troubleshooting

### "Authentication required" Error

**Problem:** Getting 401 error on protected endpoint

**Solutions:**
1. Check token is included in header: `Authorization: Bearer <token>`
2. Verify token hasn't expired (24h default)
3. Check token is valid (login again if needed)

### "Access denied" Error

**Problem:** Getting 403 error

**Solutions:**
1. Check user role has permission for endpoint
2. Admin-only endpoints require `role='admin'`
3. Verify with GET /api/auth/me

### Cannot Login

**Problem:** Login returns 401

**Solutions:**
1. Verify username and password are correct
2. Check user is active (not deactivated)
3. Check database exists and has users table

### Default Admin Not Created

**Problem:** admin/admin123 doesn't work

**Solutions:**
1. Check server logs for admin creation message
2. Users might already exist in database
3. Try registering a new admin user

## Database Schema

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'viewer',
    full_name TEXT,
    created_date TEXT,
    last_login TEXT,
    is_active INTEGER DEFAULT 1
);
```

## Future Enhancements

- [ ] Email verification
- [ ] Password reset via email
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, GitHub)
- [ ] API rate limiting
- [ ] Session management
- [ ] Login attempt tracking
- [ ] Password strength meter
- [ ] User profile management
- [ ] Audit log for admin actions

## Files Modified/Created

**Created:**
- `acs/core/auth.py` - Authentication module
- `acs/api/blueprints/auth.py` - Auth endpoints
- `test_auth.py` - Test suite
- `AUTHENTICATION.md` - This documentation
- `.env.example` - Environment template

**Modified:**
- `acs/core/database.py` - Added users table and methods
- `acs/api/app.py` - Registered auth blueprint, fixed CORS
- `requirements.txt` - Added PyJWT and bcrypt

## Support

For issues or questions:
1. Check this documentation
2. Run test suite: `python test_auth.py`
3. Check server logs
4. Review WORKFLOW_TODO.md for planned enhancements
