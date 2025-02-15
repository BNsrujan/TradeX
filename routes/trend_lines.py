from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import math
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data
from datetime import datetime, timedelta, date


# bp = Blueprint('trend_lines', __name__)

# @bp.route('/trend-lines')
# def get_trend_lines():
#     symbol = request.args.get('symbol', 'NSE:NIFTY50-INDEX')
#     interval = int(request.args.get('interval', '5'))

#     # Fetch data from database
#     data1 = fetch_data_from_db(symbol, interval)
#     if compare_db_current_date(symbol):
#         data2 = fetch_currentday_data(symbol, interval)
#     else:
#         data2 = []
#     data = data1 + data2

#     df = pd.DataFrame(data)
#     if df.empty:
#         return jsonify([])

#     df = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close'])
#     df.columns = ['date', 'open', 'high', 'low', 'close']
#     df['date'] = pd.to_datetime(df['date'])

#     # For debugging
#     climit = 2
#     dlimit = 2
#     prd = 10
#     lines = []

#     sup = df[df.low == df.low.rolling(prd*2, center=True).min()].low
#     res = df[df.high == df.high.rolling(prd*2, center=True).max()].high
#     pl = list(zip(sup.index, sup))
#     ph = list(zip(res.index, res))

#     valid = False
#     uv1 = uv2 = up1 = up2 = 0
#     ilimit = len(df)
#     uplines = []

#     def date_range(start, end):
#         if start > end:
#             start, end = end, start
#         return set(start + timedelta(days=x) for x in range((end - start).days + 1))

#     def compare_date_ranges(range1, range2, overlap_threshold=0.5):
#         if not range1 or not range2:
#             return False  # Avoid comparing empty sets
#         overlap = len(range1.intersection(range2))
#         total_dates = len(range1.union(range2))
#         return overlap / total_dates >= overlap_threshold

#     uptrend_above = []
#     uptrend_below = []
#     downtrend_above = []
#     downtrend_below = []

#     for i in range(len(pl)-1, 0, -1):
#         if pl[i][0] > ilimit:
#             continue
#         for j in range(0, i-1):
#             val1 = pl[i][1]
#             val2 = pl[j][1]
#             pos1 = pl[i][0]
#             pos2 = pl[j][0]
#             if val1 > val2:
#                 diff = (val1 - val2) / (pos1 - pos2)

#                 hline = val2
#                 lloc = pos1
#                 lval = val1
#                 valid = True
#                 c = d = 0
#                 for x in range(j+1, i):
#                     hline = val2 + (pl[x][0] - pos2) * diff
#                     if df['close'][pl[x][0]] < hline:
#                         valid = False
#                         break
#                     elif df['low'][pl[x][0]] < hline * (1.006):
#                         c += 1
#                         d = 0
#                     else:
#                         d += 1
#                         if d > dlimit:
#                             valid = False
#                             break

#                 if valid and i-j > 2 and c > climit:
#                     uv1 = lval
#                     uv2 = val2
#                     up1 = lloc
#                     up2 = pos2
#                     angle_up = math.degrees(math.atan(diff))
#                     print(
#                         f"Angle_up_below_candles_green: {angle_up}° between points ({up1}, {uv1}) and ({up2}, {uv2})")
#                     uplines.append((uv1, uv2, up1, up2, angle_up))
#                     uv1 = uv2 = up1 = up2 = 0
#                     ilimit = pl[j][0]
#                     break

#     valid = False
#     dv1 = dv2 = dp1 = dp2 = 0
#     ilimit = len(df)
#     dnlines = []

