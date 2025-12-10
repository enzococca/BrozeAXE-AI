# Web Login Interface - Testing Guide

## ✅ Implementation Complete

A complete web-based authentication interface has been added to BrozeAXE-AI!

## 🎯 What Was Added

### 1. **Login Page** (`/web/login`)
- Beautiful gradient design with logo
- Username/password form
- Pre-filled with default credentials (admin/admin123)
- Loading spinner during authentication
- Error and success alerts
- Auto-redirect if already logged in
- Responsive design

### 2. **Dashboard Page** (`/web/dashboard`)
- Welcome section with user info
- Real-time statistics (artifacts, classifications, training samples)
- Role-based quick actions
- Logout button
- Security warning for default password
- Modern card-based layout

### 3. **Global Auth Helper** (`auth.js`)
- Automatic token management
- Role checking utilities
- Token verification
- Authenticated fetch wrapper
- Auto-logout on token expiry
- Adds logout button to navbar on all pages
- Displays user info in navbar

## 🧪 How to Test

### Step 1: Start the Server

```bash
cd /home/user/BrozeAXE-AI/archaeological-classifier
python -m acs.api.app
```

You should see:
```
[Auth] ⚠️  Default admin created:
[Auth]     Username: admin
[Auth]     Password: admin123
[Auth]     ⚠️  CHANGE PASSWORD IMMEDIATELY!
 * Running on http://127.0.0.1:5000
```

### Step 2: Open Browser

Visit: **http://localhost:5000**

### Step 3: Test Login Flow

1. **Auto-Redirect:**
   - You'll be redirected from `/` → `/web/dashboard`
   - Dashboard will redirect to `/web/login` (not authenticated)

2. **Login Page:**
   - Form is pre-filled with admin/admin123
   - Click "Sign In"
   - Loading spinner appears
   - Success message: "Login successful! Redirecting..."

3. **Dashboard:**
   - Welcome message: "Welcome back, Admin!"
   - User info shows: username, email, role badge
   - Statistics cards show counts
   - Quick actions grid shows role-specific options

4. **Logout:**
   - Click "Logout" button in welcome section
   - Confirms with popup
   - Redirects to login page
   - Token cleared from localStorage

### Step 4: Test Role-Based Access

#### Create Different Users (via API)

```bash
# Register Archaeologist
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "archaeologist1",
    "email": "arch@example.com",
    "password": "test123",
    "role": "archaeologist",
    "full_name": "Test Archaeologist"
  }'

# Register Viewer
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "viewer1",
    "email": "viewer@example.com",
    "password": "test123",
    "role": "viewer",
    "full_name": "Test Viewer"
  }'
```

#### Login as Different Roles

**Admin** sees all actions:
- Upload Artifact
- Savignano Analysis
- Morphometric Analysis
- 3D Viewer
- View Artifacts
- Projects
- Technical Drawings
- Taxonomy
- AI Assistant
- **User Management** (admin only)

**Archaeologist** sees:
- Upload Artifact
- Savignano Analysis
- Morphometric Analysis
- 3D Viewer
- View Artifacts
- Projects
- Technical Drawings
- Taxonomy
- AI Assistant

**Viewer** sees:
- Morphometric Analysis (read-only)
- 3D Viewer
- View Artifacts
- Projects
- Taxonomy
- AI Assistant

### Step 5: Test Token Persistence

1. Login successfully
2. Close browser tab
3. Open new tab to http://localhost:5000
4. You should still be logged in (dashboard loads directly)
5. Token persists in localStorage

### Step 6: Test Token Expiration

Tokens expire after 24 hours. To test:

1. Login
2. In browser console: `localStorage.getItem('token')`
3. Manually set an expired token (or wait 24 hours)
4. Reload page
5. Should auto-redirect to login

### Step 7: Test Protected Endpoints

**Without Token (401):**
```bash
curl http://localhost:5000/api/mesh/upload
# Response: {"error": "Authentication required", "code": "NO_TOKEN"}
```

**With Token:**
```bash
# Get token from login response
TOKEN="eyJ..."

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/auth/me
# Response: {"status": "success", "user": {...}}
```

