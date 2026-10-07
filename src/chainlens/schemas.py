"""Pydantic models for on-chain data."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# 1 ETH = 10^18 wei. We use Decimal for exact conversion.
WEI_PER_ETH = Decimal(10) ** 18


def wei_to_eth(wei: int | str) -> Decimal:
    """Convert wei (int or hex string) to ETH as Decimal.

    Uses int(x, 0) so both "0x..." (hex) and plain decimal strings work.
    """
    wei_int = int(wei, 0) if isinstance(wei, str) else wei
    return Decimal(wei_int) / WEI_PER_ETH


class Block(BaseModel):
    """A summary of a single Ethereum block."""

    model_config = ConfigDict(frozen=True)

    number: int = Field(..., ge=0)
    hash: str
    parent_hash: str
    timestamp: datetime
    miner: str
    gas_used: int = Field(..., ge=0)
    gas_limit: int = Field(..., gt=0)
    base_fee_per_gas: int | None = Field(default=None, ge=0)
    transaction_count: int = Field(..., ge=0)

    @property
    def gas_utilization(self) -> float:
        """Fraction of gas limit consumed by this block (0.0 to 1.0)."""
        if self.gas_limit == 0:
            return 0.0
        return self.gas_used / self.gas_limit


class Transaction(BaseModel):
    """A single transaction from a block."""

    model_config = ConfigDict(frozen=True)

    hash: str
    block_number: int = Field(..., ge=0)
    from_address: str
    to_address: str | None = None
    value_wei: int = Field(..., ge=0)
    gas: int = Field(..., ge=0)
    gas_price: int | None = Field(default=None, ge=0)
    nonce: int = Field(..., ge=0)

    @property
    def value_eth(self) -> Decimal:
        """Transaction value in ETH (exact Decimal)."""
        return wei_to_eth(self.value_wei)


class WhaleTransfer(BaseModel):
    """A transfer above the configured whale threshold."""

    model_config = ConfigDict(frozen=True)

    tx_hash: str
    block_number: int = Field(..., ge=0)
    from_address: str
    to_address: str
    value_eth: Decimal = Field(..., gt=0)
    timestamp: datetime


class AddressActivity(BaseModel):
    """Activity summary for a single address over an observation window."""

    model_config = ConfigDict(frozen=True)

    address: str
    tx_count_sent: int = Field(default=0, ge=0)
    tx_count_received: int = Field(default=0, ge=0)
    total_eth_sent: Decimal = Field(default=Decimal(0), ge=0)
    total_eth_received: Decimal = Field(default=Decimal(0), ge=0)

    @property
    def net_flow_eth(self) -> Decimal:
        """Net ETH flow (positive = accumulation, negative = distribution)."""
        return self.total_eth_received - self.total_eth_sent
