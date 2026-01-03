"""
Unit Tests for Retry Logic
Tests exponential backoff and circuit breaker functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from app.core.retry import retry_with_backoff, with_fallback, CircuitBreaker, RetryExhausted


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator"""

    def test_success_first_try(self):
        """Test successful call on first attempt"""
        call_count = [0]

        @retry_with_backoff(max_retries=3)
        def test_func():
            call_count[0] += 1
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 1

    def test_retry_on_connection_error(self):
        """Test retry on ConnectionError"""
        call_count = [0]

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise requests.exceptions.ConnectionError("Failed")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 2

    def test_retry_on_timeout(self):
        """Test retry on Timeout"""
        call_count = [0]

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def test_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise requests.exceptions.Timeout("Timed out")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 3

    def test_max_retries_exhausted(self):
        """Test that exception is raised after max retries"""
        call_count = [0]

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def test_func():
            call_count[0] += 1
            raise requests.exceptions.Timeout("Timed out")

        with pytest.raises(requests.exceptions.Timeout):
            test_func()

        assert call_count[0] == 3  # Initial + 2 retries

    def test_non_retryable_exception_fails_immediately(self):
        """Test that non-retryable exceptions fail immediately"""
        call_count = [0]

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def test_func():
            call_count[0] += 1
            raise ValueError("Bad value")

        with pytest.raises(ValueError):
            test_func()

        assert call_count[0] == 1  # No retries

    def test_retry_on_500_status(self):
        """Test retry on 500 status code"""
        call_count = [0]

        @retry_with_backoff(
            max_retries=3, initial_delay=0.01, retryable_status_codes=(500, 502, 503)
        )
        def test_func():
            call_count[0] += 1
            if call_count[0] < 3:
                return Mock(status_code=500)
            return Mock(status_code=200)

        result = test_func()

        assert result.status_code == 200
        assert call_count[0] == 3

    def test_retry_on_429_rate_limit(self):
        """Test retry on 429 rate limit"""
        call_count = [0]

        @retry_with_backoff(max_retries=3, initial_delay=0.01, retryable_status_codes=(429,))
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                return Mock(status_code=429, headers={})
            return Mock(status_code=200)

        result = test_func()

        assert result.status_code == 200


class TestWithFallback:
    """Tests for with_fallback decorator"""

    def test_returns_result_on_success(self):
        """Test normal return when function succeeds"""

        @with_fallback(fallback_value="default")
        def test_func():
            return "result"

        result = test_func()

        assert result == "result"

    def test_returns_fallback_on_exception(self):
        """Test fallback value returned on exception"""

        @with_fallback(fallback_value="default")
        def test_func():
            raise ValueError("Error")

        result = test_func()

        assert result == "default"

    def test_returns_empty_list_fallback(self):
        """Test empty list as fallback"""

        @with_fallback(fallback_value=[])
        def test_func():
            raise Exception("Error")

        result = test_func()

        assert result == []

    def test_callable_fallback(self):
        """Test callable fallback value"""
        call_count = [0]

        def fallback_factory():
            call_count[0] += 1
            return {"default": True}

        @with_fallback(fallback_value=fallback_factory)
        def test_func():
            raise Exception("Error")

        result = test_func()

        assert result == {"default": True}
        assert call_count[0] == 1


class TestCircuitBreaker:
    """Tests for CircuitBreaker class"""

    def test_closed_state_allows_requests(self):
        """Test that CLOSED state allows requests"""
        breaker = CircuitBreaker(failure_threshold=3)

        @breaker
        def test_func():
            return "success"

        result = test_func()

        assert result == "success"
        assert breaker.state == "CLOSED"

    def test_opens_after_failure_threshold(self):
        """Test circuit opens after reaching failure threshold"""
        breaker = CircuitBreaker(failure_threshold=3)

        @breaker
        def test_func():
            raise Exception("Error")

        # Fail 3 times to trigger open
        for _ in range(3):
            with pytest.raises(Exception):
                test_func()

        assert breaker.state == "OPEN"
        assert breaker.failures == 3

    def test_open_state_fails_fast(self):
        """Test that OPEN state rejects requests immediately"""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60)
        call_count = [0]

        @breaker
        def test_func():
            call_count[0] += 1
            raise Exception("Error")

        # Trigger open state
        with pytest.raises(Exception):
            test_func()

        # Should fail fast without calling function
        with pytest.raises(RetryExhausted):
            test_func()

        assert call_count[0] == 1  # Only first call reached function

    def test_half_open_after_timeout(self):
        """Test circuit enters HALF_OPEN after recovery timeout"""
        import time

        breaker = CircuitBreaker(
            failure_threshold=1, recovery_timeout=0.01  # Very short for testing
        )
        call_count = [0]

        @breaker
        def test_func():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Error")
            return "success"

        # Trigger open state
        with pytest.raises(Exception):
            test_func()

        assert breaker.state == "OPEN"

        # Wait for recovery timeout
        time.sleep(0.02)

        # Should allow through (half-open) and succeed
        result = test_func()

        assert result == "success"
        assert breaker.state == "CLOSED"

    def test_reset_clears_failures(self):
        """Test manual reset clears failure count"""
        breaker = CircuitBreaker(failure_threshold=5)
        breaker.failures = 3
        breaker.state = "OPEN"

        breaker.reset()

        assert breaker.failures == 0
        assert breaker.state == "CLOSED"
