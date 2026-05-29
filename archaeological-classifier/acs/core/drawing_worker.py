"""
Drawing Worker Module
=====================

Handles technical drawing generation in a separate process to avoid
matplotlib threading issues on macOS.
"""

import os
import sys
import platform


def generate_drawing_worker(mesh_data, artifact_id, features, view_type='complete_sheet',
                            output_format='png'):
    """
    Worker function that runs in a separate process.

    Args:
        mesh_data: Serialized mesh data
        artifact_id: Artifact identifier
        features: Feature dictionary
        view_type: Type of view to generate
        output_format: 'png' or 'svg'

    Returns:
        Tuple of (success: bool, data: bytes or error_message: str)
    """
    try:
        import pickle
        import trimesh
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')

        from acs.core.technical_drawing import TechnicalDrawingGenerator

        mesh = pickle.loads(mesh_data)
        drawer = TechnicalDrawingGenerator()

        views = drawer.generate_complete_drawing(
            mesh, artifact_id, features, output_format=output_format
        )

        if view_type in views:
            return (True, views[view_type])
        else:
            return (False, f"Invalid view type: {view_type}")

    except Exception as e:
        import traceback
        return (False, f"Drawing generation failed: {str(e)}\n{traceback.format_exc()}")


def generate_drawing_safe(mesh, artifact_id, features, view_type='complete_sheet',
                          timeout=120, output_format='png'):
    """
    Generate technical drawing in a safe way using multiprocessing.

    Uses 'spawn' on macOS (avoids matplotlib threading crashes) and
    'fork' on Linux (much faster, no full interpreter restart).

    Args:
        mesh: Trimesh object
        artifact_id: Artifact identifier
        features: Feature dictionary
        view_type: Type of view to generate
        timeout: Timeout in seconds
        output_format: 'png' or 'svg'

    Returns:
        bytes: Image data on success

    Raises:
        Exception: On generation failure
    """
    import pickle
    import multiprocessing

    try:
        mesh_data = pickle.dumps(mesh)
    except Exception as e:
        raise Exception(f"Failed to serialize mesh: {str(e)}")

    start_method = 'spawn' if platform.system() == 'Darwin' else 'fork'
    ctx = multiprocessing.get_context(start_method)

    with ctx.Pool(processes=1) as pool:
        result = pool.apply_async(
            generate_drawing_worker,
            args=(mesh_data, artifact_id, features, view_type, output_format)
        )

        try:
            success, data = result.get(timeout=timeout)

            if success:
                return data
            else:
                raise Exception(data)

        except multiprocessing.TimeoutError:
            pool.terminate()
            pool.join()
            raise Exception(f"Drawing generation timed out after {timeout} seconds")
        except Exception:
            pool.terminate()
            pool.join()
            raise