#     for i in range(len(ph)-1, 0, -1):
#         if ph[i][0] > ilimit:
#             continue
#         for j in range(0, i-1):
#             val1 = ph[i][1]
#             val2 = ph[j][1]
#             pos1 = ph[i][0]
#             pos2 = ph[j][0]
#             if val1 < val2:
#                 diff = (val2 - val1) / (pos1 - pos2)
#                 hline = val2
#                 lloc = pos1
#                 lval = val1
#                 valid = True
#                 c = d = 0
#                 for x in range(j+1, i):
#                     hline = val2 - (ph[x][0] - pos2) * diff
#                     if df['close'][ph[x][0]] > hline:
#                         valid = False
#                         break
#                     elif df['high'][ph[x][0]] > hline * 0.995:
#                         c += 1
#                         d = 0
#                     else:
#                         d += 1
#                         if d > dlimit:
#                             valid = False
#                             break

#                 if valid and i-j > 2 and c > climit:
#                     dv1 = lval
#                     dv2 = val2
#                     dp1 = lloc
#                     dp2 = pos2
#                     angle_down = math.degrees(math.atan(diff))
#                     print(
#                         f"Angle_down_above_candles_red: {angle_down}° between points ({dp1}, {dv1}) and ({dp2}, {dv2})")
#                     dnlines.append((dv1, dv2, dp1, dp2, angle_down))
#                     dv1 = dv2 = dp1 = dp2 = 0
#                     ilimit = ph[j][0]
#                     break

#     valid = False
#     uv1 = uv2 = up1 = up2 = 0
#     ilimit = len(df)

#     for i in range(len(ph)-1, 0, -1):
#         if ph[i][0] > ilimit:
#             continue
#         for j in range(0, i-1):
#             val1 = ph[i][1]
#             val2 = ph[j][1]
#             pos1 = ph[i][0]
#             pos2 = ph[j][0]
#             if val1 > val2:
#                 diff = (val1 - val2) / (pos1 - pos2)
#                 hline = val2
#                 lloc = pos2
#                 lval = hline
#                 valid = True
#                 c = d = 0
#                 for x in range(j+1, i):
#                     hline = val2 + (ph[x][0] - pos2) * diff
#                     if df['close'][ph[x][0]] > hline:
#                         valid = False
#                         break
#                     elif df['high'][ph[x][0]] > hline * 0.995:
#                         c += 1
#                         d = 0
#                     else:
#                         d += 1
#                         if d > dlimit:
#                             valid = False
#                             break

#                 if valid and i-j > 2 and c > climit:
#                     uv1 = lval
#                     uv2 = val1
#                     up1 = lloc
#                     up2 = pos1
#                     angle_up = math.degrees(math.atan(diff))
#                     print(
#                         f"Angle_up_above_candles_green: {angle_up}° between points ({up1}, {uv1}) and ({up2}, {uv2})")
#                     uplines.append((uv1, uv2, up1, up2, angle_up))
#                     uv1 = uv2 = up1 = up2 = 0
#                     ilimit = ph[j][0]
#                     break

#     valid = False
#     dv1 = dv2 = dp1 = dp2 = 0
#     ilimit = len(df)

#     for i in range(len(pl)-1, 0, -1):
#         if pl[i][0] > ilimit:
#             continue
#         for j in range(0, i-1):
#             val1 = pl[i][1]
#             val2 = pl[j][1]
#             pos1 = pl[i][0]
#             pos2 = pl[j][0]
#             if val1 < val2:
#                 diff = (val2 - val1) / (pos1 - pos2)
#                 hline = val2
#                 lloc = pos2
#                 lval = hline
#                 valid = True
#                 c = d = 0
#                 for x in range(j+1, i):
#                     hline = val2 - (pl[x][0] - pos2) * diff
#                     if df['close'][pl[x][0]] < hline:
#                         valid = False
#                         break
#                     elif df['low'][pl[x][0]] < hline * 1.005:
#                         c += 1
#                         d = 0
#                     else:
#                         d += 1
#                         if d > dlimit:
#                             valid = False
#                             break

