"""
File Upload Validator
=====================

Secure file upload validation for mesh files.
Protects against:
- Oversized files (DoS)
- Invalid file types
- Path traversal attacks
- Corrupted meshes
"""

import os
import re
from typing import Tuple, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import trimesh


class FileValidationError(Exception):
    """Custom exception for file validation errors."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class FileValidator:
    """
    Validates uploaded 3D mesh files for security and integrity.

    Size Limits:
    - Web upload: 100 MB per file
    - API upload: 500 MB per file
    - Batch upload: 2 GB total
    """

    # Size limits in bytes
    MAX_SIZE_WEB = 100 * 1024 * 1024  # 100 MB
    MAX_SIZE_API = 500 * 1024 * 1024  # 500 MB
    MAX_SIZE_BATCH = 2 * 1024 * 1024 * 1024  # 2 GB

    # Allowed file extensions and MIME types
    ALLOWED_EXTENSIONS = {'.obj', '.stl', '.ply', '.off', '.gltf', '.glb'}
    ALLOWED_MIME_TYPES = {
        'text/plain',  # OBJ files
        'application/octet-stream',  # STL, PLY
        'model/obj',
        'model/stl',
        'model/ply',
        'model/gltf+json',
        'model/gltf-binary'
    }

    # Magic bytes for common 3D formats
    MAGIC_BYTES = {
        b'solid ': 'stl_ascii',
        b'\x80\x00\x00\x00': 'stl_binary',
        b'ply\n': 'ply_ascii',
        b'ply\r\n': 'ply_ascii',
        b'OFF\n': 'off',
        b'# ': 'obj',
        b'v ': 'obj',
        b'glTF': 'gltf'
    }

    @staticmethod
    def validate_file_size(file: FileStorage, max_size: int) -> None:
        """
        Validate file size doesn't exceed limit.

        Args:
            file: The uploaded file
            max_size: Maximum allowed size in bytes

        Raises:
            FileValidationError: If file is too large
        """
        # Get file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning

        if size > max_size:
            size_mb = size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            raise FileValidationError(
                f"File too large: {size_mb:.2f} MB (max: {max_mb:.0f} MB)",
                error_code="FILE_TOO_LARGE"
            )

    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Sanitize and validate filename.

        Args:
            filename: Original filename

        Returns:
            Safe filename

        Raises:
            FileValidationError: If filename is invalid
        """
        if not filename:
            raise FileValidationError(
                "No filename provided",
                error_code="NO_FILENAME"
            )

        # Sanitize filename (removes path traversal attempts)
        safe_filename = secure_filename(filename)

        if not safe_filename:
            raise FileValidationError(
                "Invalid filename",
                error_code="INVALID_FILENAME"
            )

        # Check extension
        ext = os.path.splitext(safe_filename)[1].lower()
        if ext not in FileValidator.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"Invalid file extension: {ext}. Allowed: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}",
                error_code="INVALID_EXTENSION"
            )

        return safe_filename

    @staticmethod
    def validate_magic_bytes(file: FileStorage) -> str:
        """
        Validate file type by checking magic bytes.

        Args:
            file: The uploaded file

        Returns:
            Detected file type

        Raises:
            FileValidationError: If magic bytes don't match expected format
        """
        # Read first 1024 bytes
        header = file.read(1024)
        file.seek(0)  # Reset

        # Check magic bytes
        detected_type = None
        for magic, file_type in FileValidator.MAGIC_BYTES.items():
            if header.startswith(magic):
                detected_type = file_type
                break

        # OBJ files might not start with # or v (could have comments/blanks)
        if not detected_type and b'v ' in header[:500]:
            detected_type = 'obj'

        if not detected_type:
            # Try to decode as text to check if it looks like OBJ/PLY
            try:
                text = header.decode('utf-8', errors='ignore')
                if any(keyword in text for keyword in ['vertex', 'face', 'element']):
                    detected_type = 'ascii_mesh'
            except:
                pass

        if not detected_type:
            raise FileValidationError(
                "Unrecognized file format (magic bytes check failed)",
                error_code="INVALID_MAGIC_BYTES"
            )

        return detected_type

    @staticmethod
    def validate_mesh_integrity(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate mesh can be loaded and is valid.

        Args:
            file_path: Path to the mesh file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to load mesh with trimesh
            mesh = trimesh.load(file_path)

            # Check if mesh is empty
            if isinstance(mesh, trimesh.Scene):
                # Handle scenes (multiple meshes)
                if len(mesh.geometry) == 0:
                    return False, "Mesh file is empty (no geometry)"

                # Check first geometry
                first_geom = list(mesh.geometry.values())[0]
                if not hasattr(first_geom, 'vertices') or len(first_geom.vertices) == 0:
                    return False, "Mesh has no vertices"
            else:
                # Single mesh
                if not hasattr(mesh, 'vertices') or len(mesh.vertices) == 0:
                    return False, "Mesh has no vertices"

                if not hasattr(mesh, 'faces') or len(mesh.faces) == 0:
                    return False, "Mesh has no faces"

            return True, None

        except Exception as e:
            return False, f"Failed to load mesh: {str(e)}"

    @staticmethod
    def validate_upload(
        file: FileStorage,
        max_size: int = MAX_SIZE_WEB,
        check_integrity: bool = True,
        save_path: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Perform complete file validation.

        Args:
            file: The uploaded file
            max_size: Maximum file size in bytes
            check_integrity: Whether to validate mesh integrity
            save_path: Path to save file for integrity check (if None, uses temp)

        Returns:
            Tuple of (safe_filename, detected_type)

        Raises:
            FileValidationError: If any validation fails
        """
        # 1. Validate filename
        safe_filename = FileValidator.validate_filename(file.filename)

        # 2. Validate file size
        FileValidator.validate_file_size(file, max_size)

        # 3. Validate magic bytes
        detected_type = FileValidator.validate_magic_bytes(file)

        # 4. Validate mesh integrity (optional)
        if check_integrity:
            # Save to temp location for validation
            import tempfile

            if save_path is None:
                # Create temp file
                fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(safe_filename)[1])
                os.close(fd)
            else:
                temp_path = save_path

            try:
                # Save file
                file.save(temp_path)
                file.seek(0)  # Reset for potential re-use

                # Validate mesh
                is_valid, error_msg = FileValidator.validate_mesh_integrity(temp_path)

                if not is_valid:
                    raise FileValidationError(
                        error_msg,
                        error_code="INVALID_MESH"
                    )

            finally:
                # Clean up temp file if we created it
                if save_path is None and os.path.exists(temp_path):
                    os.remove(temp_path)

        return safe_filename, detected_type

    @staticmethod
    def validate_batch_upload(files: list, max_total_size: int = MAX_SIZE_BATCH) -> None:
        """
        Validate batch upload doesn't exceed total size limit.

        Args:
            files: List of FileStorage objects
            max_total_size: Maximum total size in bytes

        Raises:
            FileValidationError: If total size exceeds limit
        """
        total_size = 0

        for file in files:
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            total_size += size

        if total_size > max_total_size:
            total_mb = total_size / (1024 * 1024)
            max_mb = max_total_size / (1024 * 1024)
            raise FileValidationError(
                f"Batch upload too large: {total_mb:.2f} MB (max: {max_mb:.0f} MB)",
                error_code="BATCH_TOO_LARGE"
            )


# Rate limiting helper (simple in-memory implementation)
class RateLimiter:
    """
    Simple in-memory rate limiter for upload endpoints.

    Note: In production, use Redis for distributed rate limiting.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {user_id: [(timestamp, count), ...]}

    def is_allowed(self, user_id: str) -> bool:
        """
        Check if user is allowed to make a request.

        Args:
            user_id: User identifier

        Returns:
            True if allowed, False if rate limited
        """
        import time

        now = time.time()
        cutoff = now - self.window_seconds

        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                (ts, count) for ts, count in self.requests[user_id]
                if ts > cutoff
            ]
        else:
            self.requests[user_id] = []

        # Count requests in window
        total_requests = sum(count for _, count in self.requests[user_id])

        if total_requests >= self.max_requests:
            return False

        # Add new request
        self.requests[user_id].append((now, 1))
        return True

    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests for user."""
        import time

        now = time.time()
        cutoff = now - self.window_seconds

        if user_id not in self.requests:
            return self.max_requests

        # Count requests in window
        total_requests = sum(
            count for ts, count in self.requests[user_id]
            if ts > cutoff
        )

        return max(0, self.max_requests - total_requests)


# Global rate limiter instance
upload_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
