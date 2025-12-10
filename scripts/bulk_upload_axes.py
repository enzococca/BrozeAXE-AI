#!/usr/bin/env python3
"""
Bulk Upload Script for Bronze Age Axes
Scans a directory recursively for OBJ files with MTL and textures,
then uploads them to the BronzeAXE-AI web application.

Usage:
    python bulk_upload_axes.py /Volumes/extesione4T/3dasce

Requirements:
    pip install requests
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from typing import Optional, List, Tuple
import time

# Configuration
DEFAULT_SERVER_URL = "https://bronzeaxe-ai.up.railway.app"
SUPPORTED_OBJ_EXTENSIONS = ['.obj']
SUPPORTED_MTL_EXTENSIONS = ['.mtl']
SUPPORTED_TEXTURE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tga', '.bmp']


def find_associated_files(obj_path: Path) -> Tuple[Optional[Path], List[Path]]:
    """
    Find MTL and texture files associated with an OBJ file.

    Searches in the same directory for:
    - MTL file with same base name or any MTL in the directory
    - Texture files referenced or with similar names

    Returns:
        Tuple of (mtl_path, list_of_texture_paths)
    """
    obj_dir = obj_path.parent
    obj_stem = obj_path.stem  # filename without extension

    mtl_file = None
    texture_files = []

    # Look for MTL file
    # First try exact match
    exact_mtl = obj_dir / f"{obj_stem}.mtl"
    if exact_mtl.exists():
        mtl_file = exact_mtl
    else:
        # Look for any MTL in the directory
        mtl_files = list(obj_dir.glob("*.mtl"))
        if mtl_files:
            mtl_file = mtl_files[0]

    # Look for texture files
    for ext in SUPPORTED_TEXTURE_EXTENSIONS:
        # Exact match
        exact_tex = obj_dir / f"{obj_stem}{ext}"
        if exact_tex.exists():
            texture_files.append(exact_tex)

        # Also check for common texture naming patterns
        for pattern in [f"{obj_stem}_*{ext}", f"{obj_stem}.*{ext}", f"*{ext}"]:
            for tex in obj_dir.glob(pattern):
                if tex not in texture_files:
                    texture_files.append(tex)

    # If we have MTL, parse it to find referenced textures
    if mtl_file:
        try:
            mtl_content = mtl_file.read_text(encoding='utf-8', errors='ignore')
            for line in mtl_content.split('\n'):
                line = line.strip()
                if line.startswith('map_') or line.startswith('bump') or line.startswith('disp'):
                    parts = line.split()
                    if len(parts) >= 2:
                        tex_name = parts[-1]
                        tex_path = obj_dir / tex_name
                        if tex_path.exists() and tex_path not in texture_files:
                            texture_files.append(tex_path)
        except Exception as e:
            print(f"    Warning: Could not parse MTL file: {e}")

    return mtl_file, texture_files


def scan_directory(base_dir: str) -> List[dict]:
    """
    Recursively scan directory for OBJ files and their associated files.

    Returns:
        List of dicts with 'obj', 'mtl', 'textures' keys
    """
    base_path = Path(base_dir)
    results = []

    print(f"\n{'='*60}")
    print(f"Scanning: {base_path}")
    print(f"{'='*60}\n")

    # Find all OBJ files recursively
    obj_files = list(base_path.rglob("*.obj"))

    print(f"Found {len(obj_files)} OBJ files\n")

    for obj_path in sorted(obj_files):
        mtl_file, texture_files = find_associated_files(obj_path)

        result = {
            'obj': obj_path,
            'mtl': mtl_file,
            'textures': texture_files,
            'name': obj_path.stem,
            'folder': obj_path.parent.name
        }
        results.append(result)

        # Print info
        print(f"  {obj_path.stem}")
        print(f"    OBJ: {obj_path.name}")
        if mtl_file:
            print(f"    MTL: {mtl_file.name}")
        if texture_files:
            print(f"    Textures: {', '.join(t.name for t in texture_files)}")
        print()

    return results


def upload_artifact(server_url: str, artifact: dict, mesh_units: str = 'mm') -> dict:
    """
    Upload a single artifact (OBJ + MTL + textures) to the server.

    Returns:
        Response dict with status
    """
    upload_url = f"{server_url}/web/upload"

    # Prepare files
    files = {}

    # OBJ file (required)
    obj_path = artifact['obj']
    files['file'] = (obj_path.name, open(obj_path, 'rb'), 'application/octet-stream')

    # MTL file (optional)
    if artifact['mtl']:
        files['mtl_file'] = (artifact['mtl'].name, open(artifact['mtl'], 'rb'), 'text/plain')

    # Texture files (optional, can be multiple)
    texture_handles = []
    for i, tex_path in enumerate(artifact['textures']):
        # Determine mime type
        ext = tex_path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tga': 'image/x-tga',
            '.bmp': 'image/bmp'
        }
        mime = mime_types.get(ext, 'application/octet-stream')

        handle = open(tex_path, 'rb')
        texture_handles.append(handle)
        files[f'texture_files'] = (tex_path.name, handle, mime)

    # Form data
    data = {
        'mesh_units': mesh_units,
        'category': 'axe',
        'material': 'bronze',
        'description': f'Bronze Age axe from {artifact["folder"]}'
    }

    try:
        response = requests.post(upload_url, files=files, data=data, timeout=300)
        result = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'raw': response.text}
        result['http_status'] = response.status_code
        return result
    except requests.exceptions.Timeout:
        return {'error': 'Upload timeout (file too large?)', 'http_status': 408}
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'http_status': 0}
    finally:
        # Close all file handles
        for key, value in files.items():
            if hasattr(value[1], 'close'):
                value[1].close()
        for handle in texture_handles:
            handle.close()


def bulk_upload(base_dir: str, server_url: str, mesh_units: str = 'mm', dry_run: bool = False):
    """
    Scan directory and upload all artifacts.
    """
    # Scan for files
    artifacts = scan_directory(base_dir)

    if not artifacts:
        print("No OBJ files found!")
        return

    print(f"\n{'='*60}")
    print(f"Summary: {len(artifacts)} artifacts to upload")
    print(f"Server: {server_url}")
    print(f"Mesh units: {mesh_units}")
    print(f"{'='*60}\n")

    if dry_run:
        print("DRY RUN - No files will be uploaded")
        return

    # Confirm
    confirm = input("Proceed with upload? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return

    # Upload each artifact
    success_count = 0
    error_count = 0
    results = []

    for i, artifact in enumerate(artifacts, 1):
        print(f"\n[{i}/{len(artifacts)}] Uploading {artifact['name']}...")

        start_time = time.time()
        result = upload_artifact(server_url, artifact, mesh_units)
        elapsed = time.time() - start_time

        result['artifact_name'] = artifact['name']
        result['elapsed_seconds'] = elapsed
        results.append(result)

        if result.get('status') == 'success':
            success_count += 1
            artifact_id = result.get('artifact_id', 'unknown')
            print(f"    ✅ Success! ID: {artifact_id} ({elapsed:.1f}s)")
        else:
            error_count += 1
            error_msg = result.get('error', result.get('raw', 'Unknown error'))
            print(f"    ❌ Error: {error_msg}")

        # Small delay between uploads to avoid overwhelming the server
        time.sleep(1)

    # Final summary
    print(f"\n{'='*60}")
    print(f"UPLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"  Success: {success_count}")
    print(f"  Errors:  {error_count}")
    print(f"  Total:   {len(artifacts)}")

    if error_count > 0:
        print(f"\nFailed uploads:")
        for r in results:
            if r.get('status') != 'success':
                print(f"  - {r['artifact_name']}: {r.get('error', 'Unknown error')}")


def main():
    parser = argparse.ArgumentParser(
        description='Bulk upload OBJ files with textures to BronzeAXE-AI'
    )
    parser.add_argument(
        'directory',
        help='Directory to scan for OBJ files (recursive)'
    )
    parser.add_argument(
        '--server', '-s',
        default=DEFAULT_SERVER_URL,
        help=f'Server URL (default: {DEFAULT_SERVER_URL})'
    )
    parser.add_argument(
        '--units', '-u',
        default='mm',
        choices=['mm', 'cm', 'm', 'in'],
        help='Mesh units (default: mm)'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Scan only, do not upload'
    )

    args = parser.parse_args()

    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: Directory not found: {args.directory}")
        sys.exit(1)

    # Run bulk upload
    bulk_upload(
        base_dir=args.directory,
        server_url=args.server,
        mesh_units=args.units,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    main()
