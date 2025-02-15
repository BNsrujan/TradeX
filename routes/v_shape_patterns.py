from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from math import atan2, degrees
from datetime import timedelta
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data


bp = Blueprint('v_shape_patterns', __name__)


@bp.route('/v-shape-patterns', methods=['GET'])
def get_v_shape_patterns():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')

    data1 = fetch_data_from_db(symbol, interval)
    if compare_db_current_date(symbol):
        data2 = fetch_currentday_data(symbol, interval)
    else:
        data2 = []
    data = data1 + data2

    df = pd.DataFrame(data)
    df.columns = [col.capitalize() for col in df.columns]
    df['Date'] = pd.to_datetime(df['Date'])

    def calculate_angle_v(p1, p2):
        return degrees(atan2(p2[1] - p1[1], p2[0] - p1[0]))

    def find_v_shapes(max_min):
        patterns_v = []
        dates = []
        for i in range(5, len(max_min)):
            window = max_min.iloc[i-5:i]

            if window.index[-1] - window.index[0] > 100:
                continue
            c = window.iloc[1]
            d = window.iloc[2]
            e = window.iloc[3]
            c_low = window.iloc[1]['Low']
            d_high = window.iloc[2]['High']
            e_low = window.iloc[3]['Low']

            date_c = window['Date'].iloc[1]
            date_d = window['Date'].iloc[2]
            date_e = window['Date'].iloc[3]

            if (c_low > d_high and d_high < e_low):
                if e.name - c.name < 9:  # Check if there are at least 8 candles
                    continue
                if abs(c['High'] - e['High']) <= 0.025 * c['High']:
                    length_cd = abs(c['High'] - d['Low'])
                    length_ce = abs(c['High'] - e['High'])

                    # Add the new condition: CD should be at least 2.5 times CE
                    if length_cd < (1.5 * length_ce):
                        continue
                    print(length_ce, length_cd)

                    length_de = abs(d['Low'] - e['High'])

                    if 0.9 * length_cd <= length_de <= 1.1 * length_cd:
                        angle_cd = calculate_angle_v(
                            [1, c['High']], [2, d['Low']])
                        angle_de = calculate_angle_v(
                            [2, d['Low']], [3, e['High']])

                        if -90 <= angle_cd <= -80 and 80 <= angle_de <= 90:
                            patterns_v.append((c['High'], d['Low'], e['High']))
                            dates.append([date_c, date_d, date_e])

        return patterns_v, dates

    def find_local_v(df, window, smooth=False, smoothing_period=3):
        local_max_arr = []
        local_min_arr = []

        if smooth:
            smooth_close = df['Close'].rolling(
                window=smoothing_period).mean().dropna()
            local_max = argrelextrema(smooth_close.values, np.greater)[0]
            local_min = argrelextrema(smooth_close.values, np.less)[0]
        else:
            local_max = argrelextrema(df['Close'].values, np.greater)[0]
            local_min = argrelextrema(df['Close'].values, np.less)[0]

        for i in local_max:
            if (i > window) and (i < len(df) - window):
                local_max_arr.append(
                    df.iloc[i - window:i + window]['Close'].idxmax())

        for i in local_min:
            if (i > window) and (i < len(df) - window):
                local_min_arr.append(
                    df.iloc[i - window:i + window]['Close'].idxmin())

        maxima = pd.DataFrame(df.loc[local_max_arr])
        minima = pd.DataFrame(df.loc[local_min_arr])
        max_min = pd.concat([maxima, minima]).sort_index()
        max_min = max_min[~max_min.index.duplicated()]
        return max_min

    window = 4
    max_min = find_local_v(df, window, smooth=True)
    patterns_v, dates = find_v_shapes(max_min)

    coordinates = []
    for pattern, date in zip(patterns_v, dates):
        coordinates.append({
            'x0': date[0].strftime('%Y-%m-%d %H:%M:%S'),
            'y0': pattern[0],
            'x1': date[1].strftime('%Y-%m-%d %H:%M:%S'),
            'y1': pattern[1],
            'x2': date[2].strftime('%Y-%m-%d %H:%M:%S'),
            'y2': pattern[2]
        })

    return jsonify(coordinates)
