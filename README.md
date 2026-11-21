# Mock Stock Challenge — the full game

A 6-week, $50,000 mock stock challenge, run Oct 12 – Nov 20, 2026.
Long-only US stocks/ETFs, fractional shares, no options/shorting/leverage,
no transaction costs, dividends ignored, benchmark S&P 500. No real money
ever moved — bragging rights only.

**Final result: $42,457.13, −15.09% vs the $50k start.**
S&P 500 was −11.54% over the same stretch, so the book trailed the
benchmark by 3.55pp. Best holding LLY (+14.04%), worst NVDA (−44.67%).
The full story is in `final-report.md`.

## What's in here

| Path | What it is |
|---|---|
| `RULES.md` | The rulebook, as agreed Oct 10, 2026 |
| `portfolio.json` | Final portfolio: positions, cost basis, fills, final valuation |
| `trades.log` | Every mock trade, timestamped, with fill price + source |
| `final-report.md` | Final report: every trade, final positions, ROI, benchmark, narrative |
| `design-spec/stock-challenge-design-spec.md` | Design spec of how the challenge was run, converted from the 17-page PDF (see below) |
| `code/` | Runnable Python reimplementation (stdlib only, no pip) |
| `HOW-I-RAN-IT.md` | How the game was actually operated, step by step |

## How to run the code

```bash
cd code
python3 run_checkin.py
```

That values the final portfolio against the latest closes and prints the
check-in: value, ROI, S&P 500 comparison, best/worst holding, and the
rules agent's ideas. To start a fresh game, reset `../portfolio.json`
(cash $50,000, empty positions) — see `code/README-pi.md`. Optional:
`llm_agent.py` adds a manager's note from a local LLM via Ollama;
`cron.example` schedules the weekly Saturday check-in.

Verified Nov 21, 2026: `run_checkin.py` reproduces the final score
exactly — $42,457.13, −15.09%.

## One honest note — what this code is and isn't

The `code/` folder is a faithful reimplementation of the game's logic:
same rules, same portfolio math, same check-in loop. It is **not** the
exact code that ran the challenge, because there wasn't a single codebase
running it. The challenge was operated by an AI assistant (YSA) through
scheduled jobs: it pulled closing prices (Finnhub, cross-checked against
published reports), computed the book, wrote the check-ins, and proposed
trades that only executed after the user's explicit approval. The
reasoning, news-gathering, and judgment calls lived in that loop, not in
a script. `HOW-I-RAN-IT.md` and the design spec PDF document that loop
in full — that, plus this code, is the complete game.
