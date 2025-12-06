"""
Cloud Storage Integration
========================

Provides unified interface for storing files on Google Drive or Dropbox.
Falls back to local storage in development.
"""

import os
import io
from pathlib import Path
from typing import Optional, BinaryIO, List
import logging

logger = logging.getLogger(__name__)


class StorageBackend:
    """Base class for storage backends."""

    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload file and return remote URL/ID."""
        raise NotImplementedError

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download file from remote to local path."""
        raise NotImplementedError

    def delete_file(self, remote_path: str) -> None:
        """Delete file from remote storage."""
        raise NotImplementedError

    def list_files(self, folder_path: str = "") -> List[dict]:
        """List files in folder."""
        raise NotImplementedError

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists."""
        raise NotImplementedError


class LocalStorage(StorageBackend):
    """Local filesystem storage (development/fallback)."""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Copy file to storage directory."""
        import shutil
        dest = self.base_path / remote_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, dest)
        return str(dest)

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Copy file from storage directory."""
        import shutil
        source = self.base_path / remote_path
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, local_path)

    def delete_file(self, remote_path: str) -> None:
        """Delete file from storage."""
        path = self.base_path / remote_path
        if path.exists():
            path.unlink()

    def list_files(self, folder_path: str = "") -> List[dict]:
        """List files in folder."""
        folder = self.base_path / folder_path
        if not folder.exists():
            return []

        return [
            {
                'name': f.name,
                'path': str(f.relative_to(self.base_path)),
                'size': f.stat().st_size,
                'modified': f.stat().st_mtime
            }
            for f in folder.rglob('*') if f.is_file()
        ]

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists."""
        return (self.base_path / remote_path).exists()


class GoogleDriveStorage(StorageBackend):
    """Google Drive storage backend."""

    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize Google Drive storage.

        Args:
            credentials_path: Path to Google Service Account credentials JSON file
        """
        try:
            from pydrive2.auth import GoogleAuth
            from pydrive2.drive import GoogleDrive
            from oauth2client.service_account import ServiceAccountCredentials

            # Define the scopes
            scopes = ['https://www.googleapis.com/auth/drive']

            # Try to load credentials
            if credentials_path and os.path.exists(credentials_path):
                # Use provided credentials file path
                credentials = ServiceAccountCredentials.from_json_keyfile_name(
                    credentials_path, scopes
                )
            else:
                # Try environment variable
                creds_json = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
                if creds_json:
                    import json
                    import tempfile

                    try:
                        # Parse JSON credentials
                        creds_dict = json.loads(creds_json)

                        # Write credentials to temp file for ServiceAccountCredentials
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                            json.dump(creds_dict, f)
                            temp_creds = f.name

                        # Load service account credentials from temp file
                        credentials = ServiceAccountCredentials.from_json_keyfile_name(
                            temp_creds, scopes
                        )

                        # Clean up temp file
                        os.unlink(temp_creds)

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in GOOGLE_DRIVE_CREDENTIALS: {e}")
                        logger.error(f"JSON starts with: {creds_json[:200]}...")
                        raise ValueError(
                            "GOOGLE_DRIVE_CREDENTIALS contains invalid JSON. "
                            "Make sure to properly escape newlines in the private_key field. "
                            f"Parse error: {str(e)}"
                        )
                else:
                    raise ValueError(
                        "No Google Drive credentials found. Set GOOGLE_DRIVE_CREDENTIALS "
                        "environment variable or provide credentials_path"
                    )

            # Create GoogleAuth instance with service account credentials
            self.gauth = GoogleAuth()
            self.gauth.credentials = credentials

            self.drive = GoogleDrive(self.gauth)
            self._folder_cache = {}

            logger.info("✅ Google Drive storage initialized with Service Account")

        except ImportError:
            raise RuntimeError(
                "PyDrive2 not installed. Install with: pip install PyDrive2"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive: {str(e)}")
            raise RuntimeError(f"Failed to initialize Google Drive: {str(e)}")

    def _get_or_create_folder(self, folder_path: str) -> str:
        """Get or create folder and return its ID."""
        if folder_path in self._folder_cache:
            return self._folder_cache[folder_path]

        # Split path into parts
        parts = folder_path.strip('/').split('/')
        parent_id = 'root'

        for part in parts:
            if not part:
                continue

            # Search for folder
            query = f"title='{part}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            file_list = self.drive.ListFile({'q': query}).GetList()

            if file_list:
                parent_id = file_list[0]['id']
            else:
                # Create folder
                folder_metadata = {
                    'title': part,
                    'parents': [{'id': parent_id}],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.drive.CreateFile(folder_metadata)
                folder.Upload()
                parent_id = folder['id']

        self._folder_cache[folder_path] = parent_id
        return parent_id

    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload file to Google Drive."""
        # Get folder and filename
        folder_path = os.path.dirname(remote_path)
        filename = os.path.basename(remote_path)

        folder_id = self._get_or_create_folder(folder_path) if folder_path else 'root'

        # Check if file already exists
        query = f"title='{filename}' and '{folder_id}' in parents and trashed=false"
        file_list = self.drive.ListFile({'q': query}).GetList()

        if file_list:
            # Update existing file
            file = file_list[0]
            file.SetContentFile(local_path)
            file.Upload()
        else:
            # Create new file
            file_metadata = {
                'title': filename,
                'parents': [{'id': folder_id}]
            }
            file = self.drive.CreateFile(file_metadata)
            file.SetContentFile(local_path)
            file.Upload()

        logger.info(f"✅ Uploaded {filename} to Google Drive")
        return file['id']

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download file from Google Drive."""
        folder_path = os.path.dirname(remote_path)
        filename = os.path.basename(remote_path)

        folder_id = self._get_or_create_folder(folder_path) if folder_path else 'root'

        # Find file
        query = f"title='{filename}' and '{folder_id}' in parents and trashed=false"
        file_list = self.drive.ListFile({'q': query}).GetList()

        if not file_list:
            raise FileNotFoundError(f"File not found: {remote_path}")

        file = file_list[0]

        # Create local directory
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        # Download
        file.GetContentFile(local_path)
        logger.info(f"✅ Downloaded {filename} from Google Drive")

    def delete_file(self, remote_path: str) -> None:
        """Delete file from Google Drive."""
        folder_path = os.path.dirname(remote_path)
        filename = os.path.basename(remote_path)

        folder_id = self._get_or_create_folder(folder_path) if folder_path else 'root'

        query = f"title='{filename}' and '{folder_id}' in parents and trashed=false"
        file_list = self.drive.ListFile({'q': query}).GetList()

        for file in file_list:
            file.Delete()

        logger.info(f"✅ Deleted {filename} from Google Drive")

    def list_files(self, folder_path: str = "") -> List[dict]:
        """List files in Google Drive folder."""
        folder_id = self._get_or_create_folder(folder_path) if folder_path else 'root'

        query = f"'{folder_id}' in parents and trashed=false"
        file_list = self.drive.ListFile({'q': query}).GetList()

        return [
            {
                'name': f['title'],
                'id': f['id'],
                'size': int(f.get('fileSize', 0)),
                'modified': f.get('modifiedDate'),
                'mimeType': f.get('mimeType')
            }
            for f in file_list
        ]

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists on Google Drive."""
        try:
            folder_path = os.path.dirname(remote_path)
            filename = os.path.basename(remote_path)

            folder_id = self._get_or_create_folder(folder_path) if folder_path else 'root'
            query = f"title='{filename}' and '{folder_id}' in parents and trashed=false"
            file_list = self.drive.ListFile({'q': query}).GetList()

            return len(file_list) > 0
        except:
            return False


