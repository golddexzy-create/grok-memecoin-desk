#!/usr/bin/env python3
"""
Standalone real-time discovery runner.
Prefer Helius Parsed Streams when key is present.

Usage:
  python run_discovery.py
"""

import asyncio
from rich.console import Console
from agents.kiwi import start_preferred_discovery
from agents.base import Candidate

console = Console()


async def on_new(c: Candidate):
    console.print(
        f"[bold]DISCOVERY[/bold] {c.symbol} ({c.name}) mint={c.mint} "
        f"source={c.raw.get('source') or c.raw.get('pump_create', {}).get('source')}"
    )


async def main():
    console.print("[cyan]Starting preferred discovery path…[/cyan]")
    await start_preferred_discovery(on_new)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
