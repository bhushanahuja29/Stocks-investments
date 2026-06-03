# Krypto Desktop Agent

Windows-first desktop assistant with wake-word voice flow and trading-level intelligence.

## Features
- **Type commands** in the text box at the bottom (Enter or Send)
- Wake phrases: `Hey Krypto`, `Crypto`, `Krypto`, `Hey Crypto`
- Greeting: `What can I do for you Bhushan?`
- `analyze btc` command for BTC level distance (fast path, no agent loop)
- `analyze all symbols` — scan Mongo watchlist for symbols near trigger levels
- **Ollama agent** with tools for open-ended market questions (Nifty 50, daily movers, watchlist crypto)
- Morning report for symbols within 2% of trigger levels
- Auto missing-level recovery via screenshot -> OCR -> Mongo push pipeline

## Agent command examples

With Ollama running (`llama3.1:8b` recommended) and the backend on port 8000:

| You say | What happens |
|---------|----------------|
| `indian bank stocks that moved more than 2% today` | **Bank Nifty** scan (`get_index_movers`, index=banknifty) |
| `fin nifty gainers above 3% sorted descending` | **Fin Nifty** gainers only, sorted desc |
| `nifty 50 losers down more than 2%` | **Nifty 50** losers only |
| `list all nifty 50 stocks` | `list_nifty50` → 50 symbols + names |
| `which crypto in my watchlist moved more than 2% today` | `get_watchlist_crypto_movers` (Mongo watchlist only) |
| `analyze btc` | Fast path — existing analyze flow (no agent) |
| `analyze all symbols within 2 percent` | Fast path — near-trigger scan |
| `pin hdfcbank` / `pin btc` | **Pinned overlay** — always-on-top tab on the right edge of the screen |
| `unpin` | Remove the pinned stock widget |
| `get news of tcs june 2026` | Headlines from **Moneycontrol + Yahoo** for that month |
| `news for reliance may 2026` | Same — month/year parsed automatically |

### Stock news (free sources)

- **Yahoo Finance** (`yfinance`) for recent headlines; **Moneycontrol** for Indian NSE names.
- Say a **month and year** (e.g. June 2026, May 2026) to filter articles.
- **Limits:** Yahoo only keeps recent articles — older months may return few or no Yahoo items. Moneycontrol HTML can change; crypto uses Yahoo only.
- API: `GET /api/market/news/{symbol}?year=2026&month=6&market_type=indian_stocks`

### Pin overlay

Say or type **pin** plus a symbol (e.g. `pin reliance`, `stick btc on screen`). Each pin gets its own tab on the **right edge**, stacked vertically (up to 12). **Hover** a tab to expand: live price, today's open, previous close, % change, **TradingView**, and **Unpin** for that symbol.

- **Multiple pins:** `pin tcs` then `pin hdfcbank` — both stay visible.
- **Unpin one:** `unpin tcs`
- **Unpin all:** `unpin all` or plain `unpin` when several are pinned
- **Persistence:** pins are saved to `jarvis_desktop/data/pinned_scrips.json` and restored when Krypto starts.

Quotes refresh every 30 seconds while Krypto is running.

Indices: **Nifty 50**, **Bank Nifty** (~12 banks), **Fin Nifty** (banks + NBFCs). Filters: `min_pct`, `direction` (up/down/any), `sort` (asc/desc), `period` (daily/weekly/monthly).

Backend routes: `GET /api/market/index-movers`, `nifty-movers`, `nifty50`, `indices`, `watchlist-movers`, `quote/{symbol}`, `news/{symbol}`.

## Run
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Start backend API (`crypto_levels_bhushan/backend/main.py`) on port `8000`
3. Start Ollama and pull a model (example: `ollama pull llama3.1:8b`)
4. Run desktop app:
   - `python run_jarvis.py`

## Environment Variables
- `JARVIS_BACKEND_URL` (default `http://192.168.29.31:8000`)
- `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`)
- `OLLAMA_MODEL` (default `llama3.1:8b`)
- `AGENT_MAX_STEPS` (default `5`)

Quick start on Windows:
```powershell
.\start_jarvis.ps1
```
- `KRYPTO_WAKE_WORDS` (comma-separated, default `hey krypto,crypto,krypto,hey crypto`)
- `JARVIS_USER_NAME` (default `Bhushan`)
- `JARVIS_SCHED_HOUR` (default `8`)
- `JARVIS_SCHED_MINUTE` (default `30`)
- `JARVIS_NEAR_TRIGGER_PCT` (default `2.0`)
