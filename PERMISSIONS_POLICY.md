# BrozeAXE-AI Permissions Policy

## Overview

This document defines the data access permissions for different API operations.

## Permission Levels

### 1. Project-Scoped Operations (User's Projects Only)
These operations can ONLY access data from projects where the user is either:
- Project owner
- Project collaborator
- Admin (can access all projects)

**Affected Operations:**
- `GET /api/mesh/list` - List uploaded meshes
- `GET /api/morphometric/features` - Get morphometric features
- `GET /api/classification/list` - List classifications
- `POST /api/classification/classify` - Classify artifact (must belong to user's project)
- `GET /api/savignano/artifacts` - List Savignano artifacts
- Query and Report operations

**Implementation:**
```python
# Example: Filter artifacts by user's accessible projects
db = get_database()
user_id = g.current_user['user_id']
role = g.current_user['role']

if role == 'admin':
    # Admin can see all projects
    artifacts = db.get_all_artifacts()
else:
    # Get user's projects (owned + collaborated)
    user_projects = db.get_user_projects(user_id)
    project_ids = [p['project_id'] for p in user_projects]

    # Filter artifacts by project_ids
    artifacts = []
    for project_id in project_ids:
        artifacts.extend(db.get_project_artifacts(project_id))
```

### 2. Global Operations (All Data)
These operations have access to ALL data across ALL users and projects:
- Training ML models
- Model comparisons
- Statistical analysis
- Cross-project pattern recognition

**Affected Operations:**
- `POST /api/classification/train` - Train ML model (uses ALL validated data)
- `POST /api/morphometric/compare` - Compare artifacts (can compare across projects)
- `GET /api/savignano/matrix-analysis` - Matrix analysis (uses ALL Savignano artifacts)
- `POST /api/classification/batch-classify` - Batch classification

**Rationale:**
- ML models need large, diverse datasets for accuracy
- Comparisons are more meaningful with access to full database
- Pattern recognition benefits from cross-project insights

**Implementation:**
```python
# Example: Training uses all data
db = get_database()

# Get ALL training data regardless of project
training_data = db.get_training_data()  # No filtering by project

# Train model on complete dataset
model.fit(training_data)
```

## Access Control Matrix

| Operation | Project Owner | Collaborator | Viewer | Admin |
|-----------|--------------|--------------|--------|-------|
| **Project Data** |  |  |  |  |
| View own project artifacts | ✅ | ✅ | ✅ (read-only) | ✅ (all projects) |
| Upload artifacts | ✅ | ✅ | ❌ | ✅ |
| Delete artifacts | ✅ | ❌ | ❌ | ✅ |
| Classify artifacts | ✅ | ✅ | ❌ | ✅ |
| View others' projects | ❌ | ❌ | ❌ | ✅ |
| **Project Management** |  |  |  |  |
| Create project | ✅ | ✅ | ✅ | ✅ |
| Update own project | ✅ | ❌ | ❌ | ✅ |
| Delete own project | ✅ | ❌ | ❌ | ✅ |
| Add collaborators | ✅ | ❌ | ❌ | ✅ |
| Remove collaborators | ✅ | ❌ | ❌ | ✅ |
| **Global Operations** |  |  |  |  |
| Train ML models | ✅ | ✅ | ❌ | ✅ |
| Compare any artifacts | ✅ | ✅ | ✅ | ✅ |
| Matrix analysis | ✅ | ✅ | ❌ | ✅ |
| **User Management** |  |  |  |  |
| View all users | ❌ | ❌ | ❌ | ✅ |
| Create users | ❌ | ❌ | ❌ | ✅ |
| Modify users | ❌ | ❌ | ❌ | ✅ |
| Deactivate users | ❌ | ❌ | ❌ | ✅ |

## Implementation Notes

### Frontend Implementation
When calling project-scoped APIs, the frontend should:
1. Get current user's projects: `GET /api/projects`
2. Filter UI to show only artifacts from accessible projects
3. Pass `project_id` in requests when creating/uploading artifacts

### Backend Implementation
Project-scoped endpoints should:
1. Extract `user_id` from JWT token via `g.current_user`
2. Check if user can access the requested project:
   - `db.can_access_project(project_id, user_id)`
   - OR `g.current_user['role'] == 'admin'`
3. Return `403 Forbidden` if access denied

### Database Queries
Use these helper methods:
```python
# Check access
db.can_access_project(project_id, user_id) -> bool
db.is_project_owner(project_id, user_id) -> bool
db.is_project_collaborator(project_id, user_id) -> bool

# Get user's projects
db.get_user_projects(user_id) -> List[Dict]

# Get project artifacts
db.get_project_artifacts(project_id) -> List[Dict]
```

## Examples

### Example 1: List Artifacts (Project-Scoped)
```python
@mesh_bp.route('/list', methods=['GET'])
@login_required
def list_meshes():
    db = get_database()
    user_id = g.current_user['user_id']
    role = g.current_user['role']

    if role == 'admin':
        # Admin sees all
        artifacts = db.get_all_artifacts()
    else:
        # User sees only their projects
        user_projects = db.get_user_projects(user_id)
        artifacts = []
        for project in user_projects:
            artifacts.extend(db.get_project_artifacts(project['project_id']))

    return jsonify({'status': 'success', 'artifacts': artifacts})
```

### Example 2: Train Model (Global Access)
```python
@classification_bp.route('/train', methods=['POST'])
@role_required('archaeologist')  # Only archaeologists and admins can train
def train_model():
    db = get_database()

    # Get ALL training data (no project filtering)
    training_data = db.get_training_data()

    # Train model on complete dataset
    model = train_classifier(training_data)

    return jsonify({'status': 'success', 'samples': len(training_data)})
```

### Example 3: Compare Artifacts (Global Access)
```python
@morphometric_bp.route('/compare', methods=['POST'])
@login_required
def compare_artifacts():
    data = request.get_json()
    artifact1_id = data['artifact1_id']
    artifact2_id = data['artifact2_id']

    db = get_database()

    # No project check - comparisons are global
    artifact1 = db.get_artifact(artifact1_id)
    artifact2 = db.get_artifact(artifact2_id)

    similarity = calculate_similarity(artifact1, artifact2)

    return jsonify({'status': 'success', 'similarity': similarity})
```

## Security Considerations

1. **Always validate user tokens** via `@login_required` decorator
2. **Check role permissions** via `@role_required('role')` for sensitive operations
3. **Verify project access** before returning project-specific data
4. **Log access attempts** for audit trails
5. **Never expose other users' data** in project-scoped operations
6. **Sanitize user input** to prevent SQL injection

## Migration Path

For existing code:
1. Add `project_id` parameter to artifact creation functions
2. Update queries to filter by `project_id` where appropriate
3. Add access checks to all project-scoped endpoints
4. Test with multiple users and projects
5. Document any exceptions to these rules

## Questions?

Contact: admin@brozeaxe.com
