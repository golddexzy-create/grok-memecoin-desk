"""
PEPA – Executor + Risk Manager
- Sizes position from current paper (or live) balance
- Records paper trades
- Simple TP / SL tracking (checked on subsequent cycles)
Live execution is deliberately stubbed; enable only after you understand the risks.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone
from agents.base import Candidate, Decision
from config import settings
from rich.console import Console

console = Console()


@dataclass
class Position:
    mint: str
    symbol: str
    entry_price: float
    size_usd: float
    entry_time: datetime
    take_profit: float
    stop_loss: float
    status: str = "open"
    exit_price: Optional[float] = None
    pnl_usd: Optional[float] = None


@dataclass
class Portfolio:
    balance_usd: float
    positions: Dict[str, Position] = field(default_factory=dict)
    closed: List[Position] = field(default_factory=list)
    trades: int = 0
    wins: int = 0

    @property
    def win_rate(self) -> float:
        if self.trades == 0:
            return 0.0
        return 100.0 * self.wins / self.trades


def size_position(balance: float) -> float:
    pct = settings.max_position_pct / 100.0
    return max(1.0, balance * pct)


def open_paper_trade(portfolio: Portfolio, candidate: Candidate) -> Optional[Position]:
    if candidate.mint in portfolio.positions:
        return None
    if candidate.price_usd <= 0:
        return None

    size = size_position(portfolio.balance_usd)
    if size > portfolio.balance_usd * 0.95:
        return None

    entry = candidate.price_usd
    tp = entry * (1 + settings.take_profit_pct / 100)
    sl = entry * (1 - settings.stop_loss_pct / 100)

    pos = Position(
        mint=candidate.mint,
        symbol=candidate.symbol,
        entry_price=entry,
        size_usd=size,
        entry_time=datetime.now(timezone.utc),
        take_profit=tp,
        stop_loss=sl,
    )
    portfolio.positions[candidate.mint] = pos
    portfolio.balance_usd -= size
    portfolio.trades += 1
    console.print(
        f"[green]PEPA BUY[/green] {candidate.symbol} (${size:.2f}) @ ${entry:.8f}  "
        f"TP ${tp:.8f} / SL ${sl:.8f}"
    )
    return pos


def check_exits(portfolio: Portfolio, price_lookup: Dict[str, float]) -> None:
    to_close = []
    for mint, pos in portfolio.positions.items():
        price = price_lookup.get(mint)
        if price is None or price <= 0:
            continue
        if price >= pos.take_profit:
            pnl = pos.size_usd * (price / pos.entry_price - 1)
            pos.exit_price = price
            pos.pnl_usd = pnl
            pos.status = "closed"
            portfolio.balance_usd += pos.size_usd + pnl
            portfolio.wins += 1
            to_close.append(mint)
            console.print(f"[bold green]PEPA TP[/bold green] {pos.symbol} +${pnl:.2f}")
        elif price <= pos.stop_loss:
            pnl = pos.size_usd * (price / pos.entry_price - 1)
            pos.exit_price = price
            pos.pnl_usd = pnl
            pos.status = "closed"
            portfolio.balance_usd += pos.size_usd + pnl
            to_close.append(mint)
            console.print(f"[bold red]PEPA SL[/bold red] {pos.symbol} ${pnl:.2f}")

    for mint in to_close:
        portfolio.closed.append(portfolio.positions.pop(mint))


def run_pepa(portfolio: Portfolio, candidate: Candidate) -> Decision:
    open_paper_trade(portfolio, candidate)
    return Decision.BUY
