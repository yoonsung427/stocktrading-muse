# Running the mock stock challenge in OpenClaw

How YSA operated the game — written so a friend can run the same thing in
OpenClaw. One honest note: this is an operating manual, not a program.
The judgment calls were made by an agent, in language, over evidence it
had just gathered. You can recreate the setup; you can't download the
judgment.

## The game in one paragraph

$50,000 of virtual cash, six weeks, long-only US stocks and ETFs,
fractional shares allowed, no options / shorting / leverage / margin,
no transaction costs, dividends ignored, benchmark S&P 500. Highest ROI
at the final Friday close wins; bragging rights only. YSA (the Muse
agent) managed one contestant portfolio against the user's friends, who
ran their own. All state lived in plain files; every timed action was a
separate scheduled job; no trade executed without the user's explicit
approval in chat. Final result, Oct 12 – Nov 20, 2026: **$42,457.13,
−15.09%**, trailing the S&P 500 (−11.54%) by ~3.55pp. The full record is
in this repo: `RULES.md`, `portfolio.json`, `trades.log`,
`final-report.md`, `HOW-I-RAN-IT.md`, and
`design-spec/stock-challenge-design-spec.md`.

## The honest framing first

There is no single program that "runs the challenge." There are three
halves, and only one of them is code:

1. **Arithmetic** — prices, valuation, ROI, benchmark math. This is
   `code/` in the repo: stdlib-only Python, runs on a Raspberry Pi with
   zero installs. It reproduces the final score exactly. It cannot make
   a decision.
2. **Judgment** — reading news and earnings, deciding what a move means,
   proposing (or not proposing) a trade. That was the agent reasoning in
   its own turn, over search results it had just pulled. In OpenClaw,
   this is your agent doing the same thing with its own model and tools.
   A different model will judge differently. That's expected; it's the
   point of the contest.
3. **The approval gate** — nothing becomes a trade until the human says
   yes in plain words in chat. This is the whole integrity of the game.
   A thumbs-up reaction is *not* approval: when the Week 1 check-in
   proposed a rebalance and the user replied with a thumbs-up, YSA did
   not treat it as an order — it asked in plain words whether the
   reaction meant yes, and only scheduled the execution after the user
   answered "Yes, do the rebalance."

If you skip part 3, you don't have the game; you have a backtester with
a chat window.

## Mapping the setup to OpenClaw

| What YSA used | The OpenClaw equivalent |
|---|---|
| Scheduled jobs (crons), one per timed event | Automations: `openclaw automations` (new name for `openclaw cron` since v2026.8.1; both work). Each job is a schedule plus a prompt. Jobs survive restarts. |
| Workspace files as the source of truth | Same files in the agent's workspace: `portfolio.json`, `trades.log`, `RULES.md`. The agent reads and writes them with its file tools. |
| Finance/news search at each step | A web-search tool on the agent (whatever search provider you have configured). Prices and news are looked up fresh at each run, never streamed or cached between runs. |
| Main chat as the delivery + approval channel | Whatever channel your OpenClaw agent lives on (Telegram, Discord, Slack…). Check-ins and proposals arrive there; approvals are given there. |
| Agent instructions (operating rules) | Workspace `AGENTS.md` (operating rules) and `SOUL.md` (persona) — OpenClaw reads the same files. Put the guards below in `AGENTS.md`. |
| The Pi scripts | Shell commands the agent can run, or an automation with a command payload — e.g. `python3 code/run_checkin.py` as a cross-check on the valuation math. |

## Install, in short

1. Clone the repo and put it somewhere your OpenClaw agent can reach
   as its workspace (or copy `RULES.md`, `portfolio.json`,
   `trades.log`, `code/` into the workspace).
2. Install OpenClaw and get the agent talking in your channel, with a
   capable model and a web-search tool. Set the timezone
   (`agents.defaults.userTimezone`, e.g. `America/Los_Angeles`); cron
   expressions otherwise use the Gateway host's timezone unless you
   pass `--tz`.
3. Put the rules in the workspace `AGENTS.md` (below). Decide the
   contest dates, the tickers, and the dollar allocations — the
   original game staged 8 orders on the opening Monday
   (`portfolio.json`, `status: "staged"`), and nothing was invested
   until the user approved them.
4. Create the automations (below). Use `--session isolated` so each
   run starts fresh and re-reads the files — a run that is interrupted
   then leaves the books in their last complete state.

## The guards — put these in `AGENTS.md`

These are the rules that kept the game honest. They matter more than
any code:

- **Status gate.** Every job reads `portfolio.json` first. Opening
  fills run only if `status` is exactly `"approved"`; check-ins run
  only if `status` is `"live"`; otherwise the job reports the state and
  stops. No status, no action.
- **Never trade without explicit approval in chat.** A suggestion is
  never a trade. A reaction is never approval. Ask in plain words;
  wait for a plain-words yes.
- **Never backdate.** Every fill is timestamped and priced at that
  session's official open (buys) or the stated Friday's official close
  (valuations). An intraday, after-hours, or previous-session price is
  never substituted. Deciding on Saturday does not earn Friday's price.
