"""Tests for chainlens.rpc — no network calls."""

from unittest.mock import AsyncMock, patch

import pytest

from chainlens.rpc import EthereumRpcClient, RpcError


def test_client_requires_at_least_one_url() -> None:
    with pytest.raises(ValueError, match="at least one"):
        EthereumRpcClient(urls=[])


def test_client_accepts_url_list() -> None:
    client = EthereumRpcClient(urls=["https://a.example.com", "https://b.example.com"])
    assert len(client._urls) == 2


@pytest.mark.asyncio
async def test_call_without_context_manager_raises() -> None:
    client = EthereumRpcClient(urls=["https://a.example.com"])
    with pytest.raises(RpcError, match="context manager"):
        await client.call("eth_blockNumber", [])


@pytest.mark.asyncio
async def test_client_context_manager_opens_session() -> None:
    async with EthereumRpcClient(urls=["https://a.example.com"]) as client:
        assert client._session is not None
        assert not client._session.closed
    assert client._session is None


@pytest.mark.asyncio
async def test_block_number_parses_hex() -> None:
    async with EthereumRpcClient(urls=["https://a.example.com"]) as client:
        with patch.object(client, "call", new=AsyncMock(return_value="0x100")):
            n = await client.block_number()
            assert n == 256


@pytest.mark.asyncio
async def test_block_number_rejects_non_string() -> None:
    async with EthereumRpcClient(urls=["https://a.example.com"]) as client:
        with (
            patch.object(client, "call", new=AsyncMock(return_value=123)),
            pytest.raises(RpcError, match="unexpected"),
        ):
            await client.block_number()


@pytest.mark.asyncio
async def test_get_block_returns_dict() -> None:
    raw = {"number": "0x1", "hash": "0xabc"}
    async with EthereumRpcClient(urls=["https://a.example.com"]) as client:
        with patch.object(client, "call", new=AsyncMock(return_value=raw)):
            result = await client.get_block(1)
            assert result == raw


@pytest.mark.asyncio
async def test_get_block_raises_on_none() -> None:
    async with EthereumRpcClient(urls=["https://a.example.com"]) as client:
        with (
            patch.object(client, "call", new=AsyncMock(return_value=None)),
            pytest.raises(RpcError, match="not found"),
        ):
            await client.get_block(999_999_999)


@pytest.mark.asyncio
async def test_get_block_raises_on_non_dict() -> None:
    async with EthereumRpcClient(urls=["https://a.example.com"]) as client:
        with (
            patch.object(client, "call", new=AsyncMock(return_value="not-a-dict")),
            pytest.raises(RpcError, match="unexpected"),
        ):
            await client.get_block(1)
