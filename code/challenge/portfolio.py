"""Portfolio math: load, value, ROI, benchmark comparison. Stdlib only."""

import json

START_CASH = 50_000.0


def load(path="portfolio.json"):
    with open(path) as f:
        return json.load(f)


def save(portfolio, path="portfolio.json"):
    with open(path, "w") as f:
        json.dump(portfolio, f, indent=2)


def value(portfolio, closes):
    """Value every position at the given closes.

    Returns a dict with per-position detail, total value, ROI, and the
    benchmark (S&P 500) move over the same period.
    """
    positions = []
    for p in portfolio["positions"]:
        ticker = p["ticker"]
        price = closes.get(ticker)
        if price is None:
            raise ValueError(f"no price for {ticker} — check your connection/symbols")
        market_value = p["shares"] * price
        pnl_pct = (price - p["fill_price"]) / p["fill_price"] * 100
        positions.append(
            {
                "ticker": ticker,
                "shares": p["shares"],
                "fill_price": p["fill_price"],
                "price": round(price, 2),
                "market_value": round(market_value, 2),
                "pnl_pct": round(pnl_pct, 2),
                "thesis": p.get("thesis", ""),
            }
        )

    total = round(sum(p["market_value"] for p in positions) + portfolio["cash"], 2)
    roi_pct = round((total - START_CASH) / START_CASH * 100, 2)

    # benchmark: S&P 500 from the challenge reference point to now
    spx_now = closes.get("SPX")
    spx_ref = portfolio.get("reference_prices_fri_oct_9_close", {}).get("SPX")
    bench_pct = (
        round((spx_now - spx_ref) / spx_ref * 100, 2)
        if spx_now and spx_ref
        else None
    )

    positions.sort(key=lambda p: p["pnl_pct"])
    return {
        "positions": positions,
        "cash": portfolio["cash"],
        "total": total,
        "roi_pct": roi_pct,
        "spx_now": spx_now,
        "bench_pct": bench_pct,
        "vs_benchmark_pp": round(roi_pct - bench_pct, 2) if bench_pct is not None else None,
        "best": positions[-1],
        "worst": positions[0],
    }


def record_trade(portfolio, ticker, action, shares, fill_price, price_source, note=""):
    """Append a mock trade to the portfolio's audit trail. Never backdates:
    callers must pass the real fill timestamp."""
    from datetime import datetime, timezone

    trade = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "ticker": ticker,
        "action": action,
        "shares": round(shares, 4),
        "fill_price": fill_price,
        "price_source": price_source,
        "note": note or "mock fill — no real money moved",
    }
    portfolio.setdefault("trades", []).append(trade)

    # apply it to positions / cash
    if action == "buy":
        cost = shares * fill_price
        if cost > portfolio["cash"]:
            raise ValueError("insufficient cash — cash can't go negative (rule 4)")
        portfolio["cash"] = round(portfolio["cash"] - cost, 2)
        for p in portfolio["positions"]:
            if p["ticker"] == ticker:
                p["shares"] = round(p["shares"] + shares, 4)
                break
        else:
            portfolio["positions"].append(
                {"ticker": ticker, "shares": round(shares, 4),
                 "fill_price": fill_price, "cost_basis": round(cost, 2),
                 "thesis": note}
            )
    elif action == "sell":
        for p in portfolio["positions"]:
            if p["ticker"] == ticker:
                if shares > p["shares"]:
                    raise ValueError("can't sell more shares than held")
                p["shares"] = round(p["shares"] - shares, 4)
                portfolio["cash"] = round(portfolio["cash"] + shares * fill_price, 2)
                break
        else:
            raise ValueError(f"no position in {ticker} to sell")
    else:
        raise ValueError("action must be 'buy' or 'sell'")
    return trade
