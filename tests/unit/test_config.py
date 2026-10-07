"""Tests for chainlens.config."""

from chainlens.config import Settings, get_settings


def test_settings_defaults() -> None:
    s = Settings()
    assert len(s.rpc_urls) >= 3
    assert all(u.startswith("https://") for u in s.rpc_urls)
    assert s.request_timeout_seconds > 0
    assert s.max_retries >= 0
    assert s.whale_threshold_eth > 0
    assert s.tracked_addresses == []


def test_settings_override_urls() -> None:
    s = Settings(rpc_urls=["https://custom.example.com"])
    assert s.rpc_urls == ["https://custom.example.com"]


def test_settings_override_threshold() -> None:
    s = Settings(whale_threshold_eth=500.0)
    assert s.whale_threshold_eth == 500.0


def test_get_settings_is_cached() -> None:
    a = get_settings()
    b = get_settings()
    assert a is b
