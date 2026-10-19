"""
KIWI – Scanner / Discovery

Priority order when HELIUS_API_KEY is set:
  1. Helius Parsed Streams (create / create_v2)  ← preferred, lowest latency, fully decoded
  2. logsSubscribe + local Borsh decoder         ← free fallback
  3. DexScreener profiles / search               ← always available polling path

The polling function `run_kiwi()` remains the default used by main.py.
Use `start_preferred_discovery()` for the real-time path.
"""

from __future__ import annotations
from typing import List, Optional
from agents.base import Candidate
from utils.apis import get_latest_token_profiles, search_pairs, get_token_pairs
from utils.pump_decoder import PumpCreate
from config import settings
from rich.console import Console

console = Console()


def pump_create_to_candidate(pc: PumpCreate) -> Candidate:
    return Candidate(
        mint=pc.mint or "",
        symbol=pc.symbol or "?",
        name=pc.name or "",
        pair_address=None,
        liquidity_usd=0.0,
        price_usd=0.0,
        volume_24h=0.0,
        pair_created_at=None,
        raw={"pump_create": pc.__dict__, "source": pc.source},
    )


def run_kiwi(max_candidates: int | None = None) -> List[Candidate]:
    max_candidates = max_candidates or settings.max_candidates_per_cycle
    candidates: List[Candidate] = []

    profiles = get_latest_token_profiles(limit=40)
    for p in profiles:
        chain = (p.get("chainId") or "").lower()
        if chain != "solana":
            continue
        mint = p.get("tokenAddress")
        if not mint:
            continue
        pairs = get_token_pairs("solana", mint)
        if not pairs:
            continue
        best = max(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd") or 0))
        liq = float(best.get("liquidity", {}).get("usd") or 0)
        price = float(best.get("priceUsd") or 0)
        vol = float(best.get("volume", {}).get("h24") or 0)
        created = best.get("pairCreatedAt")
        base = best.get("baseToken") or {}
        candidates.append(
            Candidate(
                mint=mint,
                symbol=base.get("symbol") or p.get("symbol") or "?",
                name=base.get("name") or p.get("name") or "",
                pair_address=best.get("pairAddress"),
                liquidity_usd=liq,
                price_usd=price,
                volume_24h=vol,
                pair_created_at=created,
                raw={"profile": p, "pair": best},
            )
        )
        if len(candidates) >= max_candidates:
            break

    if len(candidates) < max_candidates // 2:
        extra = search_pairs("SOL")
        for pair in extra[:20]:
            if (pair.get("chainId") or "").lower() != "solana":
                continue
            base = pair.get("baseToken") or {}
            mint = base.get("address")
            if not mint or any(c.mint == mint for c in candidates):
                continue
            liq = float(pair.get("liquidity", {}).get("usd") or 0)
            if liq < 1000:
                continue
            candidates.append(
                Candidate(
                    mint=mint,
                    symbol=base.get("symbol") or "?",
                    name=base.get("name") or "",
                    pair_address=pair.get("pairAddress"),
                    liquidity_usd=liq,
                    price_usd=float(pair.get("priceUsd") or 0),
                    volume_24h=float(pair.get("volume", {}).get("h24") or 0),
                    pair_created_at=pair.get("pairCreatedAt"),
                    raw={"pair": pair},
                )
            )
            if len(candidates) >= max_candidates:
                break

    console.print(f"[cyan]KIWI[/cyan] polled → {len(candidates)} candidates")
    return candidates


async def start_preferred_discovery(on_candidate) -> None:
    async def _handle_pump(pc: PumpCreate):
        if not pc.mint:
            return
        cand = pump_create_to_candidate(pc)
        await on_candidate(cand)

    if settings.helius_api_key:
        console.print("[green]KIWI using Helius Parsed Streams (preferred)[/green]")
        from utils.helius_streams import listen_helius_pump_creates
        await listen_helius_pump_creates(_handle_pump)
    else:
        console.print(
            "[yellow]No HELIUS_API_KEY – falling back to logsSubscribe + Borsh decoder[/yellow]"
        )
        from utils.pump_listener import listen_pump_creates
        await listen_pump_creates(_handle_pump)
