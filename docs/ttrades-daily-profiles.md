# TTrades / ICT Daily Profile Playbook for XAUUSD

Version: 2026-10-28. Educational study notes from the user's supplied charts and TTrades' published lessons. This document is not a trading signal, an empirical win-rate claim, or an exact reproduction of a proprietary indicator.

## Two separate clocks: do not confuse them

1. **Seven-hour candles (TTrades 18/01/08 profile):** use **America/New_York** clock, automatically applying EDT/EST daylight-saving changes. The named bars start at **18:00 ET (Asia; ends 01:00 ET)**, **01:00 ET (London; ends 08:00 ET)** and **08:00 ET (New York; ends 15:00 ET)**. The 18/01/08 timestamps refer to the **START** of the corresponding 7h candle, not a guaranteed clock-minute reversal. They are not three consecutive H1 candles.
2. **ICT kill zones / session reference:** this repository separately tracks the 20:00–00:00 ET Asia indicator window, 02:00–05:00 ET London window, and 09:30–11:00 ET NY AM window. These do **not** equal the 7h candle windows. Do not combine their highs/lows without labeling them.
3. **WIB conversion:** during US EDT (UTC-4): 18:00 ET=05:00 WIB following day; 01:00 ET=12:00 WIB; 08:00 ET=19:00 WIB. During EST (UTC-5): 18:00 ET=06:00 WIB following day; 01:00 ET=13:00 WIB; 08:00 ET=20:00 WIB. Convert dates carefully.
4. The 18:45 WIB briefing is after the *London ICT 02–05 ET window* but **before** the London **7h** (01–08 ET) bar closes. It must say **PRELIMINARY**. A separate brief at 08:20 ET can use the completed 7h London bar if GitHub collection succeeds.

## Profiles learned from the user's screenshots and primary TTrades explanations

### 18:00 Asia reversal -> 01:00 London expansion -> 08:00 NY continuation
- Asia 7h makes a meaningful high/low at a relevant DAILY swing, not just arbitrary minute volatility.
- London 7h expands AWAY from the Asia extreme, demonstrating directional delivery.
- Expect NY 08:00 bar continuation **only while the validated continuation invalidation is respected**.
- If 01:00 bar instead manipulates through Asia extreme and reverses, reconsider as a *London reversal*.

### 01:00 London reversal -> 08:00 NY continuation
- Asia does not establish a valid reversal; London reaches/sweeps an HTF key level/liquidity and reverses with an actual M5/M15 CISD.
- Bullish: London sells into HTF support / raids lows, then bullish CISD; NY continuation could form after a higher low/retrace.
- Bearish: London buys into HTF resistance / raids highs, then bearish CISD; NY continuation could form after a lower high/retrace.
- DO NOT chase if London both reversed and completed a large expansion/ADR already.

### 08:00 New York reversal
- Asia and London fail to establish valid reversal at the important HTF PD array. London may extend toward, but not reach, the key level.
- NY must reach/sweep the still-untouched key level; require clear displacement and M5/M15 CISD. At 18:45 WIB this is an **unconfirmed scenario**.
- Bullish NY reversal: NY sweeps down into HTF support then bullish CISD. Bearish: NY raids up into HTF resistance then bearish CISD.
- This is the narrative in the user's images with an 08:00 reversal candle.

### New York manipulation (NY sweep of a London consolidation)
- London consolidates, leaving range liquidity.
- NY raids a range high (bearish possibility) or low (bullish possibility), then CISD and expansion away. 
- Asia/ London range sweep + FVG alone is NOT a confirmation.

### Seek and Destroy / NO TRADE
- London or NY raids both sides of Asia/ranges and fails to follow through; price tends to whipsaw and seek range equilibrium.
- Especially cautious ahead of major macro announcements such as FOMC.
- A both-sided mechanical sweep alone is a **warning**, not proof of a full Seek-and-Destroy day. If uncertain mark NO TRADE.

## TTrades 7h invalidation from user's 18/01/08 screenshots
- For an established **18:00 or 01:00 reversal -> 08:00 continuation**: TTrades describes a **50% level between the appropriate opposing swing and the 01:00 candle close** as continuation invalidation. 
- The swing MUST be validated as relevant, potentially via HTF context / lower-timeframe protected structure. The current program only extracts 2-left/2-right generic fractals. Therefore the system **must not fabricate this 50% level** and must not call it "protected swing" without verification.
- For an unconfirmed **08:00 NY reversal**, do not reuse the continuation invalidation formula; watch a NY raid into HTF level followed by CISD.
- Daily bias is upstream of the profile. The sequence is **D1 swing / bias -> 7h profile -> lower-timeframe model -> risk plan**.

## Execution filter for $5,000 prop account (user's stated constraints)
- A profile is an **environmental hypothesis**. Never output an executable entry because of the 7h candle classification alone.
- Require broker price/bid-ask verification; fresh, **closed** M5/M15 candles; validated HTF key level; actual CISD close through opposing candle run; structural stop beyond the protected swing; meaningful liquidity TP; demonstrated **reward/risk >= 2.0 after costs**.
- Conservative planned risk **<= USD 12.50 including spread, commission and expected slippage** *only if current loss buffer allows*. The user mentioned USD 100 total-loss breach; never imply that buffer is guaranteed.
- If HTF context, CISD, liquidity target, position size or macro calendar is missing or invalid => **WAIT / NO TRADE**, with reasons.
- Twelve Data XAU/USD differs from OANDA/MT5 execution feed; its synthetic 7h candles and provider D1 boundaries require broker verification. FOMC and other high-impact news must be confirmed from up-to-date official calendars.

## Data fields produced by fetch.py
- `ttrades_daily_profile.asia_18_00_et`, `.london_01_00_et`, `.new_york_08_00_et`: 7h OHLC from completed M5 bars, date-bounded, with status and bar count.
- `scenario_candidates`: basic mechanical shape **possibilities**, not verified CISD, TTrades ideal swing, TTFM confirmation, A+ signals or statistical probabilities.
- `mechanical_observations`: did London 7h cross Asia 7h high or low? London 7h equilibrium, relative bar body.
- The automation must supplement these fields with actual D1/H4 HTF narrative, relevant swing validation, key FVG/PD arrays, and economic calendar; never infer a true reversal solely from mechanical shape.
- Only report a completed London 7h model when `london_01_00_et.status == "complete"`; otherwise label provisional.

## Primary sources (official TTrades)

- https://ttrades.com/a-simple-3-step-trading-model-full-breakdown/
- https://ttrades.com/london-reversal-and-new-york-continuation-daily-profile/
- https://ttrades.com/understanding-the-new-york-reversal-in-daily-profiles/
- https://ttrades.com/daily-profile-understanding-the-new-york-manipulation/
- https://ttrades.com/understanding-the-seek-and-destroy-daily-profile-in-trading/

Definitions and heuristics in our script are **our conservative implementation** for educational screening, not claimed to be TTrades' proprietary algorithm.
