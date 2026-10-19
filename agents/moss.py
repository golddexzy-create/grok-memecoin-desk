"""
MOSS – Dev / top holder concentration filter
Primary: Birdeye holder-profile (dev / sniper / bundler tags) when key present.
Fallback: RugCheck topHoldersPct + risk flags.
"""

from agents.base import Candidate, AgentResult, Decision
from utils.apis import get_rugcheck_summary, get_rugcheck_full
from utils.birdeye import get_holder_profile
from config import settings
from rich.console import Console

console = Console()


def run_moss(candidate: Candidate) -> AgentResult:
    profile = get_holder_profile(candidate.mint)
    if profile:
        top10 = profile.get("top10HolderPercent") or profile.get("top10_percent")
        if top10 is not None:
            candidate.top_holders_pct = float(top10)

        tags = profile.get("holderTags") or profile.get("tags") or {}
        dev_pct = None
        if isinstance(tags, dict):
            dev_info = tags.get("dev") or tags.get("developer") or {}
            if isinstance(dev_info, dict):
                dev_pct = dev_info.get("percent") or dev_info.get("pct")
        if dev_pct is not None:
            candidate.dev_holdings_pct = float(dev_pct)

        check_pct = candidate.dev_holdings_pct or candidate.top_holders_pct
        if check_pct is not None and check_pct > settings.max_dev_holdings_pct:
            return AgentResult(
                agent="MOSS",
                decision=Decision.SKIP,
                reason=f"Birdeye concentration {check_pct:.1f}% > {settings.max_dev_holdings_pct}%",
                candidate=candidate,
            )

        return AgentResult(
            agent="MOSS",
            decision=Decision.PASS,
            reason=f"Birdeye holders OK (top\u2248{candidate.top_holders_pct})",
            candidate=candidate,
        )

    summary = get_rugcheck_summary(candidate.mint, settings.rugcheck_api_key)
    if not summary:
        return AgentResult(
            agent="MOSS",
            decision=Decision.SKIP,
            reason="No Birdeye or RugCheck data for holder analysis",
            candidate=candidate,
        )

    top_pct = summary.get("topHoldersPct")
    if top_pct is None:
        full = get_rugcheck_full(candidate.mint, settings.rugcheck_api_key)
        if full:
            top = full.get("topHolders") or []
            if top:
                top_pct = sum(float(h.get("pct") or 0) for h in top[:5])

    candidate.top_holders_pct = float(top_pct) if top_pct is not None else None

    risks = summary.get("risks") or []
    risk_names = [str(r.get("name", "")).lower() for r in risks if isinstance(r, dict)]
    candidate.risk_notes = risk_names

    if candidate.top_holders_pct is not None and candidate.top_holders_pct > settings.max_dev_holdings_pct:
        return AgentResult(
            agent="MOSS",
            decision=Decision.SKIP,
            reason=f"Top holders {candidate.top_holders_pct:.1f}% > {settings.max_dev_holdings_pct}%",
            candidate=candidate,
        )

    bad = {"mint authority", "freeze authority", "high holder concentration", "removable liquidity"}
    if any(b in " ".join(risk_names) for b in bad):
        return AgentResult(
            agent="MOSS",
            decision=Decision.SKIP,
            reason=f"Risk flags: {', '.join(risk_names[:3])}",
            candidate=candidate,
        )

    return AgentResult(
        agent="MOSS",
        decision=Decision.PASS,
        reason=f"Holders OK (top\u2248{candidate.top_holders_pct})",
        candidate=candidate,
    )
