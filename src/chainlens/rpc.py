"""Async Ethereum JSON-RPC client with multi-endpoint fallback."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import structlog

from chainlens.config import get_settings

logger = structlog.get_logger(__name__)


class RpcError(RuntimeError):
    """Raised when all endpoints fail or return invalid responses."""


class EthereumRpcClient:
    """Minimal async JSON-RPC client with multi-endpoint rotation.

    Tries each configured endpoint in order. On transient failure, retries
    that endpoint with backoff, then moves to the next. Public endpoints
    are best-effort; having several means one outage does not break us.
    """

    def __init__(
        self,
        urls: list[str] | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        settings = get_settings()
        self._urls = list(urls) if urls is not None else list(settings.rpc_urls)
        if not self._urls:
            msg = "at least one RPC URL is required"
            raise ValueError(msg)
        self._timeout = timeout or settings.request_timeout_seconds
        self._max_retries = max_retries if max_retries is not None else settings.max_retries
        self._session: aiohttp.ClientSession | None = None
        self._request_id = 0
        self._last_url: str | None = None

    @property
    def last_url(self) -> str | None:
        """URL of the endpoint that served the most recent successful call."""
        return self._last_url

    async def __aenter__(self) -> EthereumRpcClient:
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._timeout))
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    async def call(self, method: str, params: list[Any]) -> Any:
        """Call a JSON-RPC method, trying each endpoint until one succeeds."""
        if self._session is None:
            msg = "client must be used as async context manager"
            raise RpcError(msg)

        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        errors: list[str] = []
        for url in self._urls:
            try:
                result = await self._call_one(url, payload, method)
            except RpcError as exc:
                errors.append(f"{url}: {exc}")
                logger.warning("rpc.endpoint_failed", url=url, method=method, error=str(exc))
                continue
            self._last_url = url
            return result

        combined = "; ".join(errors)
        msg = f"all {len(self._urls)} RPC endpoints failed for {method}: {combined}"
        raise RpcError(msg)

    async def _call_one(self, url: str, payload: dict[str, Any], method: str) -> Any:
        session = self._session
        if session is None:
            msg = "client must be used as async context manager"
            raise RpcError(msg)

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status >= 500:
                        msg = f"HTTP {resp.status}"
                        raise RpcError(msg)
                    if resp.status >= 400:
                        msg = f"HTTP {resp.status}"
                        raise RpcError(msg)
                    data = await resp.json()
            except (TimeoutError, aiohttp.ClientError, RpcError) as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    break
                delay = min(0.5 * (2**attempt), 2.0)
                await asyncio.sleep(delay)
                continue

            if "error" in data:
                err_msg = data["error"]
                raise RpcError(f"JSON-RPC error on {method}: {err_msg}")
            return data.get("result")

        msg = f"failed after {self._max_retries + 1} attempts"
        raise RpcError(msg) from last_exc

    async def block_number(self) -> int:
        """Return the latest block number."""
        result = await self.call("eth_blockNumber", [])
        if not isinstance(result, str):
            msg = f"unexpected block number result: {result!r}"
            raise RpcError(msg)
        return int(result, 16)

    async def get_block(self, block_number: int, include_txs: bool = True) -> dict[str, Any]:
        """Return a block by number (raw dict payload)."""
        hex_number = hex(block_number)
        result = await self.call("eth_getBlockByNumber", [hex_number, include_txs])
        if result is None:
            msg = f"block {block_number} not found"
            raise RpcError(msg)
        if not isinstance(result, dict):
            msg = f"unexpected block result: {result!r}"
            raise RpcError(msg)
        return result