#                 if valid and i-j > 2 and c > climit:
#                     dv1 = lval
#                     dv2 = val1
#                     dp1 = lloc
#                     dp2 = pos1
#                     angle_down = math.degrees(math.atan(diff))
#                     print(
#                         f"Angle_down_below_candles_red: {angle_down}° between points ({dp1}, {dv1}) and ({dp2}, {dv2})")
#                     dnlines.append((dv1, dv2, dp1, dp2, angle_down))
#                     dv1 = dv2 = dp1 = dp2 = 0
#                     ilimit = pl[j][0]
#                     break
#     angle_difference_tolerance = 10
#     # Store dates for each type of trend line
#     for up in uplines:
#         start_date = df['date'][up[3]].date()
#         end_date = df['date'][up[2]].date()
#         date_set = date_range(start_date, end_date)

#         # Debugging: print date range info
#         print(
#             f"Uptrend Start date: {start_date}, End date: {end_date}, Date range: {date_set}")

#         if up[1] > up[0]:  # Check above candles
#             uptrend_above.append((date_set, up))
#         else:  # Below candles
#             uptrend_below.append((date_set, up))

#     for dn in dnlines:
#         start_date = df['date'][dn[3]].date()
#         end_date = df['date'][dn[2]].date()
#         date_set = date_range(start_date, end_date)

#         # Debugging: print date range info
#         print(
#             f"Downtrend Start date: {start_date}, End date: {end_date}, Date range: {date_set}")

#         if dn[1] > dn[0]:  # Above candles
#             downtrend_above.append((date_set, dn))
#         else:  # Below candles
#             downtrend_below.append((date_set, dn))

#     # Compare and filter lines based on date overlap
#     uptrend_channels = []
#     for above in uptrend_above:
#         for below in uptrend_below:
#             #  if compare_date_ranges(above[0], below[0]):
#             #     uptrend_channels.append((above[1], below[1]))

#             if compare_date_ranges(above[0], below[0]) and abs(above[1][4] - below[1][4]) <= angle_difference_tolerance:
#                 uptrend_channels.append((above[1], below[1]))

#     downtrend_channels = []
#     for above in downtrend_above:
#         for below in downtrend_below:
#             #  if compare_date_ranges(above[0], below[0]):
#             #     downtrend_channels.append((above[1], below[1]))

#             if compare_date_ranges(above[0], below[0]) and abs(above[1][4] - below[1][4]) <= angle_difference_tolerance:
#                 downtrend_channels.append((above[1], below[1]))
#     # Prepare the output
#     output_lines = []
#     for channel in uptrend_channels + downtrend_channels:
#         for line in channel:
#             output_lines.append([
#                 df['date'][line[3]].strftime('%Y-%m-%d %H:%M:%S'),
#                 line[1],
#                 df['date'][line[2]].strftime('%Y-%m-%d %H:%M:%S'),
#                 line[0],
#                 1 if line in uplines else 0,
#                 round(line[4], 2)  # The angle
#             ])

#     # Debugging: Print output lines to verify
#     print(f"Output lines: {output_lines}")

#     return jsonify(output_lines)


bp = Blueprint('trend_lines', __name__)