**Wrong Role (403):**
```bash
# Login as viewer, try admin endpoint
curl -X POST http://localhost:5000/api/mesh/export \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format":"json"}'
# Response: {"error": "Access denied...", "code": "INSUFFICIENT_PERMISSIONS"}
```

## 📸 Screenshots to Verify

### Login Page
- [ ] Gradient purple background
- [ ] Logo (🏛️) and app name
- [ ] Yellow box with default credentials
- [ ] Username and password fields pre-filled
- [ ] "Sign In" button
- [ ] "OR" divider
- [ ] "Contact administrator" text

### Dashboard
- [ ] Purple gradient welcome section
- [ ] User name and email displayed
- [ ] Role badge (admin/archaeologist/viewer)
- [ ] Logout button (red)
- [ ] 4 statistics cards with icons
- [ ] Quick actions grid with cards
- [ ] Each action card has icon, title, description
- [ ] Hover effects on cards

### Navbar (After Login)
- [ ] User info displayed next to logo
- [ ] Username shown
- [ ] Role badge shown
- [ ] Logout button in navbar (red)

## 🔒 Security Features

1. **JWT Tokens:**
   - Secure token-based authentication
   - 24-hour expiration
   - Stored in localStorage (client-side)
   - Automatically cleared on logout/expiry

2. **Role-Based Access:**
   - UI hides actions user doesn't have permission for
   - API enforces permissions server-side
   - 403 error if trying to access unauthorized endpoint

3. **Auto-Verification:**
   - Token verified on each page load
   - Invalid/expired tokens auto-cleared
   - User redirected to login

4. **Password Hashing:**
   - Passwords never stored in plaintext
   - Bcrypt hashing with salt
   - Server-side validation

## 🐛 Troubleshooting

### "Cannot GET /web/login"
**Problem:** Server not running
**Solution:** Start server with `python -m acs.api.app`

### Login Button Doesn't Work
**Problem:** JavaScript not loading
**Solution:** Check browser console for errors

### Dashboard Shows 0 for All Stats
**Problem:** No data in database yet
**Solution:** Normal for fresh installation. Upload artifacts to see numbers increase.

### Logout Button Doesn't Appear
**Problem:** auth.js not loaded
**Solution:** Hard refresh browser (Ctrl+Shift+R)

### Token Not Persisting
**Problem:** Browser blocking localStorage
**Solution:** Check browser privacy settings

### CORS Error in Console
**Problem:** Browser blocking cross-origin requests
**Solution:** CORS already configured for localhost:5000

## 📊 Test Checklist

- [ ] Server starts without errors
- [ ] Can access http://localhost:5000
- [ ] Redirects to /web/dashboard
- [ ] Dashboard redirects to /web/login
- [ ] Login form is visible
- [ ] Can login with admin/admin123
- [ ] Redirects to dashboard after login
- [ ] Welcome message shows correct username
- [ ] Statistics load (may be 0)
- [ ] Quick actions show correct items for role
- [ ] Logout button works
- [ ] After logout, redirects to login
- [ ] Can login again successfully
- [ ] Token persists across page reloads
- [ ] Browser console shows no errors

## 🎉 Success Criteria

If all of the above works, the web authentication interface is functioning correctly!

## 📝 Next Steps

After testing:

1. **Change Default Password**
   ```bash
   curl -X POST http://localhost:5000/api/auth/change-password \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"current_password":"admin123","new_password":"SecurePass123!"}'
   ```

2. **Create Real Users**
   - Use registration endpoint or future User Management page

3. **Start Using the System**
   - Upload artifacts via Upload page
   - Run Savignano analysis
   - Generate reports
   - All protected with authentication!

## 🚀 What's Next

From WORKFLOW_TODO.md - Quick Wins (Priority B):

1. ✅ Authentication System (DONE)
2. ⏭️ File Size Validation (30 min)
3. ⏭️ Add Pagination (1 hour)
4. ⏭️ Health Endpoint (15 min)
5. ⏭️ Artifact Delete Endpoint (1 hour)
6. ⏭️ Batch Classification (2 hours)

Ready to continue? 🎯
