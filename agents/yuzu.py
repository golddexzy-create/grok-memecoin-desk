"""
YUZU – LP Lock / Burn filter
Uses RugCheck summary (lpLocked + locked %).
"""

from agents.base import Candidate, AgentResult, Decision
from utils.apis import get_rugcheck_summary
from config import settings
from rich.console import Console

console = Console()


def run_yuzu(candidate: Candidate) -> AgentResult:
    if not settings.require_lp_locked:
        candidate.lp_locked = True
        return AgentResult(
            agent="YUZU",
            decision=Decision.PASS,
            reason="LP lock check disabled",
            candidate=candidate,
        )

    summary = get_rugcheck_summary(candidate.mint, settings.rugcheck_api_key)
    if not summary:
        return AgentResult(
            agent="YUZU",
            decision=Decision.SKIP,
            reason="Could not fetch RugCheck data (rate limit or missing)",
            candidate=candidate,
        )

    lp_locked = summary.get("lpLocked")
    locked_pct = summary.get("lpLockedPct") or summary.get("liquidity", {}).get("lockedPct")

    candidate.lp_locked = bool(lp_locked)
    candidate.lp_locked_pct = float(locked_pct) if locked_pct is not None else None
    candidate.rug_score = summary.get("score")

    if lp_locked is True or (candidate.lp_locked_pct and candidate.lp_locked_pct >= settings.min_lp_locked_pct):
        return AgentResult(
            agent="YUZU",
            decision=Decision.PASS,
            reason=f"LP locked (pct={candidate.lp_locked_pct})",
            candidate=candidate,
        )

    return AgentResult(
        agent="YUZU",
        decision=Decision.SKIP,
        reason=f"LP not sufficiently locked (locked={lp_locked}, pct={candidate.lp_locked_pct})",
        candidate=candidate,
    )
