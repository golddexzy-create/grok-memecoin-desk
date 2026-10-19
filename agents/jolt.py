"""
JOLT – Whale / momentum + smart-money filter
Uses Birdeye holder tags (whales, snipers, smart_trader) when available,
falls back to volume/liquidity heuristic.
"""

from __future__ import annotations
import time
from agents.base import Candidate, AgentResult, Decision
from utils.birdeye import get_holder_positions
from config import settings
from rich.console import Console

console = Console()


def run_jolt(candidate: Candidate) -> AgentResult:
    if settings.birdeye_api_key:
        positions = get_holder_positions(
            candidate.mint, labels="whales,smart_trader,sniper"
        )
        whale_count = 0
        smart_count = 0
        for p in positions:
            labels = [str(l).lower() for l in (p.get("labels") or [])]
            if "whales" in labels or "whale" in labels:
                whale_count += 1
            if "smart_trader" in labels or "smart" in labels:
                smart_count += 1

        if whale_count > 0 or smart_count > 0:
            return AgentResult(
                agent="JOLT",
                decision=Decision.PASS,
                reason=f"Birdeye signal: {whale_count} whale(s), {smart_count} smart",
                candidate=candidate,
            )

        liq = max(candidate.liquidity_usd, 1)
        ratio = candidate.volume_24h / liq
        if ratio < 0.15:
            return AgentResult(
                agent="JOLT",
                decision=Decision.SKIP,
                reason="No whale/smart tags + low vol/liq",
                candidate=candidate,
            )

    liq = max(candidate.liquidity_usd, 1)
    vol = candidate.volume_24h
    ratio = vol / liq

    age_hours = None
    if candidate.pair_created_at:
        age_ms = int(time.time() * 1000) - candidate.pair_created_at
        age_hours = age_ms / (1000 * 3600)

    if ratio < 0.25 and (age_hours is None or age_hours < 1.5):
        return AgentResult(
            agent="JOLT",
            decision=Decision.SKIP,
            reason=f"Low activity (vol/liq={ratio:.2f}, age\u2248{age_hours}h)",
            candidate=candidate,
        )

    return AgentResult(
        agent="JOLT",
        decision=Decision.PASS,
        reason=f"Activity OK (vol/liq={ratio:.2f})",
        candidate=candidate,
    )
