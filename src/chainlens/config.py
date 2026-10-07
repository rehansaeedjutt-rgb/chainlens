"""Configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Multiple free public Ethereum RPC endpoints. The client tries them in order.
# No API key required. Some endpoints rate-limit or fail transiently —
# having several means one outage does not break the tool.
_DEFAULT_RPC_URLS = [
    "https://ethereum.publicnode.com",
    "https://eth.drpc.org",
    "https://rpc.ankr.com/eth",
    "https://cloudflare-eth.com",
    "https://eth.llamarpc.com",
]


class Settings(BaseSettings):
    """Runtime settings for chainlens.

    All values can be overridden via environment variables prefixed with
    ``CHAINLENS_`` (e.g. ``CHAINLENS_RPC_URLS=...``) or a local ``.env``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CHAINLENS_",
        case_sensitive=False,
        extra="ignore",
    )

    rpc_urls: list[str] = Field(
        default_factory=lambda: list(_DEFAULT_RPC_URLS),
        description="Ethereum JSON-RPC endpoints, tried in order.",
    )
    request_timeout_seconds: float = Field(default=15.0, gt=0)
    max_retries: int = Field(default=2, ge=0, le=10, description="Retries per endpoint.")

    whale_threshold_eth: float = Field(
        default=100.0,
        gt=0,
        description="Minimum ETH value for a transfer to count as a whale move.",
    )

    tracked_addresses: list[str] = Field(default_factory=list)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
