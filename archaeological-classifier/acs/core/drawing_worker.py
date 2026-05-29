"""
Drawing Worker Module
=====================

Generates technical drawings in-process, serialized through a single-worker
thread pool to protect matplotlib's global state under concurrent requests.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError


_executor = None
_executor_lock = threading.Lock()


def _get_executor():
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix='drawing'
                )
    return _executor


def _generate_view(mesh, artifact_id, features, view_type, output_format):
    """
    Generate a drawing view. Runs inside the single-worker thread pool.

    Uses generate_single_view for individual views (fast — one view only)
    and generate_complete_drawing only for 'complete_sheet' (which needs
    all sub-views for the composite).
    """
    import matplotlib
    matplotlib.use('Agg')

    from acs.core.technical_drawing import TechnicalDrawingGenerator

    drawer = TechnicalDrawingGenerator()
    return drawer.generate_single_view(
        mesh, artifact_id, view_type,
        features=features, output_format=output_format
    )


def generate_drawing_worker(mesh, artifact_id, features, view_type='complete_sheet',
                            output_format='png'):
    """
    Generate a single technical drawing view.

    Returns:
        Tuple of (success: bool, data: bytes or error_message: str)
    """
    try:
        data = _generate_view(mesh, artifact_id, features, view_type, output_format)
        return (True, data)
    except Exception as e:
        import traceback
        return (False, f"Drawing generation failed: {str(e)}\n{traceback.format_exc()}")


def generate_drawing_safe(mesh, artifact_id, features, view_type='complete_sheet',
                          timeout=120, output_format='png'):
    """
    Generate a technical drawing in-process, serialized and with a timeout.

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
        Exception: On generation failure or timeout
    """
    executor = _get_executor()
    future = executor.submit(
        _generate_view, mesh, artifact_id, features, view_type, output_format
    )

    try:
        return future.result(timeout=timeout)
    except FuturesTimeoutError:
        raise Exception(f"Drawing generation timed out after {timeout} seconds")
    except Exception:
        raise
