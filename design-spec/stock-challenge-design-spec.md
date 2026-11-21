# Mock Stock Challenge — Design Specification

_Converted from the 17-page design spec PDF dated 18 October 2026. Content is unchanged; only the format changed so it can live in the repo as text._

The one-sentence version: YSA (the Muse agent) manages one $50,000 mock portfolio against the user's friends over six weeks. All state lives in plain workspace files, every timed action is a separate scheduled job, prices and news are gathered by search at each step, the agent reasons over that evidence in its own turn, and no trade executes without the user's explicit approval.

Status: Live - opened Monday 12 October 2026, closes Friday 20 November 2026

Spec date: 18 October 2026 (after the Week 1 check-in and the approval of the first rebalance)

Contestant managed by this system: YSA's portfolio only. Friends run their own portfolios under the same shared rules.

Money: None. Every fill is a mock fill. There is no brokerage account, no order routing, and no real-money movement anywhere in the design.

How to read this document: Sections 1-2 define the contest. Sections 3-10 define the platform machinery. Sections 1113 are the core of the design: the check-in, the reasoning pipeline from news to suggestion, and the gated path from approval to execution. Sections 14-15 cover integrity, limits, and what a faithful rebuild must preserve.

## 1. Purpose, scope, and non-goals

The challenge was decided on Saturday 10 October 2026, while markets were closed, as a friendly six-week competition: who can turn $50,000 of virtual cash into the highest return by the close on Friday 20 November 2026. Bragging rights only.

This system exists to run one contestant's portfolio - YSA's - honestly enough that its result can be compared with the friends' portfolios without argument. That purpose drives every design choice that follows: published fill prices, no backdating, an append-only trade log, and a hard approval gate on trading.

**Explicit non-goals**

- Not a trading platform. No brokerage is connected, no real order can be placed, and no credentials for one are held.
- Not an autonomous trader. The agent never trades on its own judgement, on a schedule, or on a price threshold. Schedules only gather prices and news and report.
- Not a rules engine. There are no coded buy or sell rules - no "trim at +10%" or "exit at -8%" logic anywhere in this implementation. Judgement is exercised by the agent, in language, over evidence it has just gathered (Section 13).
- Not a tracker for the friends. Their portfolios are kept by them. This system stores only YSA's positions, plus the S&P 500 benchmark for context.
## 2. Contest definition - the shared rules

These rules apply to every contestant, not just YSA, and are the contract the platform implementation enforces:

1. Start: $50,000 virtual cash. Start fills at the Monday 12 October 2026 market open; end at the Friday 20 November 2026 market close (six weeks).
2. Long-only US stocks and ETFs. No shorting, no options, no leverage, no margin.
3. Fractional shares are allowed, so allocations can be exact dollar amounts.
4. Cash cannot go negative. Total buys can never exceed portfolio value at trade time.
5. No transaction costs in the simulation, keeping results comparable across contestants.
6. Dividends are ignored over the six-week horizon.
7. No backdating, ever. Every trade is timestamped and filled at that session's official open or close from a consistent, named source. Deciding on Saturday does not earn Friday's price.
8. Scoring: ROI = (final value - $50,000) / $50,000. Highest ROI wins; ties share the win. The S&P 500 return over the same period is the benchmark.
9. Proof: a trade log with date, ticker, shares, and price for every trade. No log, no proof.
## 3. Roles and authority

```
 Role                      What they do                                                   What they cannot do

 The user - owner and      Sets the rules, approves the opening picks, and approves       -
 approver                  or rejects every later trade in the main chat. Can close the
                           topic at any time.

 YSA / Muse agent -        Chooses the portfolio, gathers prices and news, values         Execute any trade without the
 contestant and manager    the portfolio, writes check-ins, proposes trades with          user's explicit approval; invent a
                           reasons, and executes approved trades as mock fills.           price; backdate a fill.

 Scheduled jobs - timers   Wake the agent at a set date and time with a fixed             Decide anything. A job carries
                           instruction set (fill the open, run a check-in, execute one    instructions written in advance; it
                           approved rebalance, run the final valuation).                  holds no discretion beyond them.

 Friends - other           Run their own portfolios under the same rules for              - (outside this system)
 contestants               comparison at the end.
```

Approval means explicit. When the Week 1 check-in proposed a rebalance and the user replied with a thumbs-up reaction, the agent did not treat the reaction as a trade order - it asked in plain words whether the reaction meant yes. Execution was scheduled only after the user answered "Yes, do the rebalance" on 18 October.

