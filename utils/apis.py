"""
Lightweight wrappers around free public APIs used by the agents.
- DexScreener: pair / liquidity / volume data
- RugCheck: LP lock, authorities, top holders, risk score
"""

from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
import requests
from rich.console import Console

console = Console()

DEXSCREENER_BASE = "https://api.dexscreener.com"
RUGCHECK_BASE = "https://api.rugcheck.xyz/v1"


def _get(url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, timeout: int = 12) -> Optional[Dict]:
    try:
        r = requests.get(url, params=params, headers=headers or {}, timeout=timeout)
        if r.status_code == 429:
            console.print("[yellow]Rate limited – sleeping 5s[/yellow]")
            time.sleep(5)
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        console.print(f"[red]API error {url}: {e}[/red]")
        return None


def get_token_pairs(chain: str, token_address: str) -> List[Dict[str, Any]]:
    data = _get(f"{DEXSCREENER_BASE}/token-pairs/v1/{chain}/{token_address}")
    if not data:
        return []
    if isinstance(data, list):
        return data
    return data.get("pairs") or []


def search_pairs(query: str) -> List[Dict[str, Any]]:
    data = _get(f"{DEXSCREENER_BASE}/latest/dex/search", params={"q": query})
    if not data:
        return []
    return data.get("pairs") or []


def get_latest_token_profiles(limit: int = 20) -> List[Dict[str, Any]]:
    data = _get(f"{DEXSCREENER_BASE}/token-profiles/latest/v1")
    if not data or not isinstance(data, list):
        return []
    return data[:limit]


def get_rugcheck_summary(mint: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return _get(f"{RUGCHECK_BASE}/tokens/{mint}/report/summary", headers=headers)


def get_rugcheck_full(mint: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return _get(f"{RUGCHECK_BASE}/tokens/{mint}/report", headers=headers)
