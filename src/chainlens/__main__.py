"""Command-line demo for chainlens."""

from __future__ import annotations

import argparse
import asyncio
import sys

from chainlens import __version__
from chainlens.blocks import parse_block, parse_transactions
from chainlens.config import get_settings
from chainlens.rpc import EthereumRpcClient


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chainlens",
        description="On-chain Ethereum analytics demo.",
    )
    parser.add_argument("--version", action="version", version=f"chainlens {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    latest = sub.add_parser("latest", help="Fetch and summarize the latest block.")
    latest.add_argument("--show-txs", type=int, default=3, help="How many txs to print.")
    return parser


async def _run_latest(show_txs: int) -> int:
    settings = get_settings()
    print(f"RPC endpoints ({len(settings.rpc_urls)}): {settings.rpc_urls[0]} (+fallbacks)")
    print(f"Whale threshold: {settings.whale_threshold_eth} ETH\\n")

    async with EthereumRpcClient() as client:
        n = await client.block_number()
        print(f"Latest block number: {n}")
        raw = await client.get_block(n, include_txs=True)

    block = parse_block(raw)
    txs = parse_transactions(raw)

    print(f"Block hash:      {block.hash}")
    print(f"Timestamp:       {block.timestamp.isoformat()}")
    print(f"Miner:           {block.miner}")
    print(f"Gas used:        {block.gas_used:,}")
    print(f"Gas limit:       {block.gas_limit:,}")
    print(f"Utilization:     {block.gas_utilization:.2%}")
    if block.base_fee_per_gas is not None:
        print(f"Base fee:        {block.base_fee_per_gas / 1e9:.3f} gwei")
    print(f"Transactions:    {block.transaction_count}")

    if show_txs > 0 and txs:
        print()
        print(f"First {min(show_txs, len(txs))} transactions:")
        for tx in txs[:show_txs]:
            to_display = tx.to_address if tx.to_address else "<contract creation>"
            print(f"  {tx.hash[:18]}...  {tx.value_eth} ETH  -> {to_display[:18]}...")

    print()
    print("Research tool. Not financial advice.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "latest":
        return asyncio.run(_run_latest(args.show_txs))
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