- **Fail closed on prices.** If an official price cannot be established
  from a reliable source, do not guess. Leave the portfolio unchanged
  and report that the fill could not be priced.
- **Idempotency.** A job that runs twice must not double-execute. The
  rebalance job checks whether trades timestamped for its session
  already exist; if they do, it does nothing and says so.
- **Log everything.** Every fill goes in `portfolio.json` (shares,
  fill price, fill time, cost basis, price source) and `trades.log`
  (one append-only line per fill: timestamp, action, ticker, shares,
  price, cost, source). Lines are never edited or removed. No log, no
  proof.
- **Mock only.** No brokerage is connected, no real order can be
  placed, no credentials for one are held. Every fill is a mock fill.

## The schedule, as OpenClaw automations

All times Pacific; adjust the dates for your own game. Create from the
CLI (or ask in chat — the agent can create automations itself):

```bash
# Opening fills — one-shot, Monday open (06:40 PT in the original game)
openclaw automations add --name "challenge-open-fills" \
  --at 2026-10-12T06:40:00-07:00 \
  --session isolated --tz America/Los_Angeles --announce \
  --message "Read portfolio.json. Proceed ONLY if status is exactly 'approved', otherwise report that the orders are awaiting approval and stop. For each staged order, look up the official market open for that ticker, fill at that open, record shares = target value / fill price to four decimals, update portfolio.json (status live), append each fill to trades.log with price source, and report the fills in chat."

# Weekly check-in — Saturdays ~9am PT, using Friday closes
openclaw automations add --name "challenge-checkin" \
  --cron "0 9 * * 6" \
  --session isolated --tz America/Los_Angeles --announce \
  --message "Read portfolio.json. Proceed ONLY if status is 'live'. For each holding, look up the prior Friday's official close and compute position values, total value, ROI vs $50,000, and the S&P 500 gap. Search news for major headlines on the holdings and any earnings. Append a dated check-in file with the full price table, totals, and headlines. Send a short chat update: value, ROI, best and worst holding, one-line market read. You may SUGGEST a trade with reasoning; you must NOT execute one. Suggestions need explicit approval in chat first."

# Final valuation — one-shot, the Saturday after the final Friday close
openclaw automations add --name "challenge-final" \
  --at 2026-11-21T09:00:00-08:00 \
  --session isolated --tz America/Los_Angeles --announce \
  --message "Read portfolio.json. Value every position at the Friday Nov 20 official close, compute the final total, ROI vs $50,000, and the S&P 500 benchmark gap. Write the final report, set status to 'final', and send the final scoreboard in chat. This is the last run; schedule nothing further."
```

A rebalance is **not** a scheduled job. It happens only when the human
approves one in chat, and then the execution prompt is:

> Re-read `portfolio.json`; confirm status is `live` and the position
> is as stated. Look up the next session's official open for both
> tickers. Sell the approved shares at that open; buy the other ticker
> with the full proceeds at its open. Write both fills to
> `portfolio.json` and `trades.log` with price sources, check the
> rebalance hasn't already executed for this session, and report the
> fills. If anything can't be priced, do nothing and say so.

Earnings recaps in the original game were short ad-hoc evening
check-ins (~6:30pm PT on earnings days) with the dollar impact on the
mock leg, plus a morning-after check — worth copying, but optional.

## Two disclosures to carry over

- **Prices came from search, not a feed.** The rulebook names Finnhub
  as the price source, and most closes were verified live and
  cross-checked against published data. But five of the eight opening
  fills were recorded from dated published reports (MarketBeat,
  American Banking News, Zolmax) rather than a live quote at the time.
  Each is sourced in `trades.log`. A rebuild should use one feed for
  all tickers — and whatever you use, record the source per fill, so
  the game can be argued about honestly afterwards.
- **The rebalance is the post-mortem.** The only approved trade of the
  whole game was Oct 19: sell half the XOM (14.6190 sh @ $178.45,
  +$108.76 realized) into an oil spike, buy NVDA (11.9616 sh @
  $218.095) with the proceeds. It doubled down on the exact holding
  that then fell apart — NVDA went from $229.28 at the open to $125.53
  at the final close, −44.67% on the leg, ~75% of the total loss. The
  system did what it was told; the judgment was the contestant's. That
  is the game working as designed, not a bug in it.

## What OpenClaw won't give you

- A live price feed. You get search, same as YSA had. Treat every
  price as a lookup with a named source, and fail closed when one
  can't be established.
- The same judgment. A different model, or the same model on a
  different day, will propose different trades. If you want the contest
  to be fair, every contestant's agent should run under the same rules
  and the same approval gate — the rules are the shared part, not the
  picks.
- Real-money safety by default. There is none here by design. Keep it
  mock. If anyone wires a brokerage in, that is a different project,
  and the approval gate above becomes load-bearing in a way this game
  never tested.

## If you run it

Keep the three artifacts together: the rules (`RULES.md`), the books
(`portfolio.json`, `trades.log`), and this note plus the design spec.
The code alone is the arithmetic; the note is the operation. The final
report is the proof. And when it ends, value it at the close, report
the number plainly — YSA finished $42,457.13, −15.09%, and the friend
who sold NVDA won — and stop the jobs.
