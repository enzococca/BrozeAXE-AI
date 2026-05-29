"""
Drawing Worker Module
=====================

Generates technical drawings in-process, serialized through a single-worker
thread pool.

Rationale: the Flask dev server runs threaded and the app also starts a
background daemon thread. Using multiprocessing here is unsafe:
- 'fork' on Linux copies a multithreaded process and inherits locks held by
  other threads (malloc, logging, matplotlib) -> the child deadlocks -> the
  request hangs and the gateway returns 502.
- 'spawn' restarts a full interpreter (re-imports trimesh/scipy/matplotlib and
  unpickles the mesh) -> slow, easily exceeding the timeout -> 500.

Since matplotlib uses the headless 'Agg' backend, drawings can be rendered
in-process. The only concern is pyplot's global state under concurrent
requests, which we avoid by serializing all generation through a module-level
ThreadPoolExecutor(max_workers=1). That same executor also provides a timeout.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError


# Single-worker executor: serializes pyplot access and gives us a timeout.
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


def generate_drawing_worker(mesh, artifact_id, features, view_type='complete_sheet',
                            output_format='png'):
    """
    Generate a single technical drawing view in the current thread.

    Args:
        mesh: Trimesh object
        artifact_id: Artifact identifier
        features: Feature dictionary
        view_type: Type of view to generate
        output_format: 'png' or 'svg'

    Returns:
        Tuple of (success: bool, data: bytes or error_message: str)
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Ensure headless backend

        from acs.core.technical_drawing import TechnicalDrawingGenerator

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
        generate_drawing_worker, mesh, artifact_id, features, view_type, output_format
    )

    try:
        success, data = future.result(timeout=timeout)
    except FuturesTimeoutError:
        # The task keeps running, but max_workers=1 keeps later requests serialized.
        raise Exception(f"Drawing generation timed out after {timeout} seconds")

    if success:
        return data
    else:
        raise Exception(data)
