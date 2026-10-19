"""
Birdeye Data API – holder profiles, whales, snipers, dev tags.
Requires BIRDEYE_API_KEY for most useful endpoints.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import requests
from config import settings
from rich.console import Console

console = Console()

BASE = "https://public-api.birdeye.so"


def _headers() -> Dict[str, str]:
    h = {"accept": "application/json", "x-chain": "solana"}
    if settings.birdeye_api_key:
        h["X-API-KEY"] = settings.birdeye_api_key
    return h


def get_holder_profile(mint: str) -> Optional[Dict[str, Any]]:
    if not settings.birdeye_api_key:
        return None
    url = f"{BASE}/token/v1/holder-profile"
    try:
        r = requests.get(url, params={"token_address": mint}, headers=_headers(), timeout=12)
        if r.status_code == 401:
            console.print("[yellow]Birdeye: invalid or missing API key[/yellow]")
            return None
        r.raise_for_status()
        data = r.json()
        return data.get("data") if data.get("success") else data
    except Exception as e:
        console.print(f"[red]Birdeye holder-profile error: {e}[/red]")
        return None


def get_holder_positions(mint: str, labels: str = "dev,sniper,insider,whales") -> List[Dict]:
    if not settings.birdeye_api_key:
        return []
    url = f"{BASE}/token/v1/holder-positions"
    try:
        r = requests.get(
            url,
            params={"token_address": mint, "labels": labels, "limit": 20},
            headers=_headers(),
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("data") or []
    except Exception as e:
        console.print(f"[red]Birdeye holder-positions error: {e}[/red]")
        return []
