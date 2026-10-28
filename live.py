#!/usr/bin/env python3
"""Near-live XAU/USD study snapshot; never publishes credentials or raw candles."""
import json
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


def main():
    if not API_KEY:
        raise RuntimeError("Set TWELVEDATA_API_KEY in GitHub Actions secrets")
    now = datetime.now(UTC)
    bars = intraday_closed(get_series("5min", 1000), "5min", now)
    if not bars:
        raise RuntimeError("No closed 5-minute candles")
    last = bars[-1]
    age_minutes = round((now - (last["dt"] + timedelta(minutes=5))).total_seconds()/60, 1)
    result = {
        "instrument": SYMBOL,
        "provider": "Twelve Data",
        "retrieved_utc": now.isoformat(),
        "latest_price": None,
        "quote_timestamp_utc": None,
        "quote_status": "unavailable",
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
        ],
        "trade_signal": "NONE — no automated broker-level execution confirmation",
    }
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
          "closed M5 age minutes:", age_minutes)


if __name__ == "__main__":
    main()