## 4. Platform architecture

There is no custom trading software and no always-on daemon. The implementation is five ordinary Muse parts composed together:

```
 Component                      Function in this challenge

 Goal                           The durable container for the challenge: its description ($50k, six weeks, long-only, weekly
                                Saturday check-ins, final valuation 20 Nov), its scheduled jobs, and its working files all hang
                                off one goal, mock-stock-challenge-6-weeks-50k.

 Workspace state files          The entire books of the contest as plain files (Section 5). Files, not a database - any run
                                starts by reading them, and ends by updating them.

 Scheduled run-once jobs        One job per timed event, each firing once at an exact Pacific time, then expiring. The full
                                inventory is Appendix B.

 Search - finance and news      The only market-data and news source. Prices are looked up per ticker at fill and valuation
 verticals                      time; news is looked up per holding at check-in time (Section 13.3). Nothing is streamed or
                                cached between runs.

 Main chat                      The delivery and approval channel. Check-ins, fill reports, and proposals arrive there;
                                approvals are given there.
```

Because each run re-reads the files and re-searches for prices and news, a run that is interrupted leaves the books in their last complete state - a job either finishes its file updates or the portfolio is unchanged.

## 5. Data model - where the truth lives

```
 Store                                Contents and role

  portfolio.json                      Single source of truth. Fields: start_cash (50000.0), cash , status (the
 ~/workspace/mock-stock-              lifecycle gate, Section 6), staged_orders[] (ticker, target_pct, target_value,
 challenge/                           thesis), positions[] (ticker, shares, fill_price, fill_time, cost_basis, thesis,
                                      price_source), trades[] (the structured copy of every fill), and
                                       reference_prices_fri_oct_9_close (kept only as a cross-check that the
                                      Monday opens were plausible against Friday's closes).

  trades.log                          Append-only human-readable mirror. One line per fill: timestamp, action, ticker,
                                      shares, fill price, cost, and price source, ending "mock fill, no real money moved".
                                      Lines are never edited or removed.

  RULES.md                            The rulebook as decided on 10 October (Section 2), stored beside the portfolio so any
                                      run can re-check itself against it.

  checkin-YYYY-MM-DD.md               One dated snapshot per check-in: the price table, totals, benchmark maths, the
 goal hidden_files/                   week's headlines with their sources, and any rebalance proposal. This is both the audit
                                      record and the raw material the reasoning is preserved in (Section 13).

 Run notes                            A short note per execution job: what was read, which prices were used and where
 e.g. open-fills-run-2026-10-12.md    each came from, and what was written. Written for fills and for the rebalance.

 Cron definitions                     The saved instruction text of every scheduled job - in effect, the executable half of this
 goal crons/runonce/                  spec. Each names its inputs, steps, guards, and the report it must send.
```

## 6. Lifecycle and state gates

```
 1. STAGED                       2. APPROVED                     3. LIVE                            4. FINAL
 Opening orders written to       User approves the picks.        Opening fills written, cash        Valued at the 20 Nov close
 portfolio.json with target      Only this exact status          ~$0. Weekly check-ins run;         by the final job on Sat 21
 dollars and theses. Nothing     unlocks the opening job.        trades only via Section 13's       Nov. No further runs are
 is invested.                                                    pipeline.                          scheduled.
```

The gate is literal. The opening-fills job's first instruction is to read portfolio.json and proceed only if status is exactly "approved"; if it is still "staged", the job does nothing except tell the user the orders are awaiting approval. Check-in jobs apply the mirror-image guard: if status is not "live", they report that the portfolio has not opened and stop. The rebalance job adds an idempotency guard - if trades timestamped for its session already exist, it does nothing and reports that the rebalance already executed.

## 7. Pricing and fill rules

Session prices only. Buys at the start of a session fill at that session's official open; valuations use the official close of the stated Friday. An intraday, after-hours, or previous-session price is never substituted. One lookup per ticker, through the finance search vertical, with the source recorded per fill in both portfolio.json ( price_source ) and trades.log .

Fractional sizing: shares = target value / fill price, kept to four decimal places. Opening example: $10,000 / $229.28 = 43.6148 shares of NVDA. Timestamp discipline: fills carry the session open time - 06:30 Pacific (09:30 Eastern) - not the time the job happened to run (the opening job ran at 06:40, ten minutes after the open it priced). Fail closed: if an official price cannot be established from a reliable source, the job must not guess. It leaves the portfolio unchanged and reports that the fill could not be priced. This rule is written into the rebalance job verbatim.

