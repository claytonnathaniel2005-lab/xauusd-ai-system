#!/usr/bin/env python3
"""Read-only XAU/USD market snapshot; publishes derived summary, never credentials or raw candles."""
import json
import os
from datetime import datetime, timezone, timedelta, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

API_KEY = os.environ.get('TWELVEDATA_API_KEY', '').strip()
SYMBOL = 'XAU/USD'
NY = ZoneInfo('America/New_York')
UTC = timezone.utc
INTERVALS = {'5min': 1000, '15min': 480, '1h': 500, '4h': 240, '1day': 100}
PERIODS = {'5min': timedelta(minutes=5), '15min': timedelta(minutes=15), '1h': timedelta(hours=1), '4h': timedelta(hours=4)}


def get_series(interval, outputsize):
    params = {'symbol': SYMBOL, 'interval': interval, 'outputsize': outputsize,
              'timezone': 'UTC', 'format': 'JSON', 'apikey': API_KEY}
    url = 'https://api.twelvedata.com/time_series?' + urlencode(params)
    try:
        with urlopen(url, timeout=20) as response:
            data = json.load(response)
    except HTTPError as e:
        raise RuntimeError('Twelve Data HTTP status ' + str(e.code)) from None
    except URLError:
        raise RuntimeError('Unable to reach Twelve Data endpoint') from None
    if data.get('status') != 'ok' and ('values' not in data):
        raise RuntimeError('Twelve Data returned an API error: ' + str(data.get('message', 'unknown')))
    rows = []
    for x in data.get('values', []):
        try:
            date = x['datetime']
            if interval == '1day':
                # Daily bars follow the provider's exchange-day boundary, NOT the request's UTC setting.
                dt = datetime.fromisoformat(date).replace(tzinfo=UTC)
            else:
                dt = datetime.fromisoformat(date).replace(tzinfo=UTC)
            row = {'dt': dt, 'open': float(x['open']), 'high': float(x['high']),
                   'low': float(x['low']), 'close': float(x['close'])}
            if row['low'] <= min(row['open'], row['close']) <= max(row['open'], row['close']) <= row['high']:
                rows.append(row)
        except (ValueError, KeyError, TypeError):
            continue
    rows.sort(key=lambda r: r['dt'])
    if not rows:
        raise RuntimeError('No valid OHLC bars available for ' + interval)
    return rows


def roundv(x):
    return round(x, 3)


def intraday_closed(rows, interval, now):
    if interval == '1day':
        return rows  # daily candle completion cannot be guaranteed from provider timezone alone
    dur = PERIODS[interval]
    return [r for r in rows if r['dt'] + dur <= now]


def swing_pivots(rows, left=2, right=2, keep=3):
    # A pivot is confirmed only after `right` subsequent CLOSED candles.
    highs, lows = [], []
    for i in range(left, len(rows)-right):
        w = rows[i-left:i+right+1]
        if all(rows[i]['high'] > r['high'] for j,r in enumerate(w) if j != left):
            highs.append({'time_utc': rows[i]['dt'].isoformat(), 'price': roundv(rows[i]['high'])})
        if all(rows[i]['low'] < r['low'] for j,r in enumerate(w) if j != left):
            lows.append({'time_utc': rows[i]['dt'].isoformat(), 'price': roundv(rows[i]['low'])})
    return {'confirmed_fractal_highs': highs[-keep:], 'confirmed_fractal_lows': lows[-keep:]}


def recent_fvgs(rows, keep=4):
    out = []
    for i in range(2, len(rows)):
        a, c = rows[i-2], rows[i]
        if c['low'] > a['high']:
            direction, low, high = 'bullish', a['high'], c['low']
            mitigated = any(z['low'] <= high for z in rows[i+1:])
        elif c['high'] < a['low']:
            direction, low, high = 'bearish', c['high'], a['low']
            mitigated = any(z['high'] >= low for z in rows[i+1:])
        else:
            continue
        if not mitigated:
            out.append({'formed_utc': c['dt'].isoformat(), 'direction':direction,
                        'low':roundv(low), 'high':roundv(high),
                        'status':'not subsequently touched by available bars'})
    return out[-keep:]


def session_range(rows, start_ny, end_ny, expected_mins):
    part = [r for r in rows if start_ny <= r['dt'].astimezone(NY) < end_ny]
    if not part:
        return {'status': 'not observed yet or not in returned history'}
    return {'status': 'complete' if len(part)*5 >= expected_mins else 'partial',
            'high':roundv(max(r['high'] for r in part)),
            'low':roundv(min(r['low'] for r in part)),
            'bars_seen':len(part),
            'start_ny':start_ny.isoformat(), 'end_ny':end_ny.isoformat()}


