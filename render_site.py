#!/usr/bin/env python3
"""Publish GitHub Pages from committed derived summaries, never raw OHLC or secrets."""
import shutil
from pathlib import Path

site = Path("site")
site.mkdir(exist_ok=True)
for name in ("latest.json", "live.json"):
    source = Path("derived") / name
    if source.is_file():
        shutil.copyfile(source, site / name)
# The page is a read-only display. All data may be delayed; the tick time is unknown.
(site / "index.html").write_text("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>XAU/USD • Near-live Study Monitor</title>
<style>
:root{color-scheme:dark}body{font:16px system-ui,-apple-system,sans-serif;background:#0c1220;color:#e5edf6;margin:0 auto;max-width:980px;padding:28px}
h1{font-size:1.8rem}h2{font-size:1.1rem}a{color:#8cbcff}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.card{padding:20px;border:1px solid #334155;border-radius:14px;background:#152033}
.big{font-size:2.3rem;font-weight:700;font-variant-numeric:tabular-nums}
.muted{color:#aabbd0}.warning{color:#fac980}.good{color:#a6f0c1}
pre{white-space:pre-wrap;word-break:break-word;background:#18263a;padding:14px;border-radius:8px;font-size:12px}
</style>
</head>
<body>
<h1>XAU/USD • Near-live Study Monitor</h1>
<p class="warning">Periodic data only. NOT a live broker bid/ask, trading signal, or guaranteed delivery interval.
Use your OANDA/MT5 quote for execution.</p>
<div class="grid">
<section class="card"><h2>Latest available quote</h2><div class="big" id="quote">Loading...</div>
<p class="muted" id="retrieved"></p><p class="warning" id="age"></p></section>
<section class="card"><h2>Last closed 5-minute candle</h2><div class="big" id="m5">Loading...</div>
<p class="muted" id="closed"></p></section>
</div>
<section class="card"><h2>Asia / London / New York 7-hour profiles</h2>
<pre id="session">Loading...</pre></section>
<section class="card"><h2>Recent M5 FVG candidates</h2><pre id="fvg">Loading...</pre></section>
<p><a href="live.json">Latest near-live data JSON</a> • <a href="latest.json">Detailed multi-timeframe JSON</a></p>
<p class="muted">The quote API provides request time but not exact tick time. Price, FVGs and session ranges can differ from your broker.</p>
<script>
const formatUTC = s => s ? new Date(s).toLocaleString(undefined,{dateStyle:"medium",timeStyle:"medium"}) : "unknown";
const $ = id => document.getElementById(id);
async function refresh(){
 try{
   const r = await fetch("live.json?t="+Date.now(),{cache:"no-store"});
   if(!r.ok)throw new Error("Live summary unavailable");
   const d = await r.json();
   $("quote").textContent = d.latest_price === null ? "Unavailable" : "$"+Number(d.latest_price).toFixed(3);
   $("retrieved").textContent = "API request: "+formatUTC(d.retrieved_utc)+" • Price tick time: unknown";
   const mins = (Date.now()-new Date(d.retrieved_utc).getTime())/60000;
   $("age").textContent = Number.isFinite(mins) ? "Snapshot age: "+Math.max(0,Math.round(mins))+" minutes"+(mins>20?" — STALE":"") : "Snapshot age unknown";
   $("m5").textContent = d.last_closed_5min?.close ?? "Unavailable";
   $("closed").textContent = "M5 closed: "+formatUTC(d.last_closed_5min?.close_utc);
   const p=d.ttrades_daily_profile||{};
   $("session").textContent=JSON.stringify({asia:p.asia_18_00_et,london:p.london_01_00_et,new_york:p.new_york_08_00_et},null,2);
   $("fvg").textContent=JSON.stringify(d.recent_unrevisited_m5_fvg_candidates||[],null,2);
 }catch(e){$("quote").textContent="No current snapshot";$("age").textContent=e.message;}
}
refresh();setInterval(refresh,60000);
</script></body></html>""", encoding="utf-8")
print("Published read-only HTML and derived JSON files to site/.")
