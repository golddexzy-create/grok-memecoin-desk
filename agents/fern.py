"""
FERN – Liquidity filter
Requires “serious” liquidity (configurable USD threshold).
"""

from agents.base import Candidate, AgentResult, Decision
from config import settings
from rich.console import Console

console = Console()


def run_fern(candidate: Candidate) -> AgentResult:
    liq = candidate.liquidity_usd
    min_liq = settings.min_liquidity_usd

    if liq >= min_liq:
        return AgentResult(
            agent="FERN",
            decision=Decision.PASS,
            reason=f"Liquidity ${liq:,.0f} ≥ ${min_liq:,.0f}",
            candidate=candidate,
        )
    return AgentResult(
        agent="FERN",
        decision=Decision.SKIP,
        reason=f"Liquidity too low: ${liq:,.0f} < ${min_liq:,.0f}",
        candidate=candidate,
    )
