"""
Resilient AI Client
====================

Provides connection-resilient wrapper for Anthropic API calls with:
- Automatic retry with exponential backoff
- Connection error recovery
- Intermediate result caching for resumption
- Progress tracking for long-running analyses
"""

import time
import logging
import json
import os
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps
from datetime import datetime
import anthropic
from anthropic import APIConnectionError, APITimeoutError, RateLimitError, APIStatusError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to delays
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        import random
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        if self.jitter:
            delay = delay * (0.5 + random.random())
        return delay


# Connection-related exceptions that should trigger retry
RETRYABLE_EXCEPTIONS = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    ConnectionError,
    TimeoutError,
    OSError,  # Network errors
)


def with_retry(
    retry_config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None
):
    """
    Decorator for adding retry logic to functions.

    Args:
        retry_config: Retry configuration (defaults to standard config)
        on_retry: Callback called on each retry (attempt, exception, delay)
    """
    if retry_config is None:
        retry_config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(retry_config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RETRYABLE_EXCEPTIONS as e:
                    last_exception = e

                    if attempt == retry_config.max_retries:
                        logger.error(
                            f"Max retries ({retry_config.max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        raise

                    delay = retry_config.get_delay(attempt)

                    logger.warning(
                        f"Retry {attempt + 1}/{retry_config.max_retries} for {func.__name__} "
                        f"after {delay:.1f}s due to: {type(e).__name__}: {str(e)[:100]}"
                    )

                    if on_retry:
                        on_retry(attempt + 1, e, delay)

                    time.sleep(delay)
                except APIStatusError as e:
                    # Don't retry on client errors (4xx except 429)
                    if 400 <= e.status_code < 500 and e.status_code != 429:
                        raise

                    last_exception = e
                    if attempt == retry_config.max_retries:
                        raise

                    delay = retry_config.get_delay(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{retry_config.max_retries} for {func.__name__} "
                        f"after {delay:.1f}s due to API error {e.status_code}"
                    )

                    if on_retry:
                        on_retry(attempt + 1, e, delay)

                    time.sleep(delay)

            # This should not be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected state in retry logic for {func.__name__}")

        return wrapper
    return decorator


class ResilientAnthropicClient:
    """
    Wrapper around Anthropic client with built-in resilience.

    Features:
    - Automatic retry with exponential backoff
    - Connection recovery
    - Progress callbacks for long operations
    - Intermediate result caching
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize resilient client.

        Args:
            api_key: Anthropic API key (defaults to env var)
            retry_config: Custom retry configuration
            cache_dir: Directory for caching intermediate results
        """
        if api_key is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')

        if not api_key:
            raise ValueError(
                "API key not configured. Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = anthropic.Anthropic(api_key=api_key)
        self.retry_config = retry_config or RetryConfig()
        self.cache_dir = cache_dir or os.path.expanduser('~/.acs/ai_cache')

        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)

        # Track current operation for resumption
        self._current_operation_id: Optional[str] = None
        self._progress_callback: Optional[Callable[[str, int, int], None]] = None

    def set_progress_callback(
        self,
        callback: Callable[[str, int, int], None]
    ):
        """
        Set callback for progress updates.

        Args:
            callback: Function(message, current_step, total_steps)
        """
        self._progress_callback = callback

    def _notify_progress(self, message: str, current: int, total: int):
        """Send progress notification if callback is set."""
        if self._progress_callback:
            try:
                self._progress_callback(message, current, total)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def _on_retry(self, attempt: int, exception: Exception, delay: float):
        """Handle retry event."""
        self._notify_progress(
            f"Connessione persa, riprovo ({attempt}/{self.retry_config.max_retries}) tra {delay:.0f}s...",
            -1, -1
        )

    def _save_intermediate_result(
        self,
        operation_id: str,
        step: int,
        result: Any
    ):
        """Save intermediate result for potential resumption."""
        try:
            cache_file = os.path.join(
                self.cache_dir,
                f"{operation_id}_step_{step}.json"
            )
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'operation_id': operation_id,
                    'step': step,
                    'timestamp': datetime.now().isoformat(),
                    'result': result
                }, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved intermediate result: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save intermediate result: {e}")

    def _load_intermediate_results(
        self,
        operation_id: str
    ) -> Dict[int, Any]:
        """Load any saved intermediate results."""
        results = {}
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.startswith(f"{operation_id}_step_") and filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        results[data['step']] = data['result']
        except Exception as e:
            logger.warning(f"Failed to load intermediate results: {e}")
        return results

    def _clear_intermediate_results(self, operation_id: str):
        """Clear intermediate results after successful completion."""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.startswith(f"{operation_id}_step_"):
                    filepath = os.path.join(self.cache_dir, filename)
                    os.remove(filepath)
        except Exception as e:
            logger.warning(f"Failed to clear intermediate results: {e}")

    def create_message(
        self,
        model: str,
        max_tokens: int,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        system: Optional[str] = None,
        **kwargs
    ) -> anthropic.types.Message:
        """
        Create a message with automatic retry on connection errors.

        Args:
            model: Model ID to use
            max_tokens: Maximum tokens in response
            messages: List of message dicts
            temperature: Sampling temperature
            system: Optional system prompt
            **kwargs: Additional arguments passed to API

        Returns:
            Anthropic Message response
        """
        @with_retry(self.retry_config, self._on_retry)
        def _create():
            params = {
                'model': model,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': messages,
                **kwargs
            }
            if system:
                params['system'] = system

            return self.client.messages.create(**params)

        return _create()

    def stream_message(
        self,
        model: str,
        max_tokens: int,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        system: Optional[str] = None,
        **kwargs
    ):
        """
        Stream a message with automatic retry on connection errors.

        Yields text chunks. If connection is lost mid-stream,
        will retry from the beginning.

        Args:
            model: Model ID
            max_tokens: Maximum tokens
            messages: List of message dicts
            temperature: Sampling temperature
            system: Optional system prompt
            **kwargs: Additional arguments

        Yields:
            Text chunks from the response
        """
        @with_retry(self.retry_config, self._on_retry)
        def _stream():
            params = {
                'model': model,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': messages,
                **kwargs
            }
            if system:
                params['system'] = system

            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text

        # Note: If connection fails mid-stream, entire stream restarts
        return _stream()

    def batch_process(
        self,
        items: List[Any],
        process_func: Callable[[Any, 'ResilientAnthropicClient'], Any],
        operation_id: Optional[str] = None,
        resume: bool = True
    ) -> List[Any]:
        """
        Process a batch of items with retry and resumption support.

        Args:
            items: List of items to process
            process_func: Function(item, client) -> result
            operation_id: Unique ID for this operation (for resumption)
            resume: Whether to resume from cached results

        Returns:
            List of results
        """
        if operation_id is None:
            operation_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self._current_operation_id = operation_id

        # Load any existing intermediate results
        cached_results = {}
        if resume:
            cached_results = self._load_intermediate_results(operation_id)
            if cached_results:
                logger.info(
                    f"Resuming operation {operation_id}: "
                    f"found {len(cached_results)} cached results"
                )

        results = [None] * len(items)

        # Fill in cached results
        for step, result in cached_results.items():
            if 0 <= step < len(results):
                results[step] = result

        # Process remaining items
        for i, item in enumerate(items):
            if results[i] is not None:
                self._notify_progress(
                    f"Usando risultato in cache per elemento {i + 1}/{len(items)}",
                    i + 1, len(items)
                )
                continue

            self._notify_progress(
                f"Elaborazione elemento {i + 1}/{len(items)}...",
                i + 1, len(items)
            )

            try:
                result = process_func(item, self)
                results[i] = result

                # Save intermediate result
                self._save_intermediate_result(operation_id, i, result)

            except Exception as e:
                logger.error(f"Failed to process item {i}: {e}")
                # Save partial results up to this point
                results[i] = {'error': str(e)}
                self._save_intermediate_result(operation_id, i, results[i])

        # Clear intermediate results on success
        if all(r is not None and not (isinstance(r, dict) and 'error' in r) for r in results):
            self._clear_intermediate_results(operation_id)

        self._current_operation_id = None
        return results


class AnalysisSession:
    """
    Manages a long-running analysis session with resumption support.
    """

    def __init__(
        self,
        session_id: str,
        client: ResilientAnthropicClient,
        db=None
    ):
        """
        Initialize analysis session.

        Args:
            session_id: Unique session identifier
            client: Resilient AI client
            db: Optional database for persistence
        """
        self.session_id = session_id
        self.client = client
        self.db = db
        self.steps_completed: List[str] = []
        self.results: Dict[str, Any] = {}
        self._status = 'initialized'
        self._progress = 0
        self._error: Optional[str] = None

        # Load existing session if available
        self._load_session()

    def _load_session(self):
        """Load session state from database."""
        if self.db:
            try:
                session_data = self.db.get_ai_cache(self.session_id, 'analysis_session')
                if session_data:
                    content = session_data.get('content', {})
                    self.steps_completed = content.get('steps_completed', [])
                    self.results = content.get('results', {})
                    self._status = content.get('status', 'initialized')
                    self._progress = content.get('progress', 0)
                    logger.info(f"Resumed session {self.session_id}: {len(self.steps_completed)} steps completed")
            except Exception as e:
                logger.warning(f"Could not load session: {e}")

    def _save_session(self):
        """Save session state to database."""
        if self.db:
            try:
                self.db.save_ai_cache(
                    self.session_id,
                    'analysis_session',
                    {
                        'steps_completed': self.steps_completed,
                        'results': self.results,
                        'status': self._status,
                        'progress': self._progress,
                        'error': self._error,
                        'updated_at': datetime.now().isoformat()
                    },
                    model='session_manager'
                )
            except Exception as e:
                logger.warning(f"Could not save session: {e}")

    @property
    def status(self) -> str:
        return self._status

    @property
    def progress(self) -> int:
        return self._progress

    def is_step_completed(self, step_name: str) -> bool:
        """Check if a step has been completed."""
        return step_name in self.steps_completed

    def get_step_result(self, step_name: str) -> Optional[Any]:
        """Get result from a completed step."""
        return self.results.get(step_name)

    def run_step(
        self,
        step_name: str,
        step_func: Callable[[], Any],
        progress_value: int = None
    ) -> Any:
        """
        Run a step with automatic resumption support.

        If step was already completed, returns cached result.
        Otherwise runs the step and caches the result.

        Args:
            step_name: Unique step identifier
            step_func: Function to execute for this step
            progress_value: Progress percentage after this step

        Returns:
            Step result (cached or newly computed)
        """
        if self.is_step_completed(step_name):
            logger.info(f"Step '{step_name}' already completed, using cached result")
            return self.get_step_result(step_name)

        self._status = 'running'

        try:
            result = step_func()

            self.results[step_name] = result
            self.steps_completed.append(step_name)

            if progress_value is not None:
                self._progress = progress_value

            self._save_session()

            return result

        except Exception as e:
            self._status = 'error'
            self._error = str(e)
            self._save_session()
            raise

    def complete(self):
        """Mark session as completed."""
        self._status = 'completed'
        self._progress = 100
        self._save_session()

    def fail(self, error: str):
        """Mark session as failed."""
        self._status = 'failed'
        self._error = error
        self._save_session()


# Global resilient client instance
_resilient_client: Optional[ResilientAnthropicClient] = None


def get_resilient_client(
    api_key: Optional[str] = None,
    retry_config: Optional[RetryConfig] = None
) -> ResilientAnthropicClient:
    """
    Get or create the global resilient AI client.

    Args:
        api_key: Optional API key (uses env var if not provided)
        retry_config: Optional custom retry configuration

    Returns:
        ResilientAnthropicClient instance
    """
    global _resilient_client

    if _resilient_client is None:
        _resilient_client = ResilientAnthropicClient(
            api_key=api_key,
            retry_config=retry_config
        )

    return _resilient_client