class DropboxStorage(StorageBackend):
    """Dropbox storage backend."""

    def __init__(self, access_token: Optional[str] = None):
        """Initialize Dropbox storage.

        Args:
            access_token: Dropbox access token (optional if using refresh token)

        Environment variables:
            DROPBOX_ACCESS_TOKEN: Short-lived access token
            DROPBOX_REFRESH_TOKEN: Long-lived refresh token (recommended)
            DROPBOX_APP_KEY: App key for OAuth
            DROPBOX_APP_SECRET: App secret for OAuth
        """
        try:
            import dropbox

            # Try OAuth with refresh token first (recommended)
            app_key = os.getenv('DROPBOX_APP_KEY')
            app_secret = os.getenv('DROPBOX_APP_SECRET')
            refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')

            if app_key and refresh_token:
                # Use OAuth with refresh token - tokens auto-renew
                self.dbx = dropbox.Dropbox(
                    oauth2_refresh_token=refresh_token,
                    app_key=app_key,
                    app_secret=app_secret
                )
                logger.info("✅ Dropbox initialized with OAuth refresh token")
            else:
                # Fallback to access token (expires after 4 hours)
                token = access_token or os.getenv('DROPBOX_ACCESS_TOKEN')
                if not token:
                    raise ValueError(
                        "Dropbox credentials required. Set either:\n"
                        "  - DROPBOX_APP_KEY + DROPBOX_REFRESH_TOKEN (recommended)\n"
                        "  - DROPBOX_ACCESS_TOKEN (expires in 4 hours)"
                    )
                self.dbx = dropbox.Dropbox(token)
                logger.warning("⚠️ Using short-lived access token. Consider using refresh token.")

            # Test connection
            self.dbx.users_get_current_account()
            logger.info("✅ Dropbox storage initialized")

        except ImportError:
            raise RuntimeError(
                "Dropbox SDK not installed. Install with: pip install dropbox"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Dropbox: {str(e)}")

    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload file to Dropbox."""
        import dropbox

        with open(local_path, 'rb') as f:
            try:
                # Use upload_session for large files (> 150MB)
                file_size = os.path.getsize(local_path)

                if file_size > 150 * 1024 * 1024:
                    # Large file upload
                    chunk_size = 4 * 1024 * 1024  # 4MB chunks

                    session_start = self.dbx.files_upload_session_start(f.read(chunk_size))
                    cursor = dropbox.files.UploadSessionCursor(
                        session_id=session_start.session_id,
                        offset=f.tell()
                    )

                    while f.tell() < file_size:
                        if file_size - f.tell() <= chunk_size:
                            # Last chunk
                            self.dbx.files_upload_session_finish(
                                f.read(chunk_size),
                                cursor,
                                dropbox.files.CommitInfo(path=f"/{remote_path}")
                            )
                        else:
                            self.dbx.files_upload_session_append_v2(
                                f.read(chunk_size),
                                cursor
                            )
                            cursor.offset = f.tell()
                else:
                    # Small file upload
                    self.dbx.files_upload(
                        f.read(),
                        f"/{remote_path}",
                        mode=dropbox.files.WriteMode.overwrite
                    )

                logger.info(f"✅ Uploaded to Dropbox: {remote_path}")
                return remote_path

            except Exception as e:
                logger.error(f"Failed to upload to Dropbox: {str(e)}")
                raise

    def download_file(self, remote_path: str, local_path: str) -> None:
        """Download file from Dropbox."""
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        self.dbx.files_download_to_file(local_path, f"/{remote_path}")
        logger.info(f"✅ Downloaded from Dropbox: {remote_path}")

    def delete_file(self, remote_path: str) -> None:
        """Delete file from Dropbox."""
        self.dbx.files_delete_v2(f"/{remote_path}")
        logger.info(f"✅ Deleted from Dropbox: {remote_path}")

    def list_files(self, folder_path: str = "") -> List[dict]:
        """List files in Dropbox folder."""
        try:
            result = self.dbx.files_list_folder(f"/{folder_path}" if folder_path else "")

            return [
                {
                    'name': entry.name,
                    'path': entry.path_display,
                    'size': getattr(entry, 'size', 0),
                    'modified': getattr(entry, 'server_modified', None)
                }
                for entry in result.entries
            ]
        except Exception as e:
            # Folder might not exist yet - return empty list
            logger.warning(f"Could not list Dropbox folder '{folder_path}': {e}")
            return []

    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists on Dropbox."""
        try:
            self.dbx.files_get_metadata(f"/{remote_path}")
            return True
        except:
            return False


# Storage factory
def get_storage(backend: str = "local", **kwargs) -> StorageBackend:
    """Get storage backend instance.

    Args:
        backend: Storage backend type ('local', 'gdrive', 'dropbox')
        **kwargs: Backend-specific arguments

    Returns:
        Storage backend instance

    Example:
        # Local storage (development)
        storage = get_storage('local', base_path='/data')

        # Google Drive (production)
        storage = get_storage('gdrive', credentials_path='credentials.json')

        # Dropbox (production)
        storage = get_storage('dropbox', access_token='...')
    """
    backend = backend.lower()

    if backend == "local":
        return LocalStorage(**kwargs)
    elif backend in ("gdrive", "google_drive", "googledrive"):
        return GoogleDriveStorage(**kwargs)
    elif backend == "dropbox":
        return DropboxStorage(**kwargs)
    else:
        raise ValueError(f"Unknown storage backend: {backend}")


# Environment-based storage selection
def get_default_storage() -> StorageBackend:
    """Get storage backend based on environment variables.

    Environment variables:
        STORAGE_BACKEND: 'local', 'gdrive', or 'dropbox' (default: 'local')
        STORAGE_BASE_PATH: Base path for local storage
        GOOGLE_DRIVE_CREDENTIALS: Google Drive credentials JSON
        DROPBOX_ACCESS_TOKEN: Dropbox access token
    """
    backend = os.getenv('STORAGE_BACKEND', 'local')

    if backend == 'local':
        base_path = os.getenv('STORAGE_BASE_PATH', '/data')
        return LocalStorage(base_path=base_path)

    elif backend == 'gdrive':
        creds_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH')
        return GoogleDriveStorage(credentials_path=creds_path)

    elif backend == 'dropbox':
        return DropboxStorage()

    else:
        logger.warning(f"Unknown backend '{backend}', falling back to local storage")
        return LocalStorage()