Known variance, stated plainly: the rulebook names Finnhub as the consistent price source, and Finnhub supplied the LLY, XOM, and GE opens. For the other five tickers the recorded opens came from dated published reports of that morning's open - MarketBeat (NVDA, MSFT), American Banking News (AMZN, META), and Zolmax (JPM). Every price is individually sourced in the log, and each was cross-checked against the stored Friday 9 October closes, but a rebuild should use one feed for all tickers (Section 15).

## 8. Opening portfolio - 12 October 2026 open

```
 Ticker      Thesis (as staged)                             Target           Fill $      Shares                     Cost $

 NVDA        AI infrastructure leader                         20%          229.28       43.6148                 10,000.00

 MSFT        AI + cloud, steady                               15%          535.07       14.0169                  7,500.02

 AMZN        AWS + consumer                                   15%          262.43       28.5790                  7,499.99

 META        AI capex, ads engine                             10%          718.67         6.9573                 5,000.00

 JPM         Bank earnings 13 Oct catalyst                    10%          333.01       15.0146                  5,000.01

 LLY         Pharma growth                                    10%        1,181.24         4.2328                 4,999.95

 XOM         Energy hedge                                     10%          171.01       29.2381                  5,000.01

 GE          Industrials, earnings 20 Oct                     10%          307.78       16.2454                  5,000.01

 Total invested / cash remaining                                                                          49,999.99 / 0.01
```

The construction is deliberate: a 60% AI-and-cloud core (NVDA, MSFT, AMZN, META), with the remaining 40% in diversifiers and dated catalysts (JPM and GE earnings, LLY growth, XOM as the energy hedge). That structure is what the Week 1 reasoning in Section 13.5 reads the market against.

## 9. Valuation and scoring

Portfolio value = sum over positions of (shares x current price) + cash. ROI = (value - $50,000) / $50,000. Benchmark = S&P 500 return over the matched window, in percentage points (pp). Best and worst holdings are ranked by return since fill.

**Worked example - Week 1 (closes, Friday 16 October)**

```
 Ticker                                     Fill $                   Close $                       Value $                  Return

 NVDA                                     229.28                      214.13                     9,339.24                  -6.61%

 MSFT                                     535.07                      529.05                     7,415.64                  -1.13%

 AMZN                                     262.43                      250.00                     7,144.75                  -4.74%

 META                                     718.67                      709.33                     4,935.02                  -1.30%

 JPM                                      333.01                      339.49                     5,097.31                  +1.95%

 LLY                                    1,181.24                    1,258.04                     5,325.03                  +6.50%

 XOM                                      171.01                      179.02                     5,234.20                  +4.68%

 GE                                       307.78                      313.79                     5,097.64                  +1.95%

 Value (positions + $0.01 cash)                                                                 49,588.85                  -0.82%
```

Benchmark: S&P 500 from 7,811.54 (9 Oct close) to 7,659.44 (16 Oct close) = -1.95%. Net: +1.12 pp ahead the diversifiers offset the falling AI core, as built. Total is the figure recorded in checkin-2026-10-17.md ; perposition values above are rounded to cents.

## 10. Scheduled operations

Every timed action is a separate run-once job owned by the goal, in America/Los_Angeles time, delivering to the main chat. Run-once matters: a check-in cannot fire twice, and no trade job exists until approval creates one.

```
 When (Pacific)                  Job                               Does

 Mon 12 Oct, 06:40               Opening fills                     Prices and writes the eight opening fills (Section 7), sets
                                                                   status to "live".

 Sat 17, 24, 31 Oct; 7, 14       Check-ins W1-W5                   Values at the prior Friday close, benchmarks, gathers news,
 Nov, 09:00                                                        files the check-in, reports, may propose - never trades.

 Mon 19 Oct, 06:35               Rebalance W2                      Created only after the 18 Oct approval. Executes exactly the
                                                                   approved XOM-to-NVDA rebalance at the open (Section 12).

 Sat 21 Nov, 09:00               Final valuation                   Values at the Fri 20 Nov close and sends the final result. The
                                                                   last scheduled run.
```

Execution jobs fire just after the open (06:35-06:40) so the opening price exists to look up; fills are timestamped at the open.

## 11. Weekly check-in procedure

Each Saturday check-in job runs the same steps, in order:

