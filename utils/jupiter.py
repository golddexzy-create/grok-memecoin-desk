"""
Jupiter Swap API helpers (quote + swap transaction).
Live trading remains gated behind LIVE_TRADING + explicit key handling.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
import requests
from config import settings
from rich.console import Console

console = Console()

QUOTE_URL = "https://lite-api.jup.ag/swap/v1/quote"
SWAP_URL = "https://lite-api.jup.ag/swap/v1/swap"


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if settings.jupiter_api_key:
        h["x-api-key"] = settings.jupiter_api_key
    return h


def get_quote(
    input_mint: str,
    output_mint: str,
    amount: int,
    slippage_bps: int = 100,
) -> Optional[Dict[str, Any]]:
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": amount,
        "slippageBps": slippage_bps,
        "swapMode": "ExactIn",
    }
    try:
        r = requests.get(QUOTE_URL, params=params, headers=_headers(), timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        console.print(f"[red]Jupiter quote error: {e}[/red]")
        return None


def get_swap_transaction(quote_response: Dict[str, Any], user_public_key: str) -> Optional[str]:
    payload = {
        "userPublicKey": user_public_key,
        "quoteResponse": quote_response,
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": True,
    }
    try:
        r = requests.post(SWAP_URL, json=payload, headers=_headers(), timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("swapTransaction")
    except Exception as e:
        console.print(f"[red]Jupiter swap error: {e}[/red]")
        return None
