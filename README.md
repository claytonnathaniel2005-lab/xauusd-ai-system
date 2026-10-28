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

GitHub Actions is scheduled for 12:35 WIB and 18:35 WIB, weekdays. Cron is UTC. Each run makes **five** `/time_series` requests (one symbol each): five credits if standard Twelve Data pricing applies. This stays within an 8-credit-per-minute limit provided no other keys/apps are simultaneously consuming your allowance. GitHub scheduled jobs can start late. Your existing ChatGPT daily briefing runs approximately at 13:00 WIB; its scheduling can also vary.

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
