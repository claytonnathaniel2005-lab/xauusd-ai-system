# XAU/USD Twelve Data → GitHub Pages → ChatGPT daily briefing

A **read-only, educational** starter pipeline. It fetches XAU/USD 5-minute, 15-minute, 1-hour, 4-hour and daily OHLC candles, then publishes a derived summary (not the raw candle history) to a read-only GitHub Pages URL. It does **not** send orders or provide an A+ trade signal. A scheduled ChatGPT briefing must separately be configured to read the URL, and live access is subject to source availability.

## Before deploying: important feed check

The first Twelve Data screenshot returned `status: ok`, but the user’s OANDA chart quotes around October 27, 2026 may differ by **tens of gold dollars** from the returned hourly candles at apparently corresponding timestamps. This is much larger than an ordinary spread. Do NOT execute a trade using levels from this feed until you compare **XAU/USD, the same UTC candle timestamp, and the same timeframe** against your execution broker. Twelve Data may use different aggregation/quotes. The screenshot also contained nearly flat Saturday bars; the script warns about such bars but does not implement comprehensive holiday/calendar filtering.

## GitHub setup (no Premium TradingView required)

1. On GitHub, create a **public repository** such as `xauusd-study`. Github Pages on GitHub Free works for public repositories. Read GitHub's Terms and Twelve Data's market-data redistribution policy before publishing derived figures. If you cannot publish the data, use the workflow's private artifacts instead; ChatGPT will not automatically be able to browse them.
2. Upload **the contents** of this folder, retaining `.github/workflows/xauusd.yml` and `fetch.py`. Do not upload your API key, request URL containing it or a `.env` file.
3. Go to **Settings → Secrets and variables → Actions → New repository secret**.
4. Secret name must be exactly `TWELVEDATA_API_KEY`, value is your private key (keep it secret).
5. Go to **Settings → Pages → Build and deployment → Source: GitHub Actions**.
6. Open **Actions → XAUUSD read-only candle snapshot → Run workflow**. Wait for the run result and inspect any errors (do not paste URLs containing your key).
7. When deployed, the public site will be `https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPOSITORY_NAME/`. A read-only summary is at `https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPOSITORY_NAME/latest.json`.
8. Share only the **public read-only summary URL** (never the API key) in ChatGPT and ask to add the URL to your existing scheduled Daily XAUUSD Bias automation.

## Schedule and limits

The **detailed** snapshots run at 12:35 WIB, 18:35 WIB, and around 08:10 America/New_York (19:10 WIB in EDT / 20:10 WIB in EST) on weekdays. The **lightweight** `live.py` snapshot is scheduled approximately every **5 minutes from 11:00–23:59 WIB on weekdays**, and every **15 minutes outside those hours on weekdays**, plus Sunday late UTC around FX reopening. The exact time is **not guaranteed** because GitHub Actions scheduling may be delayed. GitHub Actions cannot provide one-minute scheduled runs; these snapshots include the **last CLOSED M1 candle** when the Twelve Data 1min interval is available, not a tick-by-tick M1 stream. All schedules use GitHub Actions cron, which **can run late or occasionally skip**, and do not represent a real-time feed.

The lightweight job requests 1000 recent XAU/USD M5 candles and 500 recent XAU/USD M1 candles (1 API credit each), and attempts a latest-price quote through Twelve Data `/price` (1 API credit). If M1 is not entitled, this failure is explicit and does not prevent the rest of the snapshot. It records the last CLOSED M5 timestamp, FVG candidates and session profiles in `derived/live.json`, while the request-time-only quote is explicitly marked **exact tick timestamp unknown**. The full job makes five `/time_series` calls. Rough planning estimate is approximately **600–650 credits per active weekday**, depending on scheduled jobs and available instruments; check your individual Twelve Data plan, quota, licensing terms and actual consumption. The M1 series or the new quote endpoint may be unavailable under some entitlements; the M5 report can still succeed. This remains **not an OANDA/MT5 tradable bid/ask**. Use the broker quote for entries, and do not assume a 5-minute GitHub schedule guarantees 5-minute freshness.

