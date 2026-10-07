"""Tests for chainlens.schemas."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from chainlens.schemas import Block, Transaction, wei_to_eth

_TS = datetime(2026, 1, 1, tzinfo=UTC)


def test_wei_to_eth_one_eth() -> None:
    assert wei_to_eth(10**18) == Decimal(1)


def test_wei_to_eth_hex_string() -> None:
    assert wei_to_eth("0xde0b6b3a7640000") == Decimal(1)


def test_wei_to_eth_decimal_string() -> None:
    assert wei_to_eth("1000000000000000000") == Decimal(1)


def test_wei_to_eth_zero() -> None:
    assert wei_to_eth(0) == Decimal(0)


def test_block_gas_utilization() -> None:
    block = Block(
        number=1,
        hash="0xabc",
        parent_hash="0xdef",
        timestamp=_TS,
        miner="0x" + "1" * 40,
        gas_used=15_000_000,
        gas_limit=30_000_000,
        transaction_count=100,
    )
    assert block.gas_utilization == pytest.approx(0.5)


def test_block_gas_utilization_zero_limit() -> None:
    with pytest.raises(ValidationError):
        Block(
            number=1,
            hash="0xabc",
            parent_hash="0xdef",
            timestamp=_TS,
            miner="0x" + "1" * 40,
            gas_used=0,
            gas_limit=0,
            transaction_count=0,
        )


def test_block_immutable() -> None:
    block = Block(
        number=1,
        hash="0xabc",
        parent_hash="0xdef",
        timestamp=_TS,
        miner="0x" + "1" * 40,
        gas_used=100,
        gas_limit=200,
        transaction_count=0,
    )
    with pytest.raises(ValidationError):
        block.number = 2  # type: ignore[misc]


def test_transaction_value_eth() -> None:
    tx = Transaction(
        hash="0xabc",
        block_number=1,
        from_address="0x" + "1" * 40,
        to_address="0x" + "2" * 40,
        value_wei=10**18,
        gas=21000,
        nonce=0,
    )
    assert tx.value_eth == Decimal(1)


def test_transaction_rejects_negative_value() -> None:
    with pytest.raises(ValidationError):
        Transaction(
            hash="0xabc",
            block_number=1,
            from_address="0x" + "1" * 40,
            value_wei=-1,
            gas=21000,
            nonce=0,
        )
