# chainlens

> On-chain analytics: Ethereum block ingestion, whale detection, address activity.

[![CI](https://github.com/rehansaeedjutt-rgb/chainlens/actions/workflows/ci.yml/badge.svg)](https://github.com/rehansaeedjutt-rgb/chainlens/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Overview

`chainlens` ingests Ethereum block data via public JSON-RPC endpoints and produces
structured analytics: block metrics, gas usage, whale-sized transfers, and
address activity summaries.

**Status:** Phase 1 complete — RPC client, block parser, CLI, multi-endpoint resilience.

**Free-first:** Uses public RPC endpoints — no API key, no signup, no credit card.

## Why this project exists

On-chain data is the only **unfakeable** signal in crypto. Exchange volumes can be
washed. Social sentiment can be botted. But every Ethereum transaction is public,
permanent, and cryptographically verified.

Most retail tooling treats blockchain data as a black box (Etherscan) or ignores it
as too low-level. `chainlens` treats it the way a data engineer would: as a stream
to be validated, normalized, and persisted for analysis.

## Live demo

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m chainlens latest --show-txs 3
```

Example output (real Ethereum mainnet):

```
RPC endpoints (5): https://ethereum.publicnode.com (+fallbacks)
Whale threshold: 100.0 ETH

Latest block number: 26138724
Block hash:      0xcad9e81827cbe1f29ff77fc163855dfe1647a17b8b4a44b209e900273ac4f70b
Timestamp:       2026-10-07T06:29:35+00:00
Miner:           0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97
Gas used:        42,212,924
Gas limit:       60,000,000
Utilization:     70.35%
Base fee:        0.111 gwei
Transactions:    369

First 3 transactions:
  0x588aa442d8553f60...  0 ETH  -> 0x0000000aa2320090...
  0x589036dd0ab3edcf...  0 ETH  -> 0x00000000e91fc5ba...
  0x19eb95b605b456eb...  0 ETH  -> 0x03f34be1bf910116...

Research tool. Not financial advice.
```

## Architecture

```
   CLI (python -m chainlens latest)
         |
         v
  +---------------------------+
  |   EthereumRpcClient       |
  |---------------------------|
  |  try URL[0] -> retries    |
  |  try URL[1] -> retries    |   <- multi-endpoint rotation
  |  try URL[2] -> retries    |
  |  ... (5 public endpoints) |
  +---------------------------+
         |
         v
  [ raw JSON-RPC payload ]
         |
         v
  +---------------------------+
  |   Parsers (blocks.py)     |
  |---------------------------|
  |  parse_block()            |
  |  parse_transactions()     |   <- hex -> int, wei -> Decimal
  |  wei_to_eth()             |
  +---------------------------+
         |
         v
  [ Block, Transaction ]  (Pydantic validated)
```

### Design choices

| Choice | Why |
|--------|-----|
| Multiple RPC endpoints | Public endpoints fail regularly (HTTP 525, timeouts). No SLA. |
| Per-endpoint retries with backoff | Transient failures should not cascade |
| **Rotation** not parallel racing | Simpler, deterministic, easier to observe in logs |
| `Decimal` for ETH values | `float` loses precision on wei-level amounts (18 decimals) |
| `int(x, 0)` for hex parsing | Handles `"0x..."` and `"123"` in one call |
| Pydantic models are frozen | Immutable domain objects prevent accidental mutation |

## Tech stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| Async I/O | `asyncio`, `aiohttp` |
| Validation | `pydantic` v2 |
| Config | `pydantic-settings` |
| Logging | `structlog` |
| Testing | `pytest`, `pytest-asyncio` |
| Quality | `ruff`, `mypy --strict` |
| CI | GitHub Actions on Python 3.12 / 3.13 / 3.14 |

## Project structure

```
chainlens/
├── src/chainlens/
│   ├── config.py         # Settings: RPC URLs, timeout, whale threshold
│   ├── schemas.py        # Block, Transaction, WhaleTransfer, AddressActivity
│   ├── rpc.py            # EthereumRpcClient with multi-endpoint fallback
│   ├── blocks.py         # Parsers: raw RPC payload -> domain models
│   └── __main__.py       # CLI: latest block summary
├── tests/unit/           # 28 unit tests (no network)
├── pyproject.toml
└── README.md
```

## Testing

28 unit tests, all offline (RPC client is mocked):

| Module | Coverage |
|--------|----------|
| `config.py` | 100% |
| `schemas.py` | 95% |
| `blocks.py` | 93% |
| `rpc.py` | 53% |

Note: `rpc.py` has 53% coverage because HTTP error paths are hard to unit test
without a fake server. The 5-endpoint rotation is verified against live mainnet.

## Roadmap

- [x] Phase 1 — RPC client, block parser, CLI, multi-endpoint resilience
- [ ] Phase 2 — Whale detection: filter transactions above threshold
- [ ] Phase 3 — Address activity tracking: net ETH flows for tracked wallets
- [ ] Phase 4 — SQLite persistence for historical block metrics
- [ ] Phase 5 — ERC-20 transfer detection (requires contract ABI decoding)

## Limitations

- Only ETH transfers today; ERC-20 tokens require contract log parsing.
- No historical backfill yet; only fetches the latest block.
- Public RPC endpoints are rate-limited and unreliable. Use a private endpoint
  (Alchemy, Infura) in production.
- `parse_transactions` assumes the RPC was called with `include_txs=True`.

## Disclaimer

Research and educational tool. Not financial advice.

## License

MIT - see [LICENSE](LICENSE) file.

## Author

**Muhammad Rehan Saeed** - [GitHub](https://github.com/rehansaeedjutt-rgb)
