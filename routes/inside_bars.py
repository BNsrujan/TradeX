from flask import Blueprint, request, jsonify
import pandas as pd
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

bp = Blueprint('inside_bars', __name__)

@bp.route('/inside-bars', methods=['GET'])
def get_inside_bars():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')

    data1 = fetch_data_from_db(symbol, interval)
    if compare_db_current_date(symbol):
        data2 = fetch_currentday_data(symbol, interval)
    else:
        data2 = []
    data = data1 + data2

    if not data:
        return jsonify([])

    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    def detect_consecutive_ibars(df, max_inside_bars=12, height_ratio_threshold=0.6, similar_height_threshold=0.4, max_similar_height=2, body_to_wick_ratio=0.7):
        consecutive_ibars = [False] * len(df)
        i = 0
        while i < len(df) - 1:
            previous_candle = df.iloc[i]
            main_height = previous_candle['High'] - previous_candle['Low']
            main_body = abs(previous_candle['Open'] - previous_candle['Close'])
            main_wick = main_height - main_body

            # Check if the body is significantly larger than the wicks
            if main_wick == 0 or main_body / main_wick < body_to_wick_ratio:
                i += 1
                continue

            # Start looking for inside bars after the current candle
            j = i + 1
            count = 0
            similar_height_count = 0
            tall_inside_count = 0
            while j < len(df) and \
                (df.iloc[j]['High'] < previous_candle['High']) and \
                (df.iloc[j]['Low'] > previous_candle['Low']) and \
                (df.iloc[j]['Close'] < previous_candle['High']) and \
                    (df.iloc[j]['Open'] > previous_candle['Low']):

                inside_height = df.iloc[j]['High'] - df.iloc[j]['Low']
                if inside_height >= main_height * height_ratio_threshold:
                    similar_height_count += 1
                    if similar_height_count > max_similar_height:
                        break

                if inside_height >= main_height * similar_height_threshold:
                    tall_inside_count += 1

                count += 1
                j += 1

            # Check if the count of inside bars is within the allowed limit
            if count > 3 and count <= max_inside_bars and similar_height_count <= max_similar_height:
                if tall_inside_count / count < 0.5:  # Check if less than 50% of inside bars are tall
                    for k in range(i+1, j):
                        consecutive_ibars[k] = True
                    # Mark the larger candlestick as well
                    consecutive_ibars[i] = True
            # Move index to the end of the current sequence
            i = j if count == 0 else i + 1

        return consecutive_ibars

    df['ConsecutiveInsideBars'] = detect_consecutive_ibars(df)

    coordinates = []
    i = 0
    while i < len(df):
        if df['ConsecutiveInsideBars'][i]:
            start = i
            while i < len(df) and df['ConsecutiveInsideBars'][i]:
                i += 1
            end = i - 1

            x0 = df['Date'][start - 1] if start > 0 else df['Date'][start]
            x1 = df['Date'][end + 1] if end < len(df) - 1 else df['Date'][end]

            y0 = min(df['Low'][start:end+1])
            y1 = max(df['High'][start:end+1])

            coordinates.append({
                'x0': x0.strftime('%Y-%m-%d %H:%M:%S'),
                'x1': x1.strftime('%Y-%m-%d %H:%M:%S'),
                'y0': y0,
                'y1': y1
            })

            i = end + 1
        else:
            i += 1

    return jsonify(coordinates)

