"""Tests for retry logic with exponential backoff."""

from webscrape.retry import (
    calculate_backoff,
    get_retry_after,
    is_retryable_status,
)


class TestIsRetryableStatus:
    def test_retryable_codes(self):
        for code in [429, 500, 502, 503, 504]:
            assert is_retryable_status(code) is True

    def test_non_retryable_codes(self):
        for code in [200, 201, 400, 401, 403, 404]:
            assert is_retryable_status(code) is False


class TestCalculateBackoff:
    def test_backoff_increases(self):
        delays = [calculate_backoff(i, backoff_base=1.0, backoff_max=100.0) for i in range(5)]
        bases = [1.0 * (2**i) for i in range(5)]
        for delay, base in zip(delays, bases, strict=True):
            assert base <= delay <= base + 1.0

    def test_max_cap(self):
        delay = calculate_backoff(100, backoff_base=1.0, backoff_max=30.0)
        assert delay <= 30.0

    def test_jitter_within_range(self):
        for _ in range(100):
            delay = calculate_backoff(0, backoff_base=1.0, backoff_max=100.0)
            assert 1.0 <= delay <= 2.0


class TestGetRetryAfter:
    def test_numeric_value(self):
        assert get_retry_after({"Retry-After": "5"}) == 5.0

    def test_lowercase_header(self):
        assert get_retry_after({"retry-after": "10"}) == 10.0

    def test_missing_header(self):
        assert get_retry_after({}) is None

    def test_invalid_value(self):
        assert get_retry_after({"Retry-After": "not-a-number"}) is None
