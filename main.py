#!/usr/bin/env python3
"""
Grok Memecoin Desk – main loop (paper trading by default)
Writes status to data/status.json so the Streamlit dashboard can display it live.
"""

from __future__ import annotations
import time
import json
from pathlib import Path
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config import settings
from agents.kiwi import run_kiwi
from agents.fern import run_fern
from agents.yuzu import run_yuzu
from agents.moss import run_moss
from agents.jolt import run_jolt
from agents.pepa import Portfolio, run_pepa, check_exits
from agents.base import Decision
from utils.apis import get_token_pairs

console = Console()
STATUS_FILE = Path("data/status.json")
RECENT_LOG: list[str] = []


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    RECENT_LOG.append(line)
    if len(RECENT_LOG) > 40:
        RECENT_LOG.pop(0)
    console.print(msg)


def write_status(portfolio: Portfolio, cycle: int, tasks: int, skips: int):
    payload = {
        "balance": round(portfolio.balance_usd, 2),
        "open_positions": len(portfolio.positions),
        "closed_trades": len(portfolio.closed),
        "win_rate": round(portfolio.win_rate, 1),
        "tasks": tasks,
        "skips": skips,
        "cycle": cycle,
        "mode": "LIVE" if settings.live_trading else "PAPER",
        "positions": [
            {
                "mint": p.mint,
                "symbol": p.symbol,
                "size_usd": p.size_usd,
                "entry_price": p.entry_price,
                "take_profit": p.take_profit,
                "stop_loss": p.stop_loss,
            }
            for p in portfolio.positions.values()
        ],
        "recent_log": RECENT_LOG[-20:],
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(payload, indent=2))


def print_status(portfolio: Portfolio, cycle: int, tasks: int, skips: int):
    table = Table(title=f"Grok Memecoin Desk  ·  Cycle {cycle}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Paper Balance", f"${portfolio.balance_usd:,.2f}")
    table.add_row("Open Positions", str(len(portfolio.positions)))
    table.add_row("Closed Trades", str(len(portfolio.closed)))
    table.add_row("Win Rate", f"{portfolio.win_rate:.1f}%")
    table.add_row("Tasks this cycle", str(tasks))
    table.add_row("Skips this cycle", str(skips))
    console.print(table)
    write_status(portfolio, cycle, tasks, skips)


def enrich_price(mint: str) -> float:
    pairs = get_token_pairs("solana", mint)
    if not pairs:
        return 0.0
    best = max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd") or 0))
    return float(best.get("priceUsd") or 0)


def main():
    console.print(
        Panel.fit(
            "[bold green]Grok Memecoin Desk[/bold green]\n"
            f"Mode: {'[red]LIVE[/red]' if settings.live_trading else '[yellow]PAPER[/yellow]'}\n"
            f"Start balance: ${settings.paper_starting_balance:.2f}\n"
            "Filters: liquidity · LP lock · dev holdings · whale/activity\n"
            "Dashboard: streamlit run dashboard.py",
            title="Starting",
        )
    )

    if settings.live_trading:
        console.print(
            "[bold red]LIVE TRADING FLAG IS SET[/bold red]\n"
            "The main loop still only does PAPER trades.\n"
            "Real sends require utils/live_executor.py + ALLOW_LIVE_SEND=true + manual review."
        )

    portfolio = Portfolio(balance_usd=settings.paper_starting_balance)
    cycle = 0
    total_tasks = 0

    while True:
        cycle += 1
        tasks = 0
        skips = 0

        candidates = run_kiwi()
        tasks += len(candidates)
        log(f"[cyan]KIWI[/cyan] → {len(candidates)} candidates")

        passed = []
        for c in candidates:
            r = run_fern(c)
            tasks += 1
            if r.decision == Decision.SKIP:
                skips += 1
                log(f"  [dim]SKIP {c.symbol}[/dim] – FERN: {r.reason}")
                continue

            r = run_yuzu(c)
            tasks += 1
            if r.decision == Decision.SKIP:
                skips += 1
                log(f"  [dim]SKIP {c.symbol}[/dim] – YUZU: {r.reason}")
                continue

            r = run_moss(c)
            tasks += 1
            if r.decision == Decision.SKIP:
                skips += 1
                log(f"  [dim]SKIP {c.symbol}[/dim] – MOSS: {r.reason}")
                continue

            r = run_jolt(c)
            tasks += 1
            if r.decision == Decision.SKIP:
                skips += 1
                log(f"  [dim]SKIP {c.symbol}[/dim] – JOLT: {r.reason}")
                continue

            passed.append(c)
            log(f"  [green]PASS {c.symbol}[/green] – ready for PEPA")

        for c in passed:
            run_pepa(portfolio, c)
            tasks += 1

        if portfolio.positions:
            prices = {mint: enrich_price(mint) for mint in list(portfolio.positions.keys())}
            check_exits(portfolio, prices)

        total_tasks += tasks
        print_status(portfolio, cycle, tasks, skips)
        log(f"[dim]Total tasks so far: {total_tasks}[/dim]")

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped by user.[/yellow]")