1. Guard: read portfolio.json ; stop unless status is "live".
2. Price: for each of the eight tickers, look up the prior Friday's official close via the finance search vertical one query per ticker.
3. Value: compute position values, total value, ROI against $50,000, and the S&P 500 move over the matched window (Section 9).
4. Gather news: run news-vertical searches for major headlines on the holdings - earnings, guidance, macro, sector moves (detailed in Section 13.3).
5. File: append the dated check-in file with the full price table, totals, headlines with sources, and any proposal. This file is written before the chat message, so the record exists even if the summary is skimmed.
6. Report: send a short chat update - value, ROI, best and worst holding, one-line market take.
7. Propose, do not act: the job's instructions state it in capitals in spirit - suggest any rebalance idea, but make no trades; trades need the user's explicit ok.
## 12. Rebalance procedure - execution after approval

An approved rebalance gets its own new run-once job, written after approval, naming the approval date and the exact trades. The Week 2 job (Mon 19 Oct, 06:35) specifies:

1. Re-read portfolio.json ; confirm status "live" and the XOM position is still 29.2381 shares. If 19 Oct trades already exist, stop (idempotency).
2. Look up the Monday 19 Oct official open for XOM and NVDA via the finance vertical. Never Friday's closes, never a guess.
3. Sell 14.6190 shares of XOM - exactly half the position - at that open. Proceeds = 14.6190 x open.
4. Buy NVDA with the full proceeds at its open. Shares = proceeds / open. The trade is proceeds-funded, so cash cannot go negative and no new cash is introduced.
5. Write both fills to portfolio.json (XOM down to 14.6191 shares, NVDA increased) and to trades.log , each with fill price, price source, and the note recording the 18 Oct approval. Timestamp both 06:30, the open.
6. Write a run note with fill prices, share counts, and resulting position sizes; report the same to the main chat.
Fail-closed clause: "If the open prices cannot be established from a reliable source, do NOT invent prices report that the fills could not be priced and leave the portfolio unchanged." An unpriced rebalance is a reported non-event, never a filled one.

## 13. Decision-making: picking, sizing, and trading

Where reasoning happens: in the agent's own turn - in the main chat when the portfolio was designed, and inside each scheduled check-in job when trades are proposed. There is no stock-screening program, scoring model, or coded rule set behind it. The agent reads the stored theses and current prices, gathers fresh news (13.4), weighs the evidence in language, and writes its reasoning down in the check-in file where the user can audit it. That written reasoning - not a hidden calculation - is the decision record.

13.1 How the original portfolio was constructed Construction started from the contest, not from a stock list: a six-week horizon rewards names with a live growth story and a dated catalyst inside the window; long-only rules mean risk can only be managed by what is owned and in what size; and scoring on the full $50,000 means idle cash is a drag. Three layers followed:

```
 Layer                   Picks and sizing logic

 Conviction core -       NVDA ($10,000). The single largest bet and the purest expression of the portfolio's main thesis - "AI
 20%                     infra leader". Sized at 20%, not more: it is also the most volatile name, so the cap lets it drive
                         returns without letting one ticker decide the contest.

 Core support - 15%      MSFT ($7,500) - "AI + cloud, steady": the same AI theme with a steadier earnings base, ballast
 each                    inside the tech allocation. AMZN ($7,500) - "AWS + consumer": a second, distinct earnings engine
                         (cloud plus retail) rather than a duplicate of MSFT.

 Satellites - 10% each   META - "AI capex, ads engine", held smaller because it is correlated with the core. JPM - financials
                         diversifier with earnings on 13 Oct, the first full day of the contest. LLY - "pharma growth",
                         deliberately outside tech. XOM - "energy hedge", the holding expected to rise in exactly the
                         scenario that hurts the core. GE - industrials diversifier with earnings on 20 Oct.
```

Diversification logic: 60% AI-and-cloud (NVDA, MSFT, AMZN, META) against 40% non-AI (JPM, LLY, XOM, GE). The AI concentration is intentional - it is the contest's return engine - and the 40% is its insurance. Week 1 tested the design directly: the AI core fell, all four diversifiers rose, and the portfolio lost -0.82% against the S&P 500's -1.95% (Section 9). Why 10% is the floor: at $5,000, a satellite that moves 5% contributes about 0.5% to the portfolio - enough to matter, small enough that a failed thesis cannot sink the result. Why eight names: enough for real diversification, few enough that every holding can be priced and news-scanned properly at every check-in. Why fully invested (cash: $0.01): with no transaction costs and a six-week clock, uninvested cash could only subtract from ROI.

