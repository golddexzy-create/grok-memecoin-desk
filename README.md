# Grok Memecoin Desk (Full Real-API Edition)

6-agent Solana memecoin desk inspired by the public Grok Bot test.

## What is fully built

| Piece | Status |
|-------|--------|
| **KIWI** (scanner) | **Helius Parsed Streams** (preferred) → logsSubscribe + Borsh fallback → DexScreener |
| **FERN** (liquidity) | DexScreener USD liquidity |
| **YUZU** (LP lock) | RugCheck |
| **MOSS** (dev holdings) | Birdeye holder profile + RugCheck fallback |
| **JOLT** (whale / activity) | Birdeye whales/smart_trader + volume heuristic |
| **PEPA** (executor) | Paper trades + TP/SL exits |
| Status feed | `data/status.json` every cycle |
| Green dashboard | Streamlit (`dashboard.py`) |
| Live path | Gated (`utils/live_executor.py`) – unsigned Jupiter tx only |

## Safety

- **Default = PAPER only.** Live signing is blocked by design.
- Live requires `LIVE_TRADING=true` + `PRIVATE_KEY` + `ALLOW_LIVE_SEND=true`.
- Code never auto-signs. You must review and sign yourself.
- Memecoins are extremely high risk.

## Setup

```bash
git clone https://github.com/golddexzy-create/grok-memecoin-desk.git
cd grok-memecoin-desk
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add HELIUS_API_KEY, BIRDEYE_API_KEY, JUPITER_API_KEY
# Keep LIVE_TRADING=false
```

## Run

```bash
# Paper trading loop
python main.py

# Dashboard (another terminal)
streamlit run dashboard.py

# Real-time discovery (Helius preferred)
python run_discovery.py
```

## License

MIT
