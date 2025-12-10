# Google Drive Configuration for Railway

## Overview

This guide shows how to configure Google Drive storage on Railway for persistent file storage.

## Prerequisites

1. Railway account with deployed application
2. Google Cloud Project with Drive API enabled
3. Service Account credentials JSON file

## Step 1: Create Google Cloud Service Account

### 1.1 Create Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **IAM & Admin** > **Service Accounts**
4. Click **Create Service Account**
   - Name: `brozeaxe-railway-storage`
   - Description: `Service account for Railway persistent storage`
   - Click **Create and Continue**
5. Grant role: **None** (we'll use Google Drive permissions)
6. Click **Done**

### 1.2 Create Service Account Key
1. Click on the created service account
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Click **Create**
6. Save the downloaded JSON file securely

### 1.3 Enable Google Drive API
1. Go to **APIs & Services** > **Library**
2. Search for "Google Drive API"
3. Click **Enable**

## Step 2: Create Google Drive Folder

### 2.1 Create Application Folder
1. Go to [Google Drive](https://drive.google.com/)
2. Create a new folder: `BrozeAXE-Railway`
3. Inside it, create subfolders:
   ```
   BrozeAXE-Railway/
   ├── artifacts/
   ├── database/
   └── uploads/
   ```

### 2.2 Share with Service Account
1. Right-click on `BrozeAXE-Railway` folder
2. Click **Share**
3. Paste the service account email from the JSON file:
   - Format: `brozeaxe-railway-storage@YOUR-PROJECT.iam.gserviceaccount.com`
4. Set permission to **Editor**
5. Uncheck "Notify people"
6. Click **Share**

## Step 3: Configure Railway Environment Variables

### 3.1 Prepare Service Account JSON

Convert the multi-line JSON to a single-line string:

```bash
# On Linux/Mac:
cat service-account-key.json | jq -c . | pbcopy

# On Windows PowerShell:
Get-Content service-account-key.json | ConvertFrom-Json | ConvertTo-Json -Compress | Set-Clipboard
```

Or manually remove all newlines and extra spaces.

### 3.2 Add Variables to Railway

Go to Railway Dashboard → Your Project → **Variables** tab and add:

#### Required Variables:

```bash
# Storage Backend
STORAGE_BACKEND=gdrive

# Google Drive Credentials (single-line JSON)
GOOGLE_DRIVE_CREDENTIALS={"type":"service_account","project_id":"...","private_key":"..."}

# Google Drive Folder Paths
GDRIVE_FOLDER_ARTIFACTS=BrozeAXE-Railway/artifacts
GDRIVE_FOLDER_DATABASE=BrozeAXE-Railway/database
GDRIVE_FOLDER_UPLOADS=BrozeAXE-Railway/uploads

# Google Drive Root Folder ID (optional, for faster access)
GDRIVE_ROOT_FOLDER_ID=<folder_id_from_drive_url>
```

To get folder ID:
1. Open `BrozeAXE-Railway` folder in Drive
2. URL will be: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
3. Copy the `FOLDER_ID_HERE` part

#### Flask & Database Variables:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5001
HOST=0.0.0.0

# JWT Secret Key (GENERATE A SECURE ONE!)
JWT_SECRET_KEY=<use: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Database (will be synced to Google Drive)
DATABASE_PATH=/tmp/acs_artifacts.db

# File Upload Configuration
MAX_UPLOAD_SIZE=104857600
UPLOAD_FOLDER=/tmp/uploads
```

### 3.3 Alternative: Use OAuth2 (Not Recommended for Production)

If you prefer OAuth2 instead of Service Account:

```bash
# Storage Backend
STORAGE_BACKEND=gdrive

# OAuth2 Credentials
GDRIVE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=your-client-secret

# Note: OAuth2 requires user interaction for initial token
# Service Account is recommended for Railway
```

## Step 4: Verify Setup

### 4.1 Check Railway Logs

After redeployment, check logs for:

```
✅ Google Drive storage initialized
✅ Connected to folder: BrozeAXE-Railway
```

### 4.2 Test Upload

1. Login to your Railway app
2. Upload a test artifact
3. Check Google Drive folder - file should appear in `BrozeAXE-Railway/uploads/`

### 4.3 Test Database Persistence

1. Create a project in the app
2. Redeploy Railway (or restart container)
3. Project should still be there (database synced from Drive)

## Step 5: Automatic Database Sync

The application automatically:
- **On Startup:** Downloads database from Google Drive to `/tmp/acs_artifacts.db`
- **On Changes:** Uploads updated database back to Google Drive
- **On Shutdown:** Final sync to Google Drive

## Troubleshooting

### Error: "Could not authenticate with Google Drive"

**Solution:**
- Verify `GOOGLE_DRIVE_CREDENTIALS` is valid single-line JSON
- Check service account has Editor access to folder
- Ensure Google Drive API is enabled in Google Cloud

### Error: "Folder not found"

**Solution:**
- Verify folder names match exactly (case-sensitive)
- Check service account email has access to folder
- Try using folder ID instead of path:
  ```bash
  GDRIVE_ROOT_FOLDER_ID=folder_id_here
  ```

### Error: "Quota exceeded"

**Solution:**
- Google Drive free tier: 15GB total storage
- Check current usage: [drive.google.com/settings/storage](https://drive.google.com/settings/storage)
- Consider upgrading to Google Workspace if needed

### Slow Performance

**Solution:**
- Use folder IDs instead of paths (faster lookups)
- Enable caching in application
- Consider using Google Cloud Storage for better performance

## Security Best Practices

1. **Never commit service account JSON to git**
   - Add to `.gitignore`:
     ```
     service-account-key.json
     *credentials*.json
     ```

2. **Rotate service account keys regularly**
   - Create new key
   - Update Railway variable
   - Delete old key from Google Cloud

3. **Limit service account permissions**
   - Only grant Editor access to specific folder
   - Don't use full Google Drive access

4. **Monitor API usage**
   - Go to Google Cloud Console > APIs & Services > Dashboard
   - Check Drive API quota usage
   - Set up alerts for quota thresholds

5. **Backup strategy**
   - Google Drive has built-in versioning
   - Enable "Keep forever" for database folder
   - Consider periodic exports to local storage

## Cost Estimate

- **Google Drive API:** Free (1 billion requests/day limit)
- **Storage:**
  - Free tier: 15GB
  - Google One Basic: 100GB for $1.99/month
  - Google Workspace: 30GB/user from $6/month

## Alternative: Local Storage Only

If you prefer not to use Google Drive, set:

```bash
STORAGE_BACKEND=local
DATABASE_PATH=/data/acs_artifacts.db
UPLOAD_FOLDER=/data/uploads
```

**Note:** Railway containers have ephemeral filesystems. Data will be lost on redeployment unless using Railway Volumes (not available in free tier).

## Next Steps

1. ✅ Service account created
2. ✅ Google Drive folders set up
3. ✅ Railway variables configured
4. ✅ Application deployed
5. ✅ Upload test passed
6. ✅ Database persists across restarts

**Your application is now ready for production use with persistent cloud storage!**

## Support

Questions? Check:
- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [PyDrive2 Documentation](https://docs.iterative.ai/PyDrive2/)
- Project issues: [GitHub Issues](https://github.com/enzococca/BrozeAXE-AI/issues)