13.2 Ongoing trade management - the standing principles Hold is the default. The plan from the start was "no churn": a proposal must beat doing nothing, and every check-in presents the hold alternative alongside any trade idea. A thesis, not a price, is what gets re-examined. A falling holding is a candidate to add to if its thesis is intact, and a candidate to exit if the news breaks the thesis. A rising holding is a candidate to trim when the rise comes from a temporary premium rather than improved prospects. Trade strength into weakness, in pairs. Rebalances are framed as source-and-use: one holding funds another, keeping the portfolio fully invested and cash non-negative by construction. Time remaining counts. With five weeks left after Week 1, there was room for a trimmed position to recover and an added position to work; the same moves would need a stronger case in the final week. Size moves in fractions of a position, not all-or-nothing. Partial trims keep a working thesis in the portfolio while still freeing meaningful proceeds (13.5).

**13.3 The reasoning pipeline - news to execution**

```
 1. INTAKE               2. ANALYSIS             3. SUGGESTION            4. APPROVAL            5. EXECUTION
 Check-in job            Agent weighs news       Sized proposal + hold    Explicit user yes in   New run-once job fills
 searches finance        vs thesis, move since   alternative, filed and   main chat - the only   at next open, records
 prices + news           fill, benchmark,        sent in chat             trigger                both fills
 headlines per holding   catalysts
```

Stage 1 - News intake (inside the check-in job). Alongside Friday closes, the job runs news-vertical searches for major headlines on each holding: earnings results and dates, guidance, analyst actions, sector and macro moves. The headlines are saved, with their sources named, into that week's checkin-YYYY-MM- DD.md - so the evidence behind any suggestion is preserved, not summarised away. Week 1's file records, for example, JPM's 13 Oct results, Truist's META target raise, LLY's regulatory news, and the earnings dates ahead for META, AMZN, LLY, XOM, and GE.

Stage 2 - Analysis (agent reasoning, no formula). The agent reads three things together: (a) each holding's return since fill, (b) its original stored thesis, and (c) the week's news. No single input decides. A -6.61% week for NVDA means one thing alongside "AI spending is collapsing" and another alongside "semiconductors sold off sector-wide while NVDA's own story is unchanged" - the Week 1 evidence supported the second reading.

Stage 3 - Suggestion. Any idea is written into the check-in file and sent in chat as a sized, reasoned proposal with the alternative stated ("alternatively hold everything"), and is explicitly labelled: no trades made - needs the user's explicit ok.

Stages 4-5 - Approval and execution follow Sections 3 and 12: clarification of any ambiguous signal, an explicit yes, then - and only then - creation of the execution job.

13.4 Worked trace - how the Week 1 XOM to NVDA idea was formed

Evidence gathered (16 Oct Reasoning applied closes + news)

```
 AI unwind: Nasdaq's worst            Sector- and macro-driven, not NVDA-specific: the "AI infra leader" thesis was dented by
 week since June (-4.5%); SOX         sentiment, not broken by company news. A thesis-intact leader 6.6% below the contest's
 down 13% in seven sessions;          own entry is an add candidate (13.2) - a better entry than the 12 Oct open originally paid.
 CoreWeave -12% on debt
 concerns; Broadcom's CEO
 warned on AI spending; hot
 inflation raised rate-hike odds.
 NVDA fell to $214.13, -6.61%
 since fill - the worst holding.

 Oil spike: WTI closed above          XOM did its hedging job - but the rise was a geopolitical risk premium, which typically
 $100 (best week since July),         mean-reverts as headlines fade, not an improvement in XOM's prospects (earnings still
 Brent at $109.86 (highest since      two weeks away, 30 Oct). A hedge at an all-time high on temporary premium is a trim
 May) after attacks on tankers in     candidate.
 the Strait of Hormuz. XOM rose
 to $179.02, +4.68%, at or near
 an all-time high.

 Context: portfolio -0.82%,           No forced move: the portfolio was winning, so the proposal had to be an improvement
 beating the benchmark by +1.12       trade, not a rescue - presented with holding everything as a fully respectable option.
 pp; five weeks remaining.
```

