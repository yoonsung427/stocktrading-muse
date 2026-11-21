# How the game was actually run

This is the operational record: what was set up, what ran on what
schedule, where prices came from, and how decisions were made. The
design spec (`design-spec/stock-challenge-design-spec.md`, converted from the 17-page PDF)
covers the same ground in full detail, including the week-1 construction
story and the rebalance decision trace. This file is the short version.

## The setup

- **Files (the source of truth):** `portfolio.json` — positions, shares,
  cost basis, fill prices/times, cash; `trades.log` — every mock trade,
  timestamped, with fill price and source. Both live in
  `~/workspace/mock-stock-challenge/` in the original setup.
- **Rules:** `RULES.md` — long-only, fractional shares OK, no
  options/shorting/leverage/margin, no transaction costs, dividends
  ignored, cash can't go negative, all fills timestamped and never
  backdated, benchmark S&P 500.
- **Roles:** YSA (the AI assistant) was the contestant and portfolio
  manager; the user rooted for YSA against friends' portfolios. YSA
  could propose trades but never execute one without the user's explicit
  approval.

## The schedule

- **Opening fills:** Mon Oct 12, 2026, market open. 8 staged orders
  ($49,999.99 invested, $0.01 cash). Fills used official open prices.
- **Weekly check-ins:** every Saturday ~9am PT, using Friday closes —
  weeks 1–5 (Oct 17, Oct 24, Oct 31, Nov 7, Nov 14), plus an eve-of-final
  snapshot Fri Nov 20 morning.
- **Earnings recaps:** short recaps ~6:30pm PT on earnings evenings for
  GE, META, MSFT, LLY, AMZN, XOM, NVDA, each with the dollar impact on
  the mock leg, plus a Wed 8am morning-after check for NVDA.
- **Final valuation:** Fri Nov 20, 2026 close; final report Sat Nov 21,
  9am PT. That was the last scheduled run — no further check-ins.

## Where prices came from (and one disclosure)

The rulebook names Finnhub as the price source, and most closes were
verified live via Finnhub and cross-checked against published data
(MarketBeat, stockanalysis.com, etc.). Disclosure from the design spec:
**five of the eight opening fills were recorded from dated published
reports** (MarketBeat, American Banking News, Zolmax) rather than a live
Finnhub quote at the time — each is sourced in `trades.log`. No fill was
ever backdated: opening orders filled at the Monday open, never at
Friday's close.

## How decisions were made

The loop was: perceive → reason → suggest → approve → execute.

1. **Perceive:** pull closes, compute per-position P&L, ROI, benchmark gap.
2. **Reason:** news + earnings + price action, written up in the check-in.
3. **Suggest:** YSA could float a rebalance idea (e.g. the week-3 idea to
   trim LLY after +20% and add to NVDA) — but a suggestion was never a
   trade.
4. **Approve:** the user approved or declined in chat. The only approved
   trade of the whole game was the Oct 19 rebalance: sell half the XOM
   (14.6190 sh @ $178.45, +$108.76 realized gain) into an oil spike and
   buy NVDA (11.9616 sh @ $218.095) with the proceeds. Fills executed at
   the Mon Oct 19 official open.
5. **Execute + log:** the fill was recorded in `portfolio.json` and
   `trades.log` with timestamp, price, and source.

Everything else was hold-and-report. That Oct 19 rebalance is also the
honest post-mortem: it doubled down on the exact holding that then fell
apart — NVDA went from $229.28 at the open to $125.53 at the final close,
−44.67% on the leg, ~75% of the total loss.

## The ending

The final week was a broad selloff: the portfolio fell $5,214.19 from the
Fri Nov 13 close ($47,671.32) to the Fri Nov 20 close ($42,457.13),
including −$2,174.75 on the final day alone, when NVDA fell 14.01% on a
Reuters report that SEC enforcement staff are examining potential
accounting issues at Nvidia (a reported examination, not a finding).
The S&P 500 entered correction territory after a seven-day losing streak.
Only LLY (+14.04%) and GE (+0.60%) finished green vs fill.

## What the Pi code maps to

`code/` reproduces the arithmetic half of the loop — prices, valuation,
ROI, benchmark math, and the rules agent's suggestions — in stdlib-only
Python so it runs on a Raspberry Pi with zero installs. What it can't
reproduce is the other half: live news judgment, earnings interpretation,
and the approval conversation. That's why the design spec and this file
travel with the code — together they're the whole game.