Published read-only files:
- `/latest.json` — detailed but less-frequent D1/H4/H1/M15/M5 report.
- `/live.json` — faster quote request plus latest CLOSED M1 and M5, 7-hour sessions and study-only recent M1/M5 FVGs.
- `/` — browser dashboard displaying source timestamps and marking old snapshots stale. The page polls the published JSON every 60 seconds; this does **not** bypass GitHub's refresh delay.

Existing ChatGPT briefings remain at 13:00, 18:45 and 20:20 WIB. When asked for the current price, ChatGPT should attempt `derived/live.json`, verify its freshness, and separately search for a current timestamped public quote if needed. Without a broker/market-data app supporting live API calls, neither ChatGPT nor GitHub Pages can promise streaming tick prices.

## What the summary does and does not mean

- `timeframes`: last **completed intraday** candle, confirmed 2-left/2-right fractal highs and lows. These are confirmed **fractals**, not yet TTrades **protected swings** (which require additional candle-closure/CISD logic).
- `recent_unrevisited_fvg_candidates`: minimal 3-candle geometry; this is not a tested entry filter or an ICT/TTrades signal.
- `sessions`: the user's existing TradingView indicator windows in **America/New_York** time: Asia 20:00–00:00, London 02:00–05:00, NYAM 09:30–11:00. This is NOT a claim that these are the only possible ICT session definitions or TTrades 7-hour candle partitions. DST is handled by `zoneinfo`.
- `previous_UTC_calendar_day`: a UTC grouping of H1 bars, **not** the same thing as NY 17:00 rollover or broker PDH/PDL.
- `1day` timezone behavior: Twelve Data docs say timezone override does not apply to daily bars; the last returned daily candle may be incomplete.
- The script cannot know NewsX AI's proprietary signals, predict New York's future action, validate the AM Trades six-video playlist, or guarantee price levels will hold.

## Troubleshooting

- API error: verify entitlement to XAU/USD on `5min`, `15min`, `1h`, `4h`, `1day`. Each interval may have different limits.
- No page: verify Pages is set to **GitHub Actions**, repo Actions are enabled, and workflow succeeded.
- Quote discrepancy: compare two feeds at matching UTC timestamps, ask Twelve Data support about the source, and prefer your execution broker's historical data for live entries.
- Never expose API keys in source files, screenshots, browser addresses, workflow logs, or published artifacts.

## On-demand ChatGPT refresh: matching a quote to the user's request

This repository now supports a **user-requested GitHub workflow trigger** without exposing the Twelve Data API key. When the user asks ChatGPT for the current XAUUSD price, ChatGPT can use the connected GitHub app to update `refresh-requests/quote-refresh.json` on `main` with a unique `request_id` and UTC `requested_utc`, using a commit message beginning `Request XAUUSD quote refresh`. The push path on `.github/workflows/xauusd-live.yml` invokes `live.py` regardless of the delayed GitHub cron schedule.

A successful on-demand report should contain `on_demand_request.request_id` matching the just-submitted ID, its `requested_utc`, and `retrieved_utc` after the request. ChatGPT should check the GitHub workflow run status and `derived/live.json` before making a price claim. A snapshot from a different run or one whose request ID does not match is **not** proof that the specific refresh request completed. Check whether the report has reached GitHub Pages separately; Pages may deploy after the repository data is committed.

Interpret freshness conservatively: label a quote retrieval as **recent** only when it was requested after the user's question and the report is no more than about two minutes old when checked. If the run is queued, failed or delayed, say so rather than reporting an old quote as live. Never claim the timestamp equals the true Twelve Data tick time: the `/price` endpoint lacks that metadata. M1/M5 timestamps refer to last **closed** candles and may be older than `retrieved_utc`. A request can fail due to provider limits or GitHub queueing; do not poll indefinitely or retry aggressively. Never use a snapshot price as an OANDA/MT5 executable bid or ask.