13.5 The sizing - why half of XOM, all proceeds to NVDA The idea sharpened between the check-in file (which floated trimming about $1,000 of XOM) and the chat proposal: sell exactly half of XOM - 14.6190 of 29.2381 shares - and add the full proceeds to NVDA. Half realises a meaningful slice of the spike (roughly $2,600 at Week 1's close) and lifts NVDA from $9,339 (18.8% of the portfolio) toward roughly a quarter of it, while the retained half (14.6191 shares) keeps the energy hedge alive if oil rises further. A full exit would abandon a working hedge; a $1,000 trim would barely move NVDA. Using all proceeds keeps the portfolio fully invested and the trade self-funding.

13.6 Approval, pricing, and recording - the timeline as it happened

```
 When                       Event

 Sat 17 Oct                 Week 1 check-in files the proposal and reports it in chat. No trade made.

 Sun 18 Oct                 User reacts with a thumbs-up; the agent asks whether that means yes rather than assuming it. User
                            replies: "Yes, do the rebalance." Only now is the trade authorised.

 Sun 18 Oct                 The execution job mock-challenge-rebalance-w2 is created for Mon 19 Oct, 06:35 Pacific,
                            naming the approval and the exact share count.

 Mon 19 Oct                 Job looks up the official Monday opens, sells and buys at those opens (timestamped 06:30),
                            updates portfolio.json and trades.log with price and source per leg, writes its run note,
                            and reports in chat. If the opens cannot be verified, it does none of this (Section 12).
```

## 14. Integrity, failure modes, and limits

Every fill is auditable: timestamp, shares to four decimals, fill price, cost, named price source, and the mock-fill note - in both the structured record and the append-only log. No silent trades: the combination of check-in jobs that cannot trade, execution jobs that exist only after approval, and the idempotency guard makes an unauthorised or duplicated trade a structural impossibility within the design, not just a policy. Price-source variance (known flaw): the opening fills drew on Finnhub plus three dated news sources rather than one feed (Section 7). Each price is sourced and cross-checked, but a single feed would be cleaner. Search-derived prices: prices come from search results at run time, not a streaming market feed. That is sufficient for once-a-week mock valuation at official opens and closes; it would not support intraday trading, which the design does not attempt. Simplifications by rule: dividends and transaction costs are excluded for all contestants, so results are comparable but are not a simulation of a real brokerage account. Friends' results are external: the final comparison depends on their logs meeting the same proof standard (Section 2, rule 9). Reasoning is judgement, not a guarantee: the pipeline preserves the evidence and the reasoning for every suggestion, so a bad call can be examined afterwards - the Week 1 trace in 13.4 is the template.

## 15. Rebuilding this faithfully

A reimplementation - on any platform - is this challenge only if it preserves the parts that make the result trustworthy:

1. The shared rules exactly as in Section 2, including no backdating and proof by trade log. 2. One portfolio state file as the single source of truth, with a lifecycle gate that execution checks before acting. 3. Fills only at a session's official open or close, from a named source recorded per trade - and a fail-closed refusal to invent a price. Use one price feed throughout (fixing the Section 14 flaw). 4. Scheduled valuations that gather prices and news, and file a dated snapshot before reporting. 5. Reasoning done explicitly over that evidence - thesis, move, news, catalysts, time left - with proposals written down alongside the hold alternative. 6. The approval gate: no execution job, task, or order exists before an explicit human yes. 7. Proceeds-funded, fractionally sized rebalances, recorded as paired fills with sources.

Within this platform, the non-negotiables are the gates and the audit trail: change the price source or the schedule times and the challenge still works; remove the approval gate, the fail-closed pricing rule, or the per-fill source record, and it is no longer the same challenge.

16. Operational record - the actual files that were created
This is not a proposed layout. These are the files on disk, in the order they came into existence:

```
 File (exact path)                     Created / role in the running challenge

 ~/workspace/goals/mock-stock-         The goal record (ID goal_79306bfe87ef ): description, slug, and the
 challenge-6-weeks-50k/GOAL.md         statement that check-ins run each Saturday with final valuation at the Fri 20 Nov
                                       close. Every cron below is owned by this goal.

 ~/workspace/mock-stock-               The rulebook as decided Sat 10 Oct 2026 (PDT), markets closed: $50,000 start,
 challenge/RULES.md                    long-only, fractional shares, no costs, cash never negative, fills at official
                                       open/close from a consistent source, dividends ignored, S&P 500 benchmark,
                                       plus the audit-trail definition.

 .../files/mock-stock-                 The shareable rules sheet for all contestants (the version friends play by) - same
 challenge-rules.md                    rules, written for people rather than workers.

 ~/workspace/mock-stock-               First written with staged_orders and status "staged", then "approved" on the
 challenge/portfolio.json              user's go-ahead. On 12 Oct the opening worker rewrote it in place: 8
                                        positions , 8 trades , cash: 0.01 , status "live". Still the file every later
                                       job reads first and updates last.

 ~/workspace/mock-stock-               Created by the opening run: exactly 8 lines, one per fill, format timestamp |
 challenge/trades.log                  BUY TICKER | shares N | fill $P | cost $C | source: ... |
                                       mock fill, no real money moved . The rebalance job will append lines 9-
                                       10; nothing ever rewrites existing lines.
```

16. Operational record - continued
```
 File (exact path)                      Created / role in the running challenge

  .../crons/runonce/*.md (8 files)      One file per scheduled job, named <job-id>__runonce@<fire-time>.md -
                                        e.g. mock-challenge-open-fills__runonce@2026-10-
                                        12T06:40:00.md . Each file IS the job: frontmatter plus the worker's instructions
                                        (Section 17).

  .../hidden_files/open-fills-          The opening worker's run note: prices used, where each came from, fills
 run-2026-10-12.md                      computed, totals ($49,999.99 invested, $0.01 cash).

  .../hidden_files/checkin-2026-        The Week 1 worker's output file: price table, totals, headlines with sources, and
 10-17.md                               the rebalance proposal marked "no trades made".

  .../hidden_files/rebalance-           Not yet written - their jobs' instructions name these exact paths as outputs for 19
 2026-10-19.md and final-2026-          Oct and 21 Nov respectively.
 11-21.md
```

"..." above abbreviates ~/workspace/goals/mock-stock-challenge-6-weeks-50k/ only to fit the table; every other path is written in full.

17. A cron job, anatomised - what actually fires and runs
Each job file has two parts. The frontmatter is the scheduling record, identical in shape for all eight jobs:

```
 Field                         Real value (opening-fills job) and what it does

  id                            mock-challenge-open-fills - the job's name everywhere else in this spec.

  title                        "mock challenge: monday open fills" - the human label shown with the run.

  enabled                       true - a disabled job would simply never fire.

  owner                         goal:mock-stock-challenge-6-weeks-50k - ties the job to the goal, so the
                               challenge's jobs are managed as a set.

  mode                          task - when it fires, a worker agent is spawned to do work, not just send a reminder.

  schedule                      kind: runonce , timezone: America/Los_Angeles , at: 2026-10-
                               12T06:40:00 - fires once, at that Pacific time, then is done.

  delivery                     The main direct chat - where the worker's report lands and where the user reads it.
```

The body below the frontmatter is a plain-English instruction script for the worker that fires. There is no compiled code and no shell command in it. When the time comes, the worker executes the body with the ordinary tools of a Muse session, in the body's order:

1. Read the named input file ( portfolio.json in every job in this challenge).
2. Check the guard written in the body (status value, position size, or "already executed?") and stop or continue exactly as instructed.
3. Search - browser_search with the finance vertical for prices (one query per ticker, e.g. "NVDA stock price october 12 2026 open") and the news vertical for headlines (check-in jobs only).
4. Compute in the worker's own reasoning: shares = target / price, position values, ROI, benchmark move. Nothing is calculated by an external program.
5. Write the named output files - update portfolio.json , append to trades.log , create the dated run note or check-in file.
6. Report a short message to the main chat, in the format the body specifies.
That is the whole runtime: a job's file, listed in Appendix B, contains everything that will happen when it fires.

18. Runbooks - each job type, as it actually ran or will run
Opening fills - ran Mon 12 Oct, 06:40 (reported in chat the same morning) Worker read portfolio.json , found status "approved", ran eight finance searches (plus follow-ups for META and GE), computed fractional shares per ticker, rewrote portfolio.json to status "live" with all positions and trades, appended the 8 lines to trades.log , wrote the run note, and reported each ticker, shares, fill price, $49,999.99 invested and $0.01 cash. What the user saw: that fill report in the main chat - the first proof the challenge was live.

Weekly check-in - ran Sat 17 Oct, 09:00 (W1); repeats 24, 31 Oct, 7, 14 Nov Worker read the live portfolio, pulled Friday closes per ticker, computed the Section 9 table, ran news searches per holding, wrote checkin-2026-10-17.md , and sent a short chat update: $49,588.85, -0.82%, beating the S&P 500, best LLY / worst NVDA, plus the rebalance idea. Note what it did not do: touch portfolio.json positions or trades.log at all. A check-in is read-only on the books.

Rebalance execution - scheduled Mon 19 Oct, 06:35 (created only on 18 Oct, after approval) Worker will re-read the portfolio, confirm XOM is still 29.2381 shares and no 19 Oct trades exist, pull the two official opens, write both fills to portfolio.json and trades.log , write rebalance-2026-10-19.md , and report XOM shares sold and price, NVDA shares bought and price, and the new position sizes. What the user will see: exactly that fill report - or, if the opens cannot be verified, a report saying so, with the portfolio untouched.

Final valuation - scheduled Sat 21 Nov, 09:00 Worker values every position at the Fri 20 Nov close, computes final ROI and the S&P 500 comparison, writes final-2026-11-21.md with every trade, final positions, and narrative, and sends the final result. Its instructions state it is the last scheduled run - after it, the goal has no live jobs.

19. Edge cases and failure handling - as written into the jobs
```
Case                                   Handling

Opening job fires but picks were       Status is still "staged": worker does nothing except notify the user the orders await
never approved                         approval. No fills, no file changes beyond that note.

Check-in fires before the portfolio    Status is not "live": worker reports the portfolio has not opened and stops. No
opens                                  valuation is fabricated from staged orders.

Rebalance job fires twice / after a    Trades timestamped 2026-10-19 already in portfolio.json : worker does
manual fill                            nothing and reports the rebalance already executed (idempotency guard).

Official open cannot be established    Fail closed: no invented price, portfolio unchanged, user told the fills could not be
                                       priced. Written verbatim into the rebalance job.

Position changed since approval        Rebalance job first confirms XOM is still 29.2381 shares; its sell quantity (half) is
                                       defined against that recorded position, not assumed.

Price source disagrees with Friday's   Stored Friday reference prices in portfolio.json act as a sanity cross-check -
close                                  the opening run verified Finnhub quotes against them (e.g. LLY open 1181.24 vs
                                       Friday close 1179.27).

User signals approval ambiguously      Not treated as approval. The 18 Oct thumbs-up was clarified with a direct question;
                                       the job was created only after the explicit "Yes, do the rebalance".

User says stop                         Not covered in any job file - stated here as a main-chat convention, not a job rule: in
                                       the main chat, work on the challenge stops when the user says so. (A fired job itself
                                       carries no stop instruction; cancelling a not-yet-fired job is a main-chat action.)
```

Appendix A. Opening trade log - complete history as of this spec

All fills: Mon 12 Oct 2026, 06:30 Pacific (market open), mock fills - no real money moved. Recorded in portfolio.json and trades.log .

```
 Ticker                  Shares                Fill $              Cost $    Price source

 NVDA                   43.6148              229.28            10,000.00     MarketBeat instant alert, 12 Oct

 MSFT                   14.0169              535.07             7,500.02     MarketBeat instant alert, 12 Oct

 AMZN                   28.5790              262.43             7,499.99     American Banking News, 12 Oct

 META                    6.9573              718.67             5,000.00     American Banking News, 12 Oct

 JPM                    15.0146              333.01             5,000.01     Zolmax, 12 Oct

 LLY                     4.2328            1,181.24             4,999.95     Finnhub live quote (open)

 XOM                    29.2381              171.01             5,000.01     Finnhub live quote (open)

 GE                     16.2454              307.78             5,000.01     Finnhub live quote (open)
```

Pending: the approved Week 2 rebalance (sell 14.6190 XOM, buy NVDA with proceeds) at the Mon 19 Oct open - not yet a fill, so not in this log.

**Appendix B. Schedule inventory**

```
 Job ID                                      Fires (Pacific)          Purpose

  mock-challenge-open-fills                  12 Oct 2026, 06:40       Opening fills (done)

  mock-challenge-checkin-w1                  17 Oct 2026, 09:00       Week 1 check-in (done)

  mock-challenge-rebalance-w2                19 Oct 2026, 06:35       Approved XOM to NVDA rebalance

  mock-challenge-checkin-w2                  24 Oct 2026, 09:00       Week 2 check-in

  mock-challenge-checkin-w3                  31 Oct 2026, 09:00       Week 3 check-in

  mock-challenge-checkin-w4                  7 Nov 2026, 09:00        Week 4 check-in

  mock-challenge-checkin-w5                  14 Nov 2026, 09:00       Week 5 check-in

  mock-challenge-final                       21 Nov 2026, 09:00       Final valuation at the 20 Nov close; no further runs follow
```

Mock Stock Challenge - Platform Design Spec - 18 October 2026. All trades are mock fills; no real money is involved at any stage.
