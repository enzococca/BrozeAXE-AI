"""
Drawing Worker Module
=====================

Handles technical drawing generation in a separate process to avoid
matplotlib threading issues on macOS.
"""

import os
import sys


def generate_drawing_worker(mesh_data, artifact_id, features, view_type='complete_sheet'):
    """
    Worker function that runs in a separate process.

    Args:
        mesh_data: Serialized mesh data
        artifact_id: Artifact identifier
        features: Feature dictionary
        view_type: Type of view to generate

    Returns:
        Tuple of (success: bool, data: bytes or error_message: str)
    """
    try:
        # Import here to avoid loading in main process
        import pickle
        import trimesh
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')  # Must be set before importing pyplot

        from acs.core.technical_drawing import TechnicalDrawingGenerator

        # Deserialize mesh
        mesh = pickle.loads(mesh_data)

        # Generate drawing
        drawer = TechnicalDrawingGenerator()

        if view_type == 'complete_sheet':
            views = drawer.generate_complete_drawing(mesh, artifact_id, features)
            return (True, views['complete_sheet'])
        else:
            views = drawer.generate_complete_drawing(mesh, artifact_id, features)
            if view_type in views:
                return (True, views[view_type])
            else:
                return (False, f"Invalid view type: {view_type}")

    except Exception as e:
        import traceback
        return (False, f"Drawing generation failed: {str(e)}\n{traceback.format_exc()}")


def generate_drawing_safe(mesh, artifact_id, features, view_type='complete_sheet', timeout=30):
    """
    Generate technical drawing in a safe way using multiprocessing.

    This avoids matplotlib threading issues on macOS by running
    the drawing generation in a completely separate process.

    Args:
        mesh: Trimesh object
        artifact_id: Artifact identifier
        features: Feature dictionary
        view_type: Type of view to generate
        timeout: Timeout in seconds

    Returns:
        bytes: Image data on success

    Raises:
        Exception: On generation failure
    """
    import pickle
    from multiprocessing import Pool

    # Serialize mesh for IPC
    try:
        mesh_data = pickle.dumps(mesh)
    except Exception as e:
        raise Exception(f"Failed to serialize mesh: {str(e)}")

    # Create a pool with a single worker
    # Note: We use 'spawn' context to ensure clean process on macOS
    import multiprocessing
    ctx = multiprocessing.get_context('spawn')

    with ctx.Pool(processes=1) as pool:
        # Submit job
        result = pool.apply_async(
            generate_drawing_worker,
            args=(mesh_data, artifact_id, features, view_type)
        )

        try:
            # Wait for result with timeout
            success, data = result.get(timeout=timeout)

            if success:
                return data
            else:
                raise Exception(data)

        except multiprocessing.TimeoutError:
            pool.terminate()
            pool.join()
            raise Exception(f"Drawing generation timed out after {timeout} seconds")
        except Exception as e:
            pool.terminate()
            pool.join()
            raise
