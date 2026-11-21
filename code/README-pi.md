# stock challenge — raspberry pi learning package

a self-contained version of the 6-week, $50k mock stock challenge, built to
run on a raspberry pi. no pip installs needed — everything is python stdlib.

the game is over: it ran oct 12 – nov 20, 2026 and finished at $42,457.13
(-15.09% vs the $50k start; s&p 500 ~-11.54% over the same stretch).
only lly and ge finished green. run it as-is to replay the final book,
or reset it (see below) to start a fresh game.

the game is over: it ran oct 12 – nov 20, 2026 and finished at $42,457.13
(-15.09% vs the $50k start; s&p 500 ~-11.54% over the same stretch).
only lly and ge finished green. run it as-is to replay the final book,
or reset it (see below) to start a fresh game.

## what's inside

| file | what it does |
|---|---|
| `rules.md` | the challenge rulebook |
| `portfolio.json` | the final mock portfolio (8 positions + cash), updated nov 21 2026 — challenge ended fri nov 20 at $42,457.13 (-15.09%) |
| `trades.log` | every mock trade so far, timestamped |
| `run_checkin.py` | entry point — run the weekly check-in |
| `challenge/prices.py` | free price fetcher (yahoo finance, no api key) |
| `challenge/portfolio.py` | valuation, roi, benchmark math + trade recorder |
| `challenge/agent.py` | the portfolio manager: perceives → reasons → suggests (never trades alone) |
| `llm_agent.py` | optional: same report + a manager's note from a local llm via ollama |
| `cron.example` | crontab line for a weekly saturday check-in |

## quick start on the pi

```bash
# copy this folder to the pi, then:
cd stock-challenge-pi
python3 run_checkin.py
```

you'll get: portfolio value, roi, s&p 500 comparison, best/worst holding,
and the agent's ideas. that's the whole loop.

## the agent question

a pi can't run anything like muse — no cloud brain, limited ram. three
honest options, easiest first:

**1. the built-in rules agent (recommended start).** it's already here
(`challenge/agent.py`). perceive → reason → suggest, zero dependencies,
runs in seconds on any pi. this is the "portfolio manager" for learning
purposes, and honestly it's the right tool: the job is arithmetic plus
a few policy thresholds, not reasoning.

**2. local llm via ollama (the fun upgrade).** on a pi 5 with 8gb:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:4b     # small and pi-friendly; phi4-mini also works
python3 llm_agent.py     # needs `ollama serve` running
```

the model reads the check-in and writes a manager's note. advisory only —
it can't trade. expect ~10-30 seconds per note on a pi 5. this is the
closest you'll get to an "agent" on-device.

**3. a framework (only if you're curious).** huggingface's `smolagents`
is the lightest serious option and talks to ollama fine — but it needs
pip installs and buys you little over option 2 for this task. skip unless
you want to learn the framework itself.

my actual recommendation: run option 1 weekly via cron, and try option 2
once to see what the local model adds. if the llm's notes aren't better
than the rules, that's itself the lesson.

## resetting for your own run

edit `portfolio.json`: set `"cash": 50000.0`, empty `"positions": []`,
clear `"trades": []`, and set your own benchmark reference. then use
`challenge.portfolio.record_trade()` to log mock fills.

## notes & limits

- prices come from yahoo finance's free chart api (no key). it's the latest
  daily close, so check-ins are valuation snapshots — mock *fills* should
  still use official open prices per the rulebook.
- this is a learning sim: no real money, no brokerage, no advice.
