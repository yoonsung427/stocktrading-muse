# mock stock challenge — rulebook
decided: sat oct 10, 2026 (pdt) | markets were closed
start: $50,000 virtual cash | end: fri nov 20, 2026 close (6 weeks)

## rules
1. long-only us stocks/etfs. no options, no shorting, no leverage.
2. fractional shares allowed (keeps allocations clean).
3. no transaction costs in the sim (keeps it comparable w/ friends).
4. cash can't go negative. total buys ≤ portfolio value at trade time.
5. every trade timestamped, never backdated. fills use official
   open/close prices from a consistent source (finnhub).
6. opening orders fill at the mon oct 12, 2026 official open —
   no pretending fri oct 9's close was available after the decision.
7. dividends ignored (6-week horizon, keeps it simple).
8. benchmark: s&p 500 over the same period.

## audit trail
- portfolio.json — positions, cash, cost basis
- trades.log — every mock trade w/ timestamp + fill price + source
- weekly check-ins saved under checkins/
