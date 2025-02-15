from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import math
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

bp = Blueprint('triangle', __name__)

@bp.route('/triangle')
def get_triangle():
    symbol = request.args.get('symbol', 'NSE:NIFTY50-INDEX')
    interval = request.args.get('interval', '5')

    # Fetch data
    data1 = fetch_data_from_db(symbol, interval)
    print(f"Fetched historical data: {len(data1)} records")
    if compare_db_current_date(symbol):
        data2 = fetch_currentday_data(symbol, interval)
        print(f"Fetched current day data: {len(data2)} records")
    else:
        data2 = []

    data = data1 + data2
    df = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close'])
    df.columns = ['date', 'open', 'high', 'low', 'close']
    df['date'] = pd.to_datetime(df['date'])

    climit = 2
    dlimit = 2
    prd = 2
    ilimit = len(df)
    print(f"Total data points: {ilimit}")

    # Identify support and resistance levels
    sup = df[df.low == df.low.rolling(prd * 2, center=True).min()].low
    res = df[
        (df.high == df.high.rolling(prd * 2, center=True).max()) & 
        (df['close'] < df['open'])
    ].high
    print(f"Support points identified: {len(sup)}")
    print(f"Resistance points identified: {len(res)}")

    pl = list(zip(sup.index, sup))
    ph = list(zip(res.index, res))

    uplines = []
    dnlines = []
    lines = []

    # Helper function to validate candles between trendline and horizontal line
    def validate_candles_within_bounds(candles, trendline, horizontal, pos_start, pos_end):
        inside_count = 0
        total_count = pos_end - pos_start + 1
        print(f"Validating candles within bounds: start={pos_start}, end={pos_end}")

        for pos in range(pos_start, pos_end + 1):
            # Calculate the expected trendline value at position
            trendline_value = trendline[1] + (pos - trendline[0]) * trendline[2]  # y = mx + c
            horizontal_value = horizontal

            # Check if the candle is inside the triangle boundaries
            if candles['low'][pos] >= min(trendline_value, horizontal_value) and \
               candles['high'][pos] <= max(trendline_value, horizontal_value):
                inside_count += 1

        coverage = inside_count / total_count
        print(f"Coverage of candles inside bounds: {coverage * 100:.2f}%")
        return coverage >= 0.6  # At least 60% inside

    # Upward Lines (Ascending Triangle)
    for i in range(len(pl) - 1, 0, -1):
        if pl[i][0] > ilimit:
            continue
        for j in range(0, i - 1):
            val1, val2 = pl[i][1], pl[j][1]
            pos1, pos2 = pl[i][0], pl[j][0]

            if val1 > val2:
                diff = (val1 - val2) / (pos1 - pos2)
                valid = True
                c = d = 0

                for x in range(j + 1, i):
                    hline = val2 + (pl[x][0] - pos2) * diff
                    if df['close'][pl[x][0]] < hline:
                        valid = False
                        break
                    elif df['low'][pl[x][0]] < hline * 1.005:
                        c += 1
                        d = 0
                    else:
                        d += 1
                        if d > dlimit:
                            valid = False
                            break

                # Validate candles inside the triangle
                trendline = (pos2, val2, diff)  # (start position, start value, slope)
                horizontal = val1
                if valid and validate_candles_within_bounds(df, trendline, horizontal, pos2, pos1):
                    angle_up = math.degrees(math.atan(diff))
                    if 40 <= angle_up <= 65:
                        line_length = abs(pos1 - pos2)
                        uplines.append((val1, val2, pos1, pos2, angle_up, line_length))
                    print(f"Valid ascending triangle found: start={pos2}, end={pos1}, angle={angle_up:.2f}")
                    ilimit = pl[j][0]
                    break

    # Downward Lines (Descending Triangle)
    ilimit = len(df)  # Reset ilimit for downward lines
    for i in range(len(ph) - 1, 0, -1):
        if ph[i][0] > ilimit:
            continue
        for j in range(0, i - 1):
            val1, val2 = ph[i][1], ph[j][1]
            pos1, pos2 = ph[i][0], ph[j][0]

            if val1 < val2:
                diff = (val1 - val2) / (pos1 - pos2)
                valid = True
                c = d = 0

                for x in range(j + 1, i):
                    hline = val2 + (ph[x][0] - pos2) * diff
                    if df['close'][ph[x][0]] > hline:
                        valid = False
                        break
                    elif df['high'][ph[x][0]] > hline * 0.995:
                        c += 1
                        d = 0
                    else:
                        d += 1
                        if d > dlimit:
                            valid = False
                            break

                # Validate candles inside the triangle
                trendline = (pos2, val2, diff)  # (start position, start value, slope)
                horizontal = val1
                if valid and validate_candles_within_bounds(df, trendline, horizontal, pos2, pos1):
                    angle_down = abs(math.degrees(math.atan(diff)))
                    if 50 <= angle_down <= 65:
                        line_length = abs(pos1 - pos2)
                        dnlines.append((val1, val2, pos1, pos2, angle_down, line_length))
                    print(f"Valid descending triangle found: start={pos2}, end={pos1}, angle={angle_down:.2f}")
                    ilimit = ph[j][0]
                    break

    # Format uptrend lines
    for up in uplines:
        lines.append([
            df['date'][up[3]].strftime('%Y-%m-%d %H:%M:%S'),
            up[1],
            df['date'][up[2]].strftime('%Y-%m-%d %H:%M:%S'),
            up[0],
            1,
            round(up[4], 2)
        ])
        lines.append([
            df['date'][up[2]].strftime('%Y-%m-%d %H:%M:%S'),
            up[0],
            df['date'][up[3]].strftime('%Y-%m-%d %H:%M:%S'),
            up[0],
            1,
            0
        ])

    # Format downtrend lines
    for dn in dnlines:
        lines.append([
            df['date'][dn[3]].strftime('%Y-%m-%d %H:%M:%S'),
            dn[1],
            df['date'][dn[2]].strftime('%Y-%m-%d %H:%M:%S'),
            dn[0],
            -1,
            round(dn[4], 2)
        ])
        lines.append([
            df['date'][dn[2]].strftime('%Y-%m-%d %H:%M:%S'),
            dn[0],
            df['date'][dn[3]].strftime('%Y-%m-%d %H:%M:%S'),
            dn[0],
            -1,
            0
        ])

    print(f"Total ascending triangles: {len(uplines)}")
    print(f"Total descending triangles: {len(dnlines)}")

    return jsonify(lines)