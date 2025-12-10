# Testing Protected Endpoints

## Overview

All API endpoints are now protected with authentication. You need a valid JWT token to access them.

## Quick Test Guide

### 1. Start the Server

```bash
cd archaeological-classifier
python -m acs.api.app
```

### 2. Login and Get Token

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -m json.tool

# Save the token from the response
export TOKEN="eyJ..."
```

### 3. Test Protected Endpoints

#### Upload Mesh (requires archaeologist or admin)

```bash
curl -X POST http://localhost:5000/api/mesh/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@path/to/mesh.obj" \
  -F "artifact_id=test_axe"
```

#### Get Artifact (requires any authenticated user)

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/mesh/test_axe
```

#### Export Data (requires admin)

```bash
curl -X POST http://localhost:5000/api/mesh/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format":"json"}'
```

### 4. Test Unauthorized Access

```bash
# Without token - should return 401
curl http://localhost:5000/api/mesh/upload

# With viewer role trying admin endpoint - should return 403
# (first register a viewer user, login, and try admin endpoint)
```

## Endpoint Protection Summary

### Mesh Endpoints (`/api/mesh/`)

| Endpoint | Method | Required Role |
|----------|--------|---------------|
| `/upload` | POST | admin, archaeologist |
| `/batch` | POST | admin, archaeologist |
| `/<artifact_id>` | GET | any authenticated |
| `/<id1>/distance/<id2>` | GET | any authenticated |
| `/export` | POST | admin only |

### Savignano Endpoints (`/api/savignano/`)

| Endpoint | Method | Required Role |
|----------|--------|---------------|
| `/status` | GET | **PUBLIC** |
| `/upload-batch` | POST | admin, archaeologist |
| `/configure` | POST | admin, archaeologist |
| `/run-analysis` | POST | admin, archaeologist |
| `/results/<id>` | GET | any authenticated |
| `/download/<id>/<type>` | GET | any authenticated |
| `/generate-drawings/<id>` | POST | admin, archaeologist |
| `/download-drawing/<id>/<type>` | GET | any authenticated |
| `/supported-languages` | GET | **PUBLIC** |
| `/generate-comprehensive-report/<id>` | POST | admin, archaeologist |
| `/generate-comprehensive-report-stream/<id>` | GET | admin, archaeologist |
| `/download-comprehensive-report/<id>` | GET | any authenticated |

### Classification Endpoints (`/api/classification/`)

| Endpoint | Method | Required Role |
|----------|--------|---------------|
| `/define-class` | POST | admin, archaeologist |
| `/classify` | POST | admin, archaeologist |
| `/classify-savignano` | POST | admin, archaeologist |
| `/savignano-classes` | GET | any authenticated |
| `/modify-class` | POST | admin, archaeologist |
| `/discover` | POST | admin, archaeologist |
| `/classes` | GET | any authenticated |
| `/classes/<id>` | GET | any authenticated |
| `/export` | GET | admin only |
| `/import` | POST | admin only |
| `/statistics` | GET | any authenticated |

### Morphometric Endpoints (`/api/morphometric/`)

| Endpoint | Method | Required Role |
|----------|--------|---------------|
| `/add-features` | POST | admin, archaeologist |
| `/pca` | POST | admin, archaeologist |
| `/cluster` | POST | admin, archaeologist |
| `/dbscan` | POST | admin, archaeologist |
| `/similarity` | POST | any authenticated |
| `/find-similar` | POST | any authenticated |
| `/statistics` | GET | any authenticated |

## Error Responses

### 401 Unauthorized (No Token)

```json
{
  "error": "Authentication required",
  "code": "NO_TOKEN"
}
```

### 401 Unauthorized (Invalid Token)

```json
{
  "error": "Invalid or expired token",
  "code": "INVALID_TOKEN"
}
```

### 403 Forbidden (Insufficient Permissions)

```json
{
  "error": "Access denied. Required roles: admin, archaeologist",
  "code": "INSUFFICIENT_PERMISSIONS"
}
```

## Python Client Example

```python
import requests

# Login
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['token']

# Use token for authenticated requests
headers = {'Authorization': f'Bearer {token}'}

# Upload mesh
with open('axe.obj', 'rb') as f:
    files = {'file': f}
    data = {'artifact_id': 'axe001'}
    response = requests.post(
        'http://localhost:5000/api/mesh/upload',
        headers=headers,
        files=files,
        data=data
    )
    print(response.json())
```

## Next Steps

1. Change default admin password
2. Create users with appropriate roles
3. Integrate frontend with authentication
4. Add refresh token mechanism (future)
5. Add rate limiting (future)
