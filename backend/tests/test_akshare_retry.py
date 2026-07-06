import pytest

from app.providers.akshare_provider import _retry


def test_retry_with_tries_1_calls_once_and_raises() -> None:
    calls = 0

    def always_fail() -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        _retry(always_fail, "test-op", tries=1)

    assert calls == 1