@bp.route('/trend-lines')
def get_trend_lines():
    symbol = request.args.get('symbol', 'NSE:NIFTY50-INDEX')
    interval = int(request.args.get('interval', '5'))
    # New parameter to determine the mode
    mode = request.args.get('mode', 'trend_lines')

    # Fetch data from database
    data1 = fetch_data_from_db(symbol, interval)
    if compare_db_current_date(symbol):
        data2 = fetch_currentday_data(symbol, interval)
    else:
        data2 = []
    data = data1 + data2

    df = pd.DataFrame(data)
    if df.empty:
        return jsonify([])

    df = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close'])
    df.columns = ['date', 'open', 'high', 'low', 'close']
    df['date'] = pd.to_datetime(df['date'])

    # For debugging
    # Initialize mode-specific variables for climit, dlimit, and prd
    if mode == 'trend_lines':
        climit = 5
        dlimit = 2
        prd = 10
    elif mode == 'parallel_channels':
        climit = 2
        dlimit = 2
        prd = 10

    lines = []

    sup = df[df.low == df.low.rolling(prd*2, center=True).min()].low
    res = df[df.high == df.high.rolling(prd*2, center=True).max()].high
    pl = list(zip(sup.index, sup))
    ph = list(zip(res.index, res))

    def calculate_trend_lines(pl, ph):
        uplines = []
        dnlines = []

        # First loop: Uptrend below candles
        valid = False
        uv1 = uv2 = up1 = up2 = 0
        ilimit = len(df)
        for i in range(len(pl)-1, 0, -1):
            if pl[i][0] > ilimit:
                continue
            for j in range(0, i-1):
                val1 = pl[i][1]
                val2 = pl[j][1]
                pos1 = pl[i][0]
                pos2 = pl[j][0]
                if val1 > val2:
                    diff = (val1 - val2) / (pos1 - pos2)
                    hline = val2
                    lloc = pos1
                    lval = val1
                    valid = True
                    c = d = 0
                    for x in range(j+1, i):
                        hline = val2 + (pl[x][0] - pos2) * diff
                        if df['close'][pl[x][0]] < hline:
                            valid = False
                            break
                        elif df['low'][pl[x][0]] < hline * (1.006):
                            c += 1
                            d = 0
                        else:
                            d += 1
                            if d > dlimit:
                                valid = False
                                break

                    if valid and i-j > 2 and c > climit:
                        uv1 = lval
                        uv2 = val2
                        up1 = lloc
                        up2 = pos2
                        angle_up = math.degrees(math.atan(diff))
                        uplines.append((uv1, uv2, up1, up2, angle_up))
                        uv1 = uv2 = up1 = up2 = 0
                        ilimit = pl[j][0]
                        break

        # Second loop: Downtrend above candles
        valid = False
        dv1 = dv2 = dp1 = dp2 = 0
        ilimit = len(df)
        for i in range(len(ph)-1, 0, -1):
            if ph[i][0] > ilimit:
                continue
            for j in range(0, i-1):
                val1 = ph[i][1]
                val2 = ph[j][1]
                pos1 = ph[i][0]
                pos2 = ph[j][0]
                if val1 < val2:
                    diff = (val2 - val1) / (pos1 - pos2)
                    hline = val2
                    lloc = pos1
                    lval = val1
                    valid = True
                    c = d = 0
                    for x in range(j+1, i):
                        hline = val2 - (ph[x][0] - pos2) * diff
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

                    if valid and i-j > 2 and c > climit:
                        dv1 = lval
                        dv2 = val2
                        dp1 = lloc
                        dp2 = pos2
                        angle_down = math.degrees(math.atan(diff))
                        dnlines.append((dv1, dv2, dp1, dp2, angle_down))
                        dv1 = dv2 = dp1 = dp2 = 0
                        ilimit = ph[j][0]
                        break

        # Third loop: Uptrend above candles
        valid = False
        uv1 = uv2 = up1 = up2 = 0
        ilimit = len(df)
        for i in range(len(ph)-1, 0, -1):
            if ph[i][0] > ilimit:
                continue
            for j in range(0, i-1):
                val1 = ph[i][1]
                val2 = ph[j][1]
                pos1 = ph[i][0]
                pos2 = ph[j][0]
                if val1 > val2:
                    diff = (val1 - val2) / (pos1 - pos2)
                    hline = val2
                    lloc = pos2
                    lval = hline
                    valid = True
                    c = d = 0
                    for x in range(j+1, i):
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

                    if valid and i-j > 2 and c > climit:
                        uv1 = lval
                        uv2 = val1
                        up1 = lloc
                        up2 = pos1
                        angle_up = math.degrees(math.atan(diff))
                        uplines.append((uv1, uv2, up1, up2, angle_up))
                        uv1 = uv2 = up1 = up2 = 0
                        ilimit = ph[j][0]
                        break

        # Fourth loop: Downtrend below candles
        valid = False
        dv1 = dv2 = dp1 = dp2 = 0
        ilimit = len(df)
        for i in range(len(pl)-1, 0, -1):
            if pl[i][0] > ilimit:
                continue
            for j in range(0, i-1):
                val1 = pl[i][1]
                val2 = pl[j][1]
                pos1 = pl[i][0]
                pos2 = pl[j][0]
                if val1 < val2:
                    diff = (val2 - val1) / (pos1 - pos2)
                    hline = val2
                    lloc = pos2
                    lval = hline
                    valid = True
                    c = d = 0
                    for x in range(j+1, i):
                        hline = val2 - (pl[x][0] - pos2) * diff
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

                    if valid and i-j > 2 and c > climit:
                        dv1 = lval
                        dv2 = val1
                        dp1 = lloc
                        dp2 = pos1
                        angle_down = math.degrees(math.atan(diff))
                        dnlines.append((dv1, dv2, dp1, dp2, angle_down))
                        dv1 = dv2 = dp1 = dp2 = 0
                        ilimit = pl[j][0]
                        break

        return uplines, dnlines

    uplines, dnlines = calculate_trend_lines(pl, ph)

    if mode == 'trend_lines':
        # Use the original trend lines logic
        for up in uplines:
            lines.append([
                df['date'][up[3]].strftime('%Y-%m-%d %H:%M:%S'),
                up[1],
                df['date'][up[2]].strftime('%Y-%m-%d %H:%M:%S'),
                up[0],
                1,
                round(up[4], 2)
            ])

        for dn in dnlines:
            lines.append([
                df['date'][dn[3]].strftime('%Y-%m-%d %H:%M:%S'),
                dn[1],
                df['date'][dn[2]].strftime('%Y-%m-%d %H:%M:%S'),
                dn[0],
                0,
                round(dn[4], 2)
            ])

    elif mode == 'parallel_channels':
        def date_range(start, end):
            if start > end:
                start, end = end, start
            return set(start + timedelta(days=x) for x in range((end - start).days + 1))

        def compare_date_ranges(range1, range2, overlap_threshold=0.5):
            if not range1 or not range2:
                return False
            overlap = len(range1.intersection(range2))
            total_dates = len(range1.union(range2))
            return overlap / total_dates >= overlap_threshold

        angle_difference_tolerance = 10

        uptrend_above = []
        uptrend_below = []
        downtrend_above = []
        downtrend_below = []

        # Categorize trend lines
        for up in uplines:
            start_date = df['date'][up[3]].date()
            end_date = df['date'][up[2]].date()
            date_set = date_range(start_date, end_date)
            if up[1] > up[0]:
                uptrend_above.append((date_set, up))
            else:
                uptrend_below.append((date_set, up))

        for dn in dnlines:
            start_date = df['date'][dn[3]].date()
            end_date = df['date'][dn[2]].date()
            date_set = date_range(start_date, end_date)
            if dn[1] > dn[0]:
                downtrend_above.append((date_set, dn))
            else:
                downtrend_below.append((date_set, dn))

        # Find parallel channels
        uptrend_channels = []
        for above in uptrend_above:
            for below in uptrend_below:
                if compare_date_ranges(above[0], below[0]) and abs(above[1][4] - below[1][4]) <= angle_difference_tolerance:
                    uptrend_channels.append((above[1], below[1]))

        downtrend_channels = []
        for above in downtrend_above:
            for below in downtrend_below:
                if compare_date_ranges(above[0], below[0]) and abs(above[1][4] - below[1][4]) <= angle_difference_tolerance:
                    downtrend_channels.append((above[1], below[1]))

        # Prepare output for parallel channels
        for channel in uptrend_channels + downtrend_channels:
            for line in channel:
                lines.append([
                    df['date'][line[3]].strftime('%Y-%m-%d %H:%M:%S'),
                    line[1],
                    df['date'][line[2]].strftime('%Y-%m-%d %H:%M:%S'),
                    line[0],
                    1 if line in uplines else 0,
                    round(line[4], 2)
                ])

    return jsonify(lines)
