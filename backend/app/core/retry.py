"""
Retry Logic with Exponential Backoff
Utility decorators for handling transient API failures
"""

import time
import logging
import functools
from typing import Callable, Type, Tuple, Optional
import requests

logger = logging.getLogger(__name__)


class RetryExhausted(Exception):
    """Raised when all retry attempts have been exhausted"""

    pass


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
    ),
    retryable_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504),
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        max_delay: Maximum delay between retries
        retryable_exceptions: Tuple of exceptions that trigger retry
        retryable_status_codes: HTTP status codes that trigger retry

    Example:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        def fetch_data(url):
            return requests.get(url)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    # Check for retryable HTTP status codes
                    if hasattr(result, "status_code"):
                        if result.status_code in retryable_status_codes:
                            if attempt < max_retries:
                                logger.warning(
                                    f"Retryable status {result.status_code} from {func.__name__}, "
                                    f"attempt {attempt + 1}/{max_retries + 1}, "
                                    f"retrying in {delay:.1f}s"
                                )
                                time.sleep(delay)
                                delay = min(delay * backoff_factor, max_delay)
                                continue
                            else:
                                logger.error(
                                    f"Max retries exhausted for {func.__name__} "
                                    f"with status {result.status_code}"
                                )

                    # Success - log if we recovered from retries
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded after {attempt + 1} attempts"
                        )
                    return result

                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Retryable error in {func.__name__}: {type(e).__name__}: {e}, "
                            f"attempt {attempt + 1}/{max_retries + 1}, "
                            f"retrying in {delay:.1f}s"
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"Max retries exhausted for {func.__name__}: "
                            f"{type(e).__name__}: {e}"
                        )
                        raise

                except Exception as e:
                    # Non-retryable exception - fail immediately
                    logger.error(
                        f"Non-retryable error in {func.__name__}: "
                        f"{type(e).__name__}: {e}"
                    )
                    raise

            # If we get here, all retries for status codes were exhausted
            if last_exception:
                raise last_exception
            return result

        return wrapper

    return decorator


def with_fallback(fallback_value=None, log_error: bool = True):
    """
    Decorator that catches exceptions and returns a fallback value.

    Args:
        fallback_value: Value to return on exception (can be callable)
        log_error: Whether to log the error

    Example:
        @with_fallback(fallback_value=[])
        def get_items():
            return api.fetch_items()
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        f"Error in {func.__name__}: {type(e).__name__}: {e}, "
                        f"returning fallback value"
                    )
                if callable(fallback_value):
                    return fallback_value()
                return fallback_value

        return wrapper

    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.

    States:
        CLOSED: Normal operation, requests pass through
        OPEN: Failures exceeded threshold, requests fail fast
        HALF_OPEN: Testing if service has recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
        name: str = "circuit_breaker",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name

        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        """Check if execution is allowed (circuit not open)."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")
                return True
            return False
        return True

    def record_success(self):
        """Record a successful execution."""
        if self.state == "HALF_OPEN":
            logger.info(f"Circuit breaker {self.name} recovered, entering CLOSED state")
        self.state = "CLOSED"
        self.failures = 0

    def record_failure(self):
        """Record a failed execution."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                f"Circuit breaker {self.name} tripped after "
                f"{self.failures} failures, entering OPEN state"
            )

    def __call__(self, func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_execute():
                logger.warning(
                    f"Circuit breaker OPEN for {func.__name__}, failing fast"
                )
                raise RetryExhausted(f"Circuit breaker is open for {func.__name__}")

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result

            except self.expected_exception as e:
                self.record_failure()
                raise

        return wrapper

    def reset(self):
        """Manually reset the circuit breaker"""
        self.failures = 0
        self.state = "CLOSED"
        logger.info(f"Circuit breaker {self.name} manually reset")


# Alias for convenience
with_retry = retry_with_backoff
