"""Tests for chainlens.blocks parsers."""

from datetime import UTC, datetime

from chainlens.blocks import parse_block, parse_transaction, parse_transactions


def _raw_block() -> dict[str, object]:
    return {
        "number": "0x100",
        "hash": "0xabc",
        "parentHash": "0xdef",
        "timestamp": "0x65000000",
        "miner": "0x" + "1" * 40,
        "gasUsed": "0x1",
        "gasLimit": "0x2",
        "baseFeePerGas": "0x3b9aca00",
        "transactions": [],
    }


def test_parse_block_basic() -> None:
    block = parse_block(_raw_block())  # type: ignore[arg-type]
    assert block.number == 0x100
    assert block.gas_used == 1
    assert block.gas_limit == 2
    assert block.base_fee_per_gas == 1_000_000_000
    assert block.transaction_count == 0
    assert block.timestamp == datetime.fromtimestamp(0x65000000, tz=UTC)


def test_parse_block_no_base_fee() -> None:
    raw = _raw_block()
    del raw["baseFeePerGas"]
    block = parse_block(raw)  # type: ignore[arg-type]
    assert block.base_fee_per_gas is None


def test_parse_transaction_basic() -> None:
    raw = {
        "hash": "0xaaa",
        "from": "0x" + "1" * 40,
        "to": "0x" + "2" * 40,
        "value": "0xde0b6b3a7640000",
        "gas": "0x5208",
        "gasPrice": "0x3b9aca00",
        "nonce": "0x1",
    }
    tx = parse_transaction(raw, block_number=100)
    assert tx.block_number == 100
    assert tx.from_address == ("0x" + "1" * 40).lower()
    assert tx.to_address == ("0x" + "2" * 40).lower()
    assert tx.value_wei == 10**18
    assert tx.nonce == 1


def test_parse_transaction_contract_creation() -> None:
    raw = {
        "hash": "0xbbb",
        "from": "0x" + "1" * 40,
        "to": None,
        "value": "0x0",
        "gas": "0x5208",
        "nonce": "0x0",
    }
    tx = parse_transaction(raw, block_number=1)
    assert tx.to_address is None


def test_parse_transactions_skips_non_dicts() -> None:
    raw_block = {
        "number": "0x1",
        "transactions": [
            {
                "hash": "0x1",
                "from": "0x" + "1" * 40,
                "to": None,
                "value": "0x0",
                "gas": "0x1",
                "nonce": "0x0",
            },
            "not-a-dict",
        ],
    }
    txs = parse_transactions(raw_block)  # type: ignore[arg-type]
    assert len(txs) == 1
    assert txs[0].hash == "0x1"


def test_parse_transactions_empty() -> None:
    assert parse_transactions({"number": "0x1", "transactions": []}) == []
