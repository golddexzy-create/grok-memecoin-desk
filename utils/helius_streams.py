"""
Helius Parsed Streams – preferred discovery path for new pump.fun tokens.

Filter: programs 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
instructionNames: create, create_v2
"""

from __future__ import annotations
import asyncio
import json
from typing import Callable, Awaitable, Optional, Dict, List
import websockets
from rich.console import Console
from config import settings
from utils.pump_decoder import PumpCreate

console = Console()

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"


def _account_by_role(decoded: Optional[Dict], role: str) -> Optional[str]:
    if not decoded:
        return None
    accounts = decoded.get("accounts") or []
    for a in accounts:
        if a.get("name") == role:
            return a.get("pubkey")
    return None


def parsed_ix_to_pump_create(tx: Dict, ix: Dict) -> Optional[PumpCreate]:
    decoded = ix.get("decoded") or {}
    args = decoded.get("args") or {}
    name = args.get("name") or ""
    symbol = args.get("symbol") or ""
    uri = args.get("uri") or ""
    mint = _account_by_role(decoded, "mint")
    creator = (
        args.get("creator")
        or _account_by_role(decoded, "creator")
        or _account_by_role(decoded, "user")
    )
    bonding = _account_by_role(decoded, "bondingCurve") or _account_by_role(
        decoded, "bonding_curve"
    )
    if not (name or symbol or mint):
        return None
    return PumpCreate(
        name=str(name),
        symbol=str(symbol),
        uri=str(uri),
        mint=mint,
        bonding_curve=bonding,
        creator=creator,
        signature=tx.get("signature"),
        source="helius_parsed",
    )


async def listen_helius_pump_creates(
    on_create: Callable[[PumpCreate], Awaitable[None]],
    api_key: Optional[str] = None,
) -> None:
    key = api_key or settings.helius_api_key
    if not key:
        raise ValueError("HELIUS_API_KEY required for Parsed Streams")

    urls = [
        f"wss://beta.helius-rpc.com/?api-key={key}",
        f"wss://atlas-mainnet.helius-rpc.com/?api-key={key}",
        f"wss://mainnet.helius-rpc.com/?api-key={key}",
    ]

    subscribe = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "parsedTransactionSubscribe",
        "params": [
            {
                "programs": [PUMP_PROGRAM],
                "instructionNames": ["create", "create_v2"],
                "includeFailed": False,
                "includeCpi": True,
            }
        ],
    }

    url_idx = 0
    while True:
        url = urls[url_idx % len(urls)]
        url_idx += 1
        try:
            console.print("[cyan]Helius Parsed Streams connecting\u2026[/cyan]")
            async with websockets.connect(url, ping_interval=20, max_size=2**23) as ws:
                await ws.send(json.dumps(subscribe))
                console.print(
                    "[green]Subscribed to Helius Parsed Streams "
                    "(create / create_v2)[/green]"
                )

                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue

                    if msg.get("error"):
                        console.print(f"[red]Helius stream error: {msg['error']}[/red]")
                        continue

                    if msg.get("id") == 1 and isinstance(msg.get("result"), int):
                        console.print(f"[dim]subscription id={msg['result']}[/dim]")
                        continue

                    if msg.get("method") != "parsedTransactionNotification":
                        continue

                    params = msg.get("params") or {}
                    result = params.get("result") or {}
                    value = result.get("value") or result
                    tx = value.get("transaction") or value
                    instructions: List[Dict] = value.get("instructions") or []
                    matched = value.get("matchedIndexes") or list(range(len(instructions)))

                    for i in matched:
                        if i >= len(instructions):
                            continue
                        ix = instructions[i]
                        name = (ix.get("instructionName") or ix.get("name") or "").lower()
                        if name not in ("create", "create_v2"):
                            continue
                        create = parsed_ix_to_pump_create(tx, ix)
                        if create:
                            console.print(
                                f"[bold green]HELIUS NEW[/bold green] "
                                f"{create.symbol or '?'} ({create.name or ''}) "
                                f"mint={create.mint or '?'} "
                                f"creator={create.creator or '?'}"
                            )
                            await on_create(create)

        except Exception as e:
            console.print(f"[red]Helius stream error: {e} – reconnect in 4s[/red]")
            await asyncio.sleep(4)
