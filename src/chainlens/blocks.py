"""Parse raw RPC block payloads into validated domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from chainlens.schemas import Block, Transaction


def _hex_to_int(value: str | None) -> int:
    if value is None:
        return 0
    return int(value, 16)


def parse_block(raw: dict[str, Any]) -> Block:
    """Convert a raw eth_getBlockByNumber payload into a Block."""
    base_fee = raw.get("baseFeePerGas")
    return Block(
        number=_hex_to_int(raw["number"]),
        hash=str(raw["hash"]),
        parent_hash=str(raw["parentHash"]),
        timestamp=datetime.fromtimestamp(_hex_to_int(raw["timestamp"]), tz=UTC),
        miner=str(raw["miner"]),
        gas_used=_hex_to_int(raw["gasUsed"]),
        gas_limit=_hex_to_int(raw["gasLimit"]),
        base_fee_per_gas=_hex_to_int(base_fee) if base_fee else None,
        transaction_count=len(raw.get("transactions") or []),
    )


def parse_transaction(raw: dict[str, Any], block_number: int) -> Transaction:
    """Convert a raw transaction payload into a Transaction."""
    gas_price = raw.get("gasPrice")
    to_addr = raw.get("to")
    return Transaction(
        hash=str(raw["hash"]),
        block_number=block_number,
        from_address=str(raw["from"]).lower(),
        to_address=str(to_addr).lower() if to_addr else None,
        value_wei=_hex_to_int(raw["value"]),
        gas=_hex_to_int(raw["gas"]),
        gas_price=_hex_to_int(gas_price) if gas_price else None,
        nonce=_hex_to_int(raw["nonce"]),
    )


def parse_transactions(raw_block: dict[str, Any]) -> list[Transaction]:
    """Extract and parse all full transactions from a block payload."""
    block_number = _hex_to_int(raw_block["number"])
    txs = raw_block.get("transactions") or []
    parsed: list[Transaction] = []
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        parsed.append(parse_transaction(tx, block_number))
    return parsed
