"""The portfolio manager. A rules-based agent: it values the portfolio,
compares against the benchmark, and proposes ideas — but never trades on its
own. (On the real challenge, trades need a human's explicit OK. Same here:
AUTO_TRADE stays False unless you flip it and accept the consequences.)

This is the file to study if you're learning how agents work: perceive
(fetch prices) -> reason (score positions) -> act (report / suggest).
"""

from . import portfolio as pf
from . import prices

# --- policy knobs: the agent's "personality". Tweak and re-run. ---
TRIM_WINNER_AT = 10.0    # propose trimming a position up this much since fill
ADD_WEAKNESS_AT = -8.0   # flag a position down this much as a possible add
CASH_SIDELINE_PCT = 5.0  # flag cash above this % of portfolio value


def weekly_checkin(portfolio_path="portfolio.json"):
    """Run one check-in. Returns a dict; also prints a human-readable report."""
    port = pf.load(portfolio_path)
    tickers = [p["ticker"] for p in port["positions"]] + ["SPX"]
    closes = prices.fetch_closes(tickers)
    v = pf.value(port, closes)

    ideas = []
    for p in v["positions"]:
        if p["pnl_pct"] >= TRIM_WINNER_AT:
            ideas.append(
                f"TRIM candidate: {p['ticker']} is up {p['pnl_pct']}% since fill "
                f"(${p['fill_price']} -> ${p['price']}). Consider banking some gains."
            )
        elif p["pnl_pct"] <= ADD_WEAKNESS_AT:
            ideas.append(
                f"WEAKNESS watch: {p['ticker']} is down {p['pnl_pct']}% since fill. "
                f"Thesis was '{p['thesis']}' — add only if the thesis still holds."
            )
    cash_pct = v["cash"] / v["total"] * 100 if v["total"] else 0
    if cash_pct >= CASH_SIDELINE_PCT:
        ideas.append(f"CASH: ${v['cash']:,.2f} ({cash_pct:.1f}%) sitting out — deploy or hold?")
    if not ideas:
        ideas.append("No triggers hit. Hold steady — no churn without a reason.")

    report = {
        "total": v["total"],
        "roi_pct": v["roi_pct"],
        "bench_pct": v["bench_pct"],
        "vs_benchmark_pp": v["vs_benchmark_pp"],
        "best": v["best"],
        "worst": v["worst"],
        "ideas": ideas,
        "positions": v["positions"],
    }
    _print(report)
    return report


def _print(r):
    print(f"\nportfolio: ${r['total']:,.2f}  ({r['roi_pct']:+.2f}%)")
    if r["bench_pct"] is not None:
        print(f"s&p 500:   {r['bench_pct']:+.2f}%   (we're {r['vs_benchmark_pp']:+.2f}pp vs benchmark)")
    print(f"best:  {r['best']['ticker']} {r['best']['pnl_pct']:+.1f}%")
    print(f"worst: {r['worst']['ticker']} {r['worst']['pnl_pct']:+.1f}%")
    print("\nagent ideas (suggestions only — no trades executed):")
    for i in r["ideas"]:
        print(f"  - {i}")
    print()
