#!/usr/bin/env python3
"""Near-live XAU/USD study snapshot; never publishes credentials or raw candles."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

from fetch import (API_KEY, SYMBOL, UTC, get_series, intraday_closed,
                   recent_fvgs, swing_pivots, get_sessions,
                   ttrades_seven_hour_profile, roundv)


def get_latest_price():
    """Twelve Data /price is a quote lookup, NOT a timestamped broker tick."""
    query = urlencode({"symbol": SYMBOL, "apikey": API_KEY})
    url = "https://api.twelvedata.com/price?" + query
    try:
        with urlopen(url, timeout=20) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError("Twelve Data /price returned HTTP " + str(exc.code)) from None
    except URLError:
        raise RuntimeError("Twelve Data /price unavailable") from None
    if "price" not in payload:
        raise RuntimeError("Twelve Data /price returned no usable price: " +
                           str(payload.get("message", "unknown provider response")))
    value = float(payload["price"])
    if not (0 < value < 100000):
        raise RuntimeError("Twelve Data /price is not a plausible XAU/USD number")
    return roundv(value)



def on_demand_request_from_event():
    """Correlate this snapshot with a specific ChatGPT-triggered repository push."""
    if os.environ.get("GITHUB_EVENT_NAME") != "push":
        return None
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        return None
    try:
        event = json.loads(Path(path).read_text(encoding="utf-8"))
        commit = event.get("head_commit") or {}
        changed = set(commit.get("added") or []) | set(commit.get("modified") or [])
        if "refresh-requests/quote-refresh.json" not in changed:
            return None
        payload = json.loads(Path("refresh-requests/quote-refresh.json").read_text(encoding="utf-8"))
        request_id, request_time = payload.get("request_id"), payload.get("requested_utc")
        if not isinstance(request_id, str) or not isinstance(request_time, str):
            return None
        parsed = datetime.fromisoformat(request_time.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return {"request_id": request_id,
                "requested_utc": parsed.astimezone(UTC).isoformat(),
                "status": "trigger_recognized"}
    except (OSError, ValueError, TypeError, KeyError):
        return None


def main():
    if not API_KEY:
        raise RuntimeError("Set TWELVEDATA_API_KEY in GitHub Actions secrets")
    now = datetime.now(UTC)
    bars = intraday_closed(get_series("5min", 1000), "5min", now)
    if not bars:
        raise RuntimeError("No closed 5-minute candles")
    last = bars[-1]
    age_minutes = round((now - (last["dt"] + timedelta(minutes=5))).total_seconds()/60, 1)
    # M1 is optional by provider entitlement and NEVER uses an unclosed candle.
    # M1 data allows faster structure checks when the periodic workflow actually runs.
    minute_bar = None
    minute_status = "unavailable"
    minute_warning = None
    minute_fvgs = []
    minute_pivots = None
    try:
        m1_raw = get_series("1min", 500)
        m1_closed = [r for r in m1_raw if r["dt"] + timedelta(minutes=1) <= now]
        if not m1_closed:
            raise RuntimeError("Provider has not returned a completed M1 bar")
        m1 = m1_closed[-1]
        m1_age = round((now - (m1["dt"] + timedelta(minutes=1))).total_seconds()/60, 1)
        minute_bar = {
            "start_utc": m1["dt"].isoformat(),
            "close_utc": (m1["dt"] + timedelta(minutes=1)).isoformat(),
            "open": roundv(m1["open"]),
            "high": roundv(m1["high"]),
            "low": roundv(m1["low"]),
            "close": roundv(m1["close"]),
            "age_minutes_at_generation": m1_age,
        }
        minute_fvgs = recent_fvgs(m1_closed, keep=8)
        minute_pivots = swing_pivots(m1_closed, keep=6)
        minute_status = "fresh_at_generation" if m1_age <= 5 else "stale_at_generation"
    except (RuntimeError, ValueError, TypeError, KeyError, IndexError) as exc:
        minute_warning = "M1 feed unavailable or unsupported; no M1 inference. " + str(exc)
    result = {
        "instrument": SYMBOL,
        "provider": "Twelve Data",
        "retrieved_utc": now.isoformat(),
        "on_demand_request": on_demand_request_from_event(),
        "latest_price": None,
        "quote_timestamp_utc": None,
        "quote_status": "unavailable",
        "last_closed_1min": minute_bar,
        "minute_data_status": minute_status,
        "recent_unrevisited_m1_fvg_candidates": minute_fvgs,
        "confirmed_m1_fractal_pivots_not_protected_swings": minute_pivots,
        "last_closed_5min": {
            "start_utc": last["dt"].isoformat(),
            "close_utc": (last["dt"] + timedelta(minutes=5)).isoformat(),
            "open": roundv(last["open"]),
            "high": roundv(last["high"]),
            "low": roundv(last["low"]),
            "close": roundv(last["close"]),
            "age_minutes_at_generation": age_minutes,
        },
        "recent_unrevisited_m5_fvg_candidates": recent_fvgs(bars, keep=8),
        "confirmed_fractal_pivots_not_protected_swings": swing_pivots(bars, keep=6),
        "sessions": get_sessions(bars, now),
        "ttrades_daily_profile": ttrades_seven_hour_profile(bars, now),
        "data_status": "fresh_at_generation" if age_minutes <= 20 else "m5_stale_at_generation",
        "warnings": [
            "This is a delayed periodic snapshot, not a continuously streaming feed.",
            "Twelve Data /price does not return an exact tick timestamp. retrieved_utc is the REQUEST time, NOT the trade time.",
            "Provider quote is NOT an OANDA/MT5 executable bid/ask.",
            "FVGs and session profiles are study candidates, not confirmed CISD or trade signals.",
            "M1 requires a CLOSED 1-minute candle and fresh retrieval; this is not a live streaming feed.",
        ],
        "trade_signal": "NONE — no automated broker-level execution confirmation",
    }
    if minute_warning:
        result["warnings"].append(minute_warning)
    try:
        result["latest_price"] = get_latest_price()
        result["quote_status"] = "retrieved_from_price_endpoint_timestamp_unknown"
    except (RuntimeError, TypeError, ValueError) as exc:
        # Preserve the accurately timestamped M5 summary even if /price is not available.
        result["warnings"].append("Fresh quote unavailable; check the quote status. " + str(exc))
    out = Path("derived")
    out.mkdir(parents=True, exist_ok=True)
    (out / "live.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Wrote sanitized near-live XAUUSD summary; quote status:", result["quote_status"],
          "closed M5 age minutes:", age_minutes, "M1 status:", minute_status)


if __name__ == "__main__":
    main()
