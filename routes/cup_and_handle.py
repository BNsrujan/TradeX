from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from math import degrees, atan2
from datetime import timedelta
from scipy.optimize import curve_fit
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

bp = Blueprint('cup_and_handle', __name__)

# Helper function for quadratic fit (parabolic cup shape)


def quadratic(x, a, b, c):
    return a * x ** 2 + b * x + c


@bp.route('/cup-and-handle', methods=['GET'])
def find_cup_and_handle():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')

    # Fetch data from the database
    data1 = fetch_data_from_db(symbol, interval)
    data2 = fetch_currentday_data(
        symbol, interval) if compare_db_current_date(symbol) else []
    data = data1 + data2

    if not data:
        return jsonify([])

    # Create DataFrame and preprocess
    df = pd.DataFrame(data)
    df.rename(columns={'Date': 'date', 'Open': 'open',
              'High': 'high', 'Low': 'low', 'Close': 'close'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    price_diff = np.mean(df['high'] - df['low'])

    # Helper function to find pivot highs
    def find_pivot_highs(df, window=5):
        highs = df['high']
        pivot_highs = []
        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i - window:i + window + 1]):
                pivot_highs.append(i)
        return pivot_highs

    # Helper function to detect cup and handle pattern
    def find_cup_and_handle_parabolic(df, pivot_highs, max_bars=100, price_tolerance=0.01):
        patterns = []
        for i in range(len(pivot_highs) - 1):
            for j in range(i + 1, len(pivot_highs)):
                if pivot_highs[j] - pivot_highs[i] <= max_bars and \
                   abs(df['high'][pivot_highs[i]] - df['high'][pivot_highs[j]]) <= price_tolerance * df['high'][pivot_highs[i]]:

                    start_idx = pivot_highs[i]
                    end_idx = pivot_highs[j]
                    x = np.arange(end_idx - start_idx + 1)
                    y = df['low'][start_idx:end_idx + 1].values

                    if len(x) > 2:
                        popt, _ = curve_fit(quadratic, x, y)
                        a, b, c = popt
                        if a > 0:
                            vertex = -b / (2 * a)
                            if 0 < vertex < end_idx - start_idx and 90 < (end_idx - start_idx) / abs(a) < 150:
                                depth = df['high'][start_idx] - \
                                    quadratic(vertex, a, b, c)
                                if depth > price_diff * 2:
                                    patterns.append(
                                        (start_idx, end_idx, vertex + start_idx, a, b, c))
        return patterns

    # Helper function to filter out overlapping patterns
    def filter_overlapping_cups(patterns, overlap_threshold=0.1):
        def are_overlapping(cup1, cup2):
            start_idx1, end_idx1 = cup1[:2]
            start_idx2, end_idx2 = cup2[:2]
            overlap_length = max(
                0, min(end_idx1, end_idx2) - max(start_idx1, start_idx2))
            cup1_length = end_idx1 - start_idx1
            cup2_length = end_idx2 - start_idx2
            total_length = cup1_length + cup2_length - overlap_length
            return overlap_length / total_length > overlap_threshold

        unique_patterns = []
        for pattern in patterns:
            if not any(are_overlapping(pattern, unique_pattern) for unique_pattern in unique_patterns):
                unique_patterns.append(pattern)
        return unique_patterns

    # Main code to detect and format patterns
    pivot_highs = find_pivot_highs(df)
    patterns = find_cup_and_handle_parabolic(df, pivot_highs)
    unique_patterns = filter_overlapping_cups(patterns)

    # Prepare JSON response
    coordinates = []
    for start_idx, end_idx, vertex_idx, a, b, c in unique_patterns:
        if end_idx < len(df):
            coordinates.append({
                'start_date': df['date'][start_idx].strftime('%Y-%m-%d %H:%M:%S'),
                'start_price': df['low'][start_idx],
                'end_date': df['date'][end_idx].strftime('%Y-%m-%d %H:%M:%S'),
                'end_price': df['low'][end_idx],
                'vertex_date': df['date'][int(vertex_idx)].strftime('%Y-%m-%d %H:%M:%S'),
                'vertex_price': quadratic(vertex_idx - start_idx, a, b, c),
                'handle_start_date': df['date'][end_idx + 1].strftime('%Y-%m-%d %H:%M:%S'),
                'handle_start_price': df['low'][end_idx + 1],
                'handle_end_date': df['date'][end_idx + (end_idx - start_idx) // 3].strftime('%Y-%m-%d %H:%M:%S'),
                'handle_end_price': df['low'][end_idx + (end_idx - start_idx) // 3],
            })
    return jsonify(coordinates)
