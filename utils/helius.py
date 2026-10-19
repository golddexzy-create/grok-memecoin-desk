"""
Helius helpers – RPC + Parsed Streams oriented utilities.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import requests
from config import settings
from rich.console import Console

console = Console()


def helius_rpc_url() -> str:
    if settings.helius_api_key:
        return f"https://mainnet.helius-rpc.com/?api-key={settings.helius_api_key}"
    return settings.solana_rpc_url


def get_asset(mint: str) -> Optional[Dict[str, Any]]:
    if not settings.helius_api_key:
        return None
    url = f"https://mainnet.helius-rpc.com/?api-key={settings.helius_api_key}"
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "getAsset",
        "params": {"id": mint},
    }
    try:
        r = requests.post(url, json=payload, timeout=12)
        r.raise_for_status()
        return r.json().get("result")
    except Exception as e:
        console.print(f"[red]Helius getAsset error: {e}[/red]")
        return None


def get_token_accounts(owner: str, mint: Optional[str] = None) -> List[Dict]:
    if not settings.helius_api_key:
        return []
    url = f"https://mainnet.helius-rpc.com/?api-key={settings.helius_api_key}"
    params: Dict[str, Any] = {"ownerAddress": owner, "page": 1, "limit": 100}
    if mint:
        params["mint"] = mint
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "getTokenAccounts",
        "params": params,
    }
    try:
        r = requests.post(url, json=payload, timeout=12)
        r.raise_for_status()
        result = r.json().get("result") or {}
        return result.get("token_accounts") or []
    except Exception as e:
        console.print(f"[red]Helius getTokenAccounts error: {e}[/red]")
        return []
