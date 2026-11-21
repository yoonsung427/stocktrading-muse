#!/usr/bin/env python3
"""Optional LLM portfolio manager. Needs Ollama running locally:

    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull qwen3:4b        # small, pi-5-friendly
    ollama serve                # usually auto-starts

Then:  python3 llm_agent.py

It runs the same rules-based check-in, then asks the local model to write a
short manager's note (hold vs. change + why). The model only *advises* — it
cannot trade. Stdlib only.
"""

import json
import os
import urllib.request

from challenge.agent import weekly_checkin

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")


def ask_manager(report):
    lines = [
        f"- {p['ticker']}: {p['shares']} sh @ ${p['price']} "
        f"({p['pnl_pct']:+.1f}% since fill ${p['fill_price']}); thesis: {p['thesis']}"
        for p in report["positions"]
    ]
    prompt = (
        "You are a portfolio manager in a 6-week mock stock challenge ($50k virtual, "
        "long-only stocks/ETFs, no leverage, benchmark S&P 500). Rules: never churn "
        "without a reason, never recommend more risk than the rules allow.\n\n"
        f"Portfolio: ${report['total']:,.2f} ({report['roi_pct']:+.2f}%). "
        f"S&P 500 over same period: {report['bench_pct']:+.2f}%.\n"
        "Positions:\n" + "\n".join(lines) + "\n\n"
        "Write a 3-sentence manager's note: (1) how we're doing vs the benchmark, "
        "(2) the single best opportunity or risk you see, (3) hold or suggest one "
        "specific change and why. Plain language, no hype."
    )
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())["response"].strip()
    except Exception as e:  # noqa: BLE001 — pi-friendly error, not a crash
        return f"(llm unavailable: {e}. is `ollama serve` running?)"


if __name__ == "__main__":
    report = weekly_checkin()
    print("manager's note (local llm):")
    print(ask_manager(report))
    print()
