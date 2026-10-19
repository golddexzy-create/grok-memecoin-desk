from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from enum import Enum


class Decision(str, Enum):
    PASS = "PASS"
    SKIP = "SKIP"
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Candidate:
    mint: str
    symbol: str = ""
    name: str = ""
    pair_address: Optional[str] = None
    liquidity_usd: float = 0.0
    price_usd: float = 0.0
    volume_24h: float = 0.0
    pair_created_at: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    lp_locked: Optional[bool] = None
    lp_locked_pct: Optional[float] = None
    top_holders_pct: Optional[float] = None
    dev_holdings_pct: Optional[float] = None
    rug_score: Optional[int] = None
    risk_notes: list = field(default_factory=list)
    decision: Decision = Decision.PASS
    reason: str = ""


@dataclass
class AgentResult:
    agent: str
    decision: Decision
    reason: str
    candidate: Candidate
