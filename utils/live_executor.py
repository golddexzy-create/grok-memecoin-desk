"""
LIVE EXECUTION MODULE – HEAVILY GATED

This module is intentionally incomplete and conservative.
It will NOT sign or send any transaction unless:
  1. LIVE_TRADING=true in .env
  2. PRIVATE_KEY is present
  3. ALLOW_LIVE_SEND=true (extra explicit flag)
  4. You call the functions yourself after reviewing the unsigned tx

Even then, you should always simulate first and use limited funds.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from config import settings
from utils.jupiter import get_quote, get_swap_transaction
from rich.console import Console
import os

console = Console()

SOL_MINT = "So11111111111111111111111111111111111111112"


def is_live_allowed() -> bool:
    return (
        settings.live_trading
        and bool(settings.private_key)
        and os.getenv("ALLOW_LIVE_SEND", "false").lower() == "true"
    )


def prepare_buy_quote(
    token_mint: str,
    amount_sol_lamports: int,
    slippage_bps: int = 150,
) -> Optional[Dict[str, Any]]:
    if not settings.live_trading:
        console.print("[yellow]LIVE_TRADING is false – quote only for inspection[/yellow]")
    return get_quote(
        input_mint=SOL_MINT,
        output_mint=token_mint,
        amount=amount_sol_lamports,
        slippage_bps=slippage_bps,
    )


def get_unsigned_buy_tx(
    token_mint: str,
    amount_sol_lamports: int,
    user_pubkey: str,
    slippage_bps: int = 150,
) -> Optional[str]:
    quote = prepare_buy_quote(token_mint, amount_sol_lamports, slippage_bps)
    if not quote:
        return None
    return get_swap_transaction(quote, user_pubkey)


def warn_and_block():
    console.print(
        "[bold red]LIVE SEND IS BLOCKED[/bold red]\n"
        "To enable (at your own risk):\n"
        "  LIVE_TRADING=true\n"
        "  PRIVATE_KEY=...\n"
        "  ALLOW_LIVE_SEND=true\n"
        "Even then, this module does not auto-sign. You must review and sign yourself."
    )