def get_sessions(m5, now):
    today = now.astimezone(NY).date()
    def d(date, hour, minute=0):
        return datetime.combine(date, time(hour, minute), NY)
    return {
        'asia_indicator_window_20_00_00_00_ET': session_range(m5, d(today-timedelta(days=1),20), d(today,0),240),
        'london_indicator_window_02_00_05_00_ET': session_range(m5, d(today,2),d(today,5),180),
        'ny_am_indicator_window_09_30_11_00_ET': session_range(m5, d(today,9,30),d(today,11),90),
    }


def quality_warnings(byint):
    messages = []
    h1 = byint['1h']
    for a,b in zip(h1[-60:-1],h1[-59:]):
        if abs(b['open']-a['close']) > 20 and (b['dt']-a['dt']) <= timedelta(hours=2):
            messages.append('Possible large quote discontinuity near ' + b['dt'].isoformat() +
                            '; verify against your execution broker (not necessarily an error).')
            break
    # Artificial flat weekend candles seen in user's first response: warn instead of treating as liquidity.
    for interval in ('1h','5min'):
        seq = byint[interval][-1000:]
        flat = sum(1 for z in seq if z['dt'].weekday() == 5 and z['high']-z['low'] < .5)
        if flat > 8:
            messages.append('Nearly flat Saturday bars detected on '+interval+'; do not interpret weekend bars as live liquidity.')
    return messages


def main():
    if not API_KEY:
        raise RuntimeError('Set TWELVEDATA_API_KEY as a GitHub Actions repository secret.')
    now = datetime.now(UTC)
    data = {interval: get_series(interval, size) for interval,size in INTERVALS.items()}
    closed = {interval: intraday_closed(rows,interval,now) for interval,rows in data.items()}
    summary = {
      'instrument': SYMBOL,
      'generated_utc': now.isoformat(),
      'provider': 'Twelve Data',
      'warning': ('DATA REVIEW ONLY. Not an executable trading signal; the Twelve Data feed may differ '
                  'materially from your OANDA/MT5 execution prices. D1 provider candle boundaries differ from UTC.'),
      'timeframes': {},
      'sessions': get_sessions(closed['5min'], now),
      'quality_warnings': quality_warnings(data),
      'trade_signal': 'none (confirmation not implemented)',
    }
    for interval in INTERVALS:
        arr = closed[interval]
        last = arr[-1]
        info = {'bars_returned':len(data[interval]),'last_bar_timestamp':last['dt'].isoformat(),
                'last_bar_close':roundv(last['close']),
                'last_bar_high':roundv(last['high']), 'last_bar_low':roundv(last['low']),
                'candle_status': 'UNVERIFIED: daily provider boundary' if interval=='1day' else 'closed by UTC bar duration',
                'pivots':swing_pivots(arr)}
        if interval in ('5min','15min','1h'):
            info['recent_unrevisited_fvg_candidates'] = recent_fvgs(arr)
        summary['timeframes'][interval] = info
    # Derive previous UTC calendar day range from H1 bars only; not necessarily the broker's daily candle.
    h1 = closed['1h']
    dates = sorted({r['dt'].date() for r in h1})
    if len(dates) >= 2:
        prevdate = now.date() - timedelta(days=1)
        prev = [r for r in h1 if r['dt'].date() == prevdate]
        if len(prev)>=18:
            summary['previous_UTC_calendar_day']={'date':str(prevdate), 'high':roundv(max(r['high'] for r in prev)),
                'low':roundv(min(r['low'] for r in prev)), 'note':'UTC calendar day, NOT necessarily broker PDH/PDL'}
    site = Path('site')
    site.mkdir(exist_ok=True)
    (site / 'latest.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (site / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>XAU/USD study snapshot</title><style>body{background:#101820;color:#e5edf6;font:16px system-ui;margin:auto;max-width:900px;padding:28px}pre{white-space:pre-wrap;word-break:break-word;background:#1d2939;padding:20px;border-radius:10px}a{color:#8cbcff}</style><h1>XAU/USD read-only market snapshot</h1><p>Derived levels for study only. Not a live trading signal. <a href="latest.json">Raw summary JSON</a></p><pre id="out">Loading...</pre><script>fetch('latest.json').then(r=>r.json()).then(d=>document.getElementById('out').textContent=JSON.stringify(d,null,2)).catch(()=>document.getElementById('out').textContent='Could not load the latest snapshot.')</script></html>''',encoding='utf-8')
    print('Wrote read-only derived study snapshot to site/. No API key or raw OHLC history published.')

if __name__=='__main__':
    main()
