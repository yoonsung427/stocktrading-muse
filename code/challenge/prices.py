"""Free price fetcher. Uses Yahoo Finance's public chart API — no API key needed.

Stdlib only (urllib), so it runs on a stock Raspberry Pi.

Caveat for the sim: the quote is the latest daily close (or the previous
close when the market is shut). For mock *fills*, use the official open
price like the rulebook says — this fetcher is for valuation/check-ins,
not fills.
"""

import json
import urllib.request

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"


def _to_yahoo(ticker):
    if ticker.upper() == "SPX":
        return "%5EGSPC"  # S&P 500 index
    return ticker.upper()


def fetch_closes(tickers):
    """Return {TICKER: close_price} for each ticker. Raises on network failure."""
    closes = {}
    for t in tickers:
        req = urllib.request.Request(
            YAHOO_URL.format(symbol=_to_yahoo(t)),
            headers={"User-Agent": "Mozilla/5.0 (stock-challenge-pi/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        result = data["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        valid = [c for c in quote["close"] if c is not None]
        if not valid:
            raise ValueError(f"no price data for {t}")
        closes[t.upper()] = round(valid[-1], 2)  # latest close
    return closes


if __name__ == "__main__":
    print(fetch_closes(["NVDA", "MSFT", "SPX"]))
