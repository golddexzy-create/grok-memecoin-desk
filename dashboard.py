"""
Simple Streamlit dashboard inspired by the original Grok Bot green UI.
Run with: streamlit run dashboard.py

Shows live paper balance, positions, agent status, and recent activity.
"""

from __future__ import annotations
import streamlit as st
import time
from pathlib import Path
import json
from datetime import datetime

st.set_page_config(
    page_title="Grok Memecoin Desk",
    page_icon="\U0001F7E2",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { background-color: #0a0f0a; color: #e0ffe0; }
    h1, h2, h3 { color: #39ff14 !important; }
    .metric-card {
        background: linear-gradient(135deg, #0d1a0d, #122212);
        border: 1px solid #1f3d1f;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .agent-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        margin: 0.15rem;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .pass { background: #0d3d0d; color: #39ff14; border: 1px solid #39ff14; }
    .skip { background: #2a1a00; color: #ffaa00; border: 1px solid #ffaa00; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("\U0001F7E2 Grok Memecoin Desk")
st.caption("Paper trading dashboard \u00b7 inspired by the original 6-agent Grok Bot test")

with st.sidebar:
    st.header("Controls")
    auto_refresh = st.checkbox("Auto-refresh (10s)", value=True)
    st.markdown("---")
    st.markdown("**Agents**")
    agents = ["KIWI", "FERN", "YUZU", "MOSS", "JOLT", "PEPA"]
    for a in agents:
        st.markdown(f'<span class="agent-pill pass">{a}</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.info("Run `python main.py` in another terminal to feed live paper activity.\n\nThis dashboard reads from `data/status.json` when present.")

status_path = Path("data/status.json")
status = {
    "balance": 64.0,
    "open_positions": 0,
    "closed_trades": 0,
    "win_rate": 0.0,
    "tasks": 0,
    "skips": 0,
    "cycle": 0,
    "mode": "PAPER",
    "positions": [],
    "recent_log": [],
    "updated": None,
}

if status_path.exists():
    try:
        status = json.loads(status_path.read_text())
    except Exception:
        pass

col1, col2, col3, col4 = st.columns(4)
col1.metric("Paper Balance", f"${status.get('balance', 64):,.2f}")
col2.metric("Open Positions", status.get("open_positions", 0))
col3.metric("Closed Trades", status.get("closed_trades", 0))
col4.metric("Win Rate", f"{status.get('win_rate', 0):.1f}%")

st.markdown("---")

st.subheader("Open Positions")
positions = status.get("positions") or []
if positions:
    for p in positions:
        st.markdown(
            f"**{p.get('symbol', '?')}** \u00b7 size ${p.get('size_usd', 0):.2f} \u00b7 "
            f"entry ${p.get('entry_price', 0):.8f} \u00b7 "
            f"TP ${p.get('take_profit', 0):.8f} / SL ${p.get('stop_loss', 0):.8f}"
        )
else:
    st.write("No open positions")

st.markdown("---")

st.subheader("Recent Activity")
log = status.get("recent_log") or ["Waiting for main.py to write status\u2026"]
for line in log[-15:]:
    st.text(line)

st.markdown("---")
st.caption(f"Last update: {status.get('updated') or 'never'} \u00b7 Cycle {status.get('cycle', 0)}")

if auto_refresh:
    time.sleep(10)
    st.rerun()
