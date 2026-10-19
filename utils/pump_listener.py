"""
Real-time pump.fun new-token listener using logsSubscribe + improved IDL-style decoding.

Program ID: 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
"""

from __future__ import annotations
import asyncio
import json
from typing import Callable, Awaitable, Optional
import websockets
from rich.console import Console
from utils.helius import helius_rpc_url
from utils.pump_decoder import decode_from_logs, is_create_log, PumpCreate, PUMP_PROGRAM

console = Console()


async def listen_pump_creates(
    on_create: Callable[[PumpCreate], Awaitable[None]],
    ws_url: Optional[str] = None,
) -> None:
    if not ws_url:
        http = helius_rpc_url()
        if "helius-rpc.com" in http:
            ws_url = http.replace("https://", "wss://")
        else:
            ws_url = http.replace("https://", "wss://").replace("http://", "ws://")

    console.print(f"[cyan]pump.fun listener connecting → {ws_url[:70]}...[/cyan]")

    sub_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "logsSubscribe",
        "params": [
            {"mentions": [PUMP_PROGRAM]},
            {"commitment": "processed"},
        ],
    }

    while True:
        try:
            async with websockets.connect(ws_url, ping_interval=20, max_size=2**22) as ws:
                await ws.send(json.dumps(sub_req))
                console.print("[green]Subscribed to pump.fun logs (Create decoding active)[/green]")

                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue
                    if "params" not in msg:
                        continue
                    result = msg["params"].get("result") or {}
                    value = result.get("value") or {}
                    logs = value.get("logs") or []
                    sig = value.get("signature")

                    if not is_create_log(logs):
                        continue

                    decoded = decode_from_logs(logs, signature=sig)
                    if decoded is None:
                        continue

                    console.print(
                        f"[bold green]NEW PUMP[/bold green] "
                        f"{decoded.symbol or '?'} ({decoded.name or 'unnamed'}) "
                        f"mint={decoded.mint or 'pending'} "
                        f"creator={decoded.creator or '?'} "
                        f"[{decoded.source}]"
                    )
                    await on_create(decoded)

        except Exception as e:
            console.print(f"[red]Listener error: {e} – reconnecting in 5s[/red]")
            await asyncio.sleep(5)


def run_listener_forever(on_create: Callable[[PumpCreate], Awaitable[None]]):
    asyncio.run(listen_pump_creates(on_create))
