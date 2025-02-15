from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from math import degrees, atan2
from datetime import timedelta
from sklearn.linear_model import LinearRegression
from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from math import degrees, atan2
from datetime import timedelta
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data
from datetime import date
from time import sleep
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
from bs4 import BeautifulSoup
from flask import Flask, render_template
import requests
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from scipy.signal import argrelextrema
# import pandas_ta as ta
import plotly.io as pio
from sklearn.cluster import DBSCAN
import json
from fyers_apiv3 import fyersModel
import datetime as dt
import plotly
import pyotp
import mysql.connector
from urllib.parse import parse_qs, urlparse
import base64
import warnings
from math import atan2, degrees, sqrt
import pytz
import math
import requests
from time import sleep
from datetime import datetime, timedelta, date
import webbrowser
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
# from flask_mail import Mail, Message
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
# import pandas_ta as ta
import plotly.io as pio
from sklearn.linear_model import LinearRegression
import json
from fyers_apiv3 import fyersModel
import os
import datetime as dt
import plotly
import pyotp
import mysql.connector
import csv
from scipy.optimize import curve_fit
from scipy.optimize import OptimizeWarning
from datetime import datetime, timedelta


# Database connection configuration
db_config3 = {
    'host': '118.139.182.3',
    'user': 'sqluser1',
    'password': 'TGDp0U&[1Y4S',
    'database': 'stocks'
}

# Function to create a MySQL connection


def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config3)
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection
# Function to get the previous working day (skip weekends)


def get_previous_working_day():
    today = datetime.now()
    previous_day = today - timedelta(days=1)

    # If the previous day is Saturday or Sunday, adjust to Friday
    if previous_day.weekday() == 5:  # Saturday
        previous_day -= timedelta(days=1)
    elif previous_day.weekday() == 6:  # Sunday
        previous_day -= timedelta(days=2)

    return previous_day.strftime('%Y-%m-%d')

# Function to fetch the previous day's close price for Nifty 50 stocks


def fetch_previous_close_price(symbol):
    con = create_connection()
    cur = con.cursor()

    # Normalize the symbol name to match your database table naming convention
    sym = symbol.split(':')[-1].replace('-', '_').replace('&', '_').lower()

    # Check if the table for the symbol exists in the database
    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'stocks'"
    )
    tables = cur.fetchall()
    tables = [table[0] for table in tables]

    if sym not in tables:
        print(f"Table for {symbol} does not exist in the database.")
        con.close()
        return None

    # Get the previous working day
    previous_working_day = get_previous_working_day()

    # SQL query to fetch the close price for the previous working day
    query = f"""
        SELECT `close`
        FROM {sym}
        WHERE DATE(`date`) = %s
        ORDER BY `date` DESC
        LIMIT 1;
    """

    cur.execute(query, (previous_working_day,))
    result = cur.fetchone()

    con.close()

    if result:
        return {
            'Symbol': symbol,
            'Date': previous_working_day,
            'Close': result[0]
        }
    else:
        print(f"No data found for {symbol} on {previous_working_day}.")
        return None

# Function to write the data to a CSV file


def write_to_csv(data, filename="preclose_prices.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['Symbol', 'Date', 'Close'])
        writer.writeheader()
        writer.writerows(data)


nifty_50_symbols = ["NSE:NIFTY50-INDEX", "NSE:NIFTYBANK-INDEX", "NSE:RELIANCE-EQ", "NSE:TCS-EQ",
                    "NSE:HCLTECH-EQ", "NSE:WIPRO-EQ", "NSE:IRCTC-EQ"]  # Add more stock symbols as needed
preclose_data = []

for symbol in nifty_50_symbols:
    close_price = fetch_previous_close_price(symbol)
    if close_price:
        preclose_data.append(close_price)

write_to_csv(preclose_data)
print(f"Preclose prices written to preclose_prices.csv")

# Function to fetch data from the database


def fetch_data_from_db(symbol, interval):
    con = create_connection()
    cur = con.cursor()

    # Normalize the symbol name to match your database table naming convention
    sym = symbol.split(':')[-1].replace('-', '_').replace('&', '_').lower()

    # Check if the table for the symbol exists in the database
    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'stocks'")
    tables = cur.fetchall()
    tables = [table[0] for table in tables]

    if sym not in tables:
        print(f"Table for {symbol} does not exist in the database.")
        con.close()
        return []

    # SQL query to fetch data for specified interval
    query = f"""
        SELECT t.INTERVAL_START AS `Interval`, t.`Open`, t.`High`, t.`Low`, ae.`Close`, t.`Volume`
        FROM (
            SELECT
                (UNIX_TIMESTAMP(`date`) - (UNIX_TIMESTAMP(DATE_FORMAT(`date`, '%Y-%m-%d 09:15:00')))) DIV ({interval} * 60) + UNIX_TIMESTAMP(DATE_FORMAT(`date`, '%Y-%m-%d 09:15:00')) AS interval_id,
                MIN(`date`) AS INTERVAL_START,
                `open` AS `Open`,
                MAX(`high`) AS `High`,
                MIN(`low`) AS `Low`,
                MAX(`date`) AS max_date,
                 SUM(`volume`) AS `Volume`
            FROM {sym}
            GROUP BY interval_id
            ORDER BY max_date DESC
            LIMIT 5000
        ) AS t
        INNER JOIN {sym} ae ON ae.`date` = t.max_date
        ORDER BY t.max_date ASC;
    """

    cur.execute(query)
    rows = cur.fetchall()

    # Storing data
    seen = set()
    data = []
    for row in rows:
        row_data = {
            'Date': row[0].strftime('%Y-%m-%d %H:%M:%S'),
            'Open': row[1],
            'High': row[2],
            'Low': row[3],
            'Close': row[4],
            'Volume': row[5]
        }
        # Convert dict to tuple for hashable set
        row_tuple = tuple(row_data.items())
        if row_tuple not in seen:
            seen.add(row_tuple)
            data.append(row_data)

    con.close()
    return data

# Function to detect inside bars (iBars) and return datetime ranges

def detect_consecutive_ibars(df, interval, max_inside_bars=12, height_ratio_threshold=0.6, similar_height_threshold=0.4, max_similar_height=2, body_to_wick_ratio=0.7):
    consecutive_ibars = [False] * len(df)
    i = 0
    inside_bar_ranges = []  # To store datetime ranges of detected patterns

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
                start_time = df.iloc[i]['Date']  # Start of the pattern
                end_time = df.iloc[j-1]['Date']  # End of the pattern
                inside_bar_ranges.append(f"{start_time} - {end_time}")
        # Move index to the end of the current sequence
        i = j if count == 0 else i + 1
    days = 5
    today = datetime.now()
    # Start date (from 5 days before yesterday)
    start_date = today - timedelta(days=days+1)
    end_date = today - timedelta(days=1)  # End date (yesterday)

    # Filter date ranges based on the condition
    filtered_ranges = []
    for date_range in inside_bar_ranges:
        start_str, end_str = date_range.split(" - ")
        range_start = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        range_end = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')

        # Check if the range falls within the last 5 days
        if start_date <= range_start <= end_date and start_date <= range_end <= end_date:
            filtered_ranges.append(date_range)
    # print(filtered_ranges)
    return filtered_ranges


# Function to detect double tops and return datetime ranges


def detect_double_tops(df):
    def calculate_angle_and_validate(p1, p2, angle_min, angle_max):
        x1, y1 = p1
        x2, y2 = p2
        angle = degrees(atan2(y2 - y1, x2 - x1))
        return angle_min <= angle <= angle_max

    # Function to calculate the length between two points
    def calculate_length_dtop(p1, p2):
        return np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

    def find_doubles_patterns(max_min):
        patterns_tops = []
        dates = []

        for i in range(5, len(max_min)):
            window = max_min.iloc[i-5:i]

            if window.index[-1] - window.index[0] > 50:
                continue

            a = window.iloc[0]['Close']
            b = window.iloc[1]['Close']
            c = window.iloc[2]['Close']
            d = window.iloc[3]['Close']
            e = window.iloc[4]['Close']

            date_a = window['Date'].iloc[0]
            date_b = window['Date'].iloc[1]
            date_c = window['Date'].iloc[2]
            date_d = window['Date'].iloc[3]
            date_e = window['Date'].iloc[4]

            a_high = window.iloc[0]['High']
            b_low = window.iloc[1]['Low']
            c_low = window.iloc[2]['Low']
            c_high = window.iloc[2]['High']
            d_high = window.iloc[3]['High']
            d_low = window.iloc[3]['Low']
            e_low = window.iloc[4]['Low']
            e_high = window.iloc[4]['High']

            a_high = window.iloc[0]['High']
            b_low = window.iloc[1]['Low']

            # Length matching condition
            length_ab = calculate_length_dtop((0, a), (1, b))
            length_bc = calculate_length_dtop((1, b), (2, c))
            length_cd = calculate_length_dtop((2, c), (3, d))
            length_de = calculate_length_dtop((3, d), (4, e))

            if a_high < b_low and c_high < d_low and d_low > e_high and a < b and b > c and c < d and e < d and d > a and b > e:
                # Check if lengths match by 85%
                if (0.6 <= length_bc / length_cd <= 1.4 or
                    0.6 <= length_cd / length_bc <= 1.4) and \
                    (length_ab > max(length_bc, length_cd) and
                     length_de > max(length_bc, length_cd)):
                    patterns_tops.append((a, b, c, d, e))
                    dates.append([date_a, date_b, date_c, date_d, date_e])

        return patterns_tops, dates

    def validate_patterns(patterns_tops, dates):
        filtered_patterns = []
        filtered_dates = []

        for pattern, date in zip(patterns_tops, dates):
            a, b, c, d, e = pattern

            if (calculate_angle_and_validate((0, a), (1, b), 45, 90) and
                calculate_angle_and_validate((1, b), (2, c), -90, -45) and
                calculate_angle_and_validate((2, c), (3, d), 45, 90) and
                    calculate_angle_and_validate((3, d), (4, e), -90, -45)):
                # Add pattern and date if all angle conditions are satisfied
                filtered_patterns.append(pattern)
                filtered_dates.append(date)

        return filtered_patterns, filtered_dates

    def find_custom_peaks(df, window, pct_threshold=0.02):
        peaks = []
        valleys = []

        for i in range(window, len(df) - window):
            # Check for peaks
            if df['Close'][i] == df['Close'][i-window:i+window].max() and df['Close'][i] - df['Close'][i-1] > pct_threshold:
                peaks.append(i)
            # Check for valleys
            elif df['Close'][i] == df['Close'][i-window:i+window].min() and df['Close'][i-1] - df['Close'][i] > pct_threshold:
                valleys.append(i)

        maxima = df.iloc[peaks]
        minima = df.iloc[valleys]
        max_min = pd.concat([maxima, minima]).sort_index()

        return max_min

    # alldays = set(df['Date'][0] + timedelta(x)
    #               for x in range((df['Date'].iloc[-1] - df['Date'][0]).days))

    window = 4
    max_min = find_custom_peaks(df, window)
    patterns_tops, dates = find_doubles_patterns(max_min)

    # Validate and filter patterns
    filtered_patterns, dtop_dates = validate_patterns(
        patterns_tops, dates)
    days = 5
    today = datetime.now()
    # Start date (from 5 days before yesterday)
    start_date = today - timedelta(days=days+1)
    end_date = today - timedelta(days=1)  # End date (yesterday)

    # Filter the date ranges
    filtered_dates = []
    for date_group in dtop_dates:
        # Check if all dates in the group are within the range
        if all(start_date <= datetime.strptime(d, '%Y-%m-%d %H:%M:%S') <= end_date for d in date_group):
            filtered_dates.append(date_group)
    return filtered_dates

# Function to detect head-and-shoulders patterns and return count


def detect_head_and_shoulders(df):
    sup = df[df['Low'] == df['Low'].rolling(24, center=True).min()]['Low']
    res = df[df['High'] == df['High'].rolling(24, center=True).max()]['High']
    sup = sup.to_frame()
    sup.columns = ['price']
    sup['val'] = 1
    res = res.to_frame()
    res.columns = ['price']
    res['val'] = 2
    lev = sup.combine_first(res)

    def hsf(hs):
        ls, lb, head, rb, rs = hs
        if df['High'][head] <= max(df['High'][ls], df['High'][rs]):
            return None

        rh = rs - head
        lh = head - ls
        if rh > 2.5 * lh or lh > 2.5 * rh:
            return None

        neck_run = rb - lb
        neck_rise = df['Low'][rb] - df['Low'][lb]
        neck_slope = neck_rise / neck_run

        head_width = rb - lb
        pat_start = -1
        pat_end = -1

        for j in range(1, head_width):
            neck1 = df['Low'][lb] + (ls - lb - j) * neck_slope
            if ls - j < 0:
                return None
            if df['Low'][ls - j] < neck1:
                pat_start = ls - j
                break

        for j in range(1, head_width):
            neck2 = df['Low'][lb] + (rs - lb + j) * neck_slope
            if rs + j > len(df) - 1:
                return None
            if df['Low'][rs + j] < neck2:
                pat_end = rs + j
                break

        if pat_start == -1 or pat_end == -1:
            return None

        hs.insert(0, pat_start)
        hs.append(pat_end)
        return hs

    head_and_shoulders = []
    c = []
    p = lev.index[0]
    for i in lev.index:
        if not c:
            if lev['val'][i] == 2:
                c.append(i)
            else:
                p = i
                continue
        else:
            if lev['val'][i] != lev['val'][p] and i - p > 3:
                c.append(i)
            elif lev['val'][i] == 1:
                c = []
            else:
                c = [i]

        if len(c) == 5:
            hs = hsf(c)
            if hs:
                head_and_shoulders.append(hs)
                c = []
            else:
                c = c[2:]
        p = i
    # Convert 'Date' column to string explicitly (if not already done) at the start
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Now process the head and shoulders logic
    coordinates = []
    for hs in head_and_shoulders:
        points = []
        for i in range(len(hs)):
            # Ensure the date is a string and convert it if it's a Timestamp
            # It should already be a string after conversion
            date_value = df['Date'][hs[i]]

            points.append({
                'x': date_value,  # Use the date as a string now
                'y': df['Low'][hs[i]] if i % 2 == 0 else df['High'][hs[i]]
            })
        coordinates.append(points)

    # Print coordinates to verify
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)

    # Calculate the date range for the last 5 days (starting from yesterday)
    date_range = [yesterday - timedelta(days=i) for i in range(5)]

    # Flatten the coordinates list to access dates easily
    filtered_coordinates = []

    for points in coordinates:
        filtered_points = []

        for point in points:
            # Convert the date string to a datetime object for comparison
            point_date = datetime.strptime(
                point['x'], '%Y-%m-%d %H:%M:%S').date()

            # Check if the point's date is within the last 5 days
            if point_date in date_range:
                filtered_points.append(point)

        # Only add points to the filtered list if they belong to the last 5 days
        if filtered_points:
            filtered_coordinates.append(filtered_points)
    return len(filtered_coordinates)
    # return len(head_and_shoulders)
# Save results to a CSV file


def quadratic(x, a, b, c):
    return a * x**2 + b * x + c


def find_cup_and_handle(df):
    df = df.rename(columns={
        'Date': 'date',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close'
    })
    df['date'] = pd.to_datetime(df['date'])
    price_diff = np.mean(df['high'] - df['low'])

    # Generate date range for the previous 5 days starting from yesterday
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)
    date_range = [yesterday - timedelta(days=i) for i in range(5)]

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
                # Ensure the range is within max_bars and the highs are within the price tolerance
                if pivot_highs[j] - pivot_highs[i] <= max_bars and \
                        abs(df['high'][pivot_highs[i]] - df['high'][pivot_highs[j]]) <= price_tolerance * df['high'][pivot_highs[i]]:

                    start_idx = pivot_highs[i]
                    end_idx = pivot_highs[j]
                    x = np.arange(end_idx - start_idx + 1)
                    y = df['low'][start_idx:end_idx + 1].values

                    if len(x) > 2:
                        # Suppress the OptimizeWarning temporarily
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", OptimizeWarning)
                            try:
                                popt, _ = curve_fit(quadratic, x, y)
                                a, b, c = popt

                                # Check if the curve opens upwards (a > 0)
                                if a > 0:
                                    # Calculate the vertex of the parabola
                                    vertex = -b / (2 * a)

                                    # Ensure vertex is within the start and end range and the curve depth is reasonable
                                    if 0 < vertex < end_idx - start_idx and 90 < (end_idx - start_idx) / abs(a) < 150:
                                        depth = df['high'][start_idx] - \
                                            quadratic(vertex, a, b, c)
                                        # Adjust depth condition if needed
                                        if depth > (df['high'][start_idx] - df['low'][start_idx]) * 2:
                                            patterns.append(
                                                (start_idx, end_idx, vertex + start_idx, a, b, c))
                            except Exception as e:
                                print(
                                    f"Error in curve fitting for range ({start_idx}, {end_idx}): {e}")
                                continue  # Skip to the next pair if curve fitting fails
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

    # Now using the extracted `a`, `b`, `c`, and `x`, `y` to generate coordinates for charting
    coordinates = []
    for start_idx, end_idx, vertex_idx, a, b, c in unique_patterns:
        if end_idx < len(df):
            # Convert start_date, end_date, vertex_date to datetime objects
            start_date = df['date'][start_idx].date()
            end_date = df['date'][end_idx].date()
            vertex_date = df['date'][int(vertex_idx)].date()
            handle_start_date = df['date'][end_idx + 1].date()
            handle_end_date = df['date'][end_idx +
                                         (end_idx - start_idx) // 3].date()

            # Check if all dates are within the last 5 days
            if start_date in date_range and end_date in date_range and vertex_date in date_range and \
               handle_start_date in date_range and handle_end_date in date_range:
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

    # Print coordinates to check
    return coordinates


# Function to detect V-shape patterns and return count


def detect_v_shape_patterns(df):
    def calculate_angle_v(p1, p2):
        return degrees(atan2(p2[1] - p1[1], p2[0] - p1[0]))

    def find_v_shapes(max_min):
        patterns_v = []
        dates = []
        for i in range(5, len(max_min)):
            window = max_min.iloc[i-5:i]

            if window.index[-1] - window.index[0] > 50:
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
                if abs(c['High'] - e['High']) <= 0.025 * c['High']:
                    length_cd = abs(c['High'] - d['Low'])
                    length_de = abs(d['Low'] - e['High'])

                    if 0.85 * length_cd <= length_de <= 1.15 * length_cd:
                        angle_cd = calculate_angle_v(
                            [1, c['High']], [2, d['Low']])
                        angle_de = calculate_angle_v(
                            [2, d['Low']], [3, e['High']])

                        if -95 <= angle_cd <= -85 and 85 <= angle_de <= 95:
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

    days = 5
    today = datetime.now()
    # Start date (from 5 days before yesterday)
    start_date = today - timedelta(days=days+1)
    end_date = today - timedelta(days=1)  # End date (yesterday)

    # Filter the date ranges
    filtered_dates = []
    for date_group in dates:
        # Check if all dates in the group are within the range
        if all(start_date <= datetime.strptime(d, '%Y-%m-%d %H:%M:%S') <= end_date for d in date_group):
            filtered_dates.append(date_group)
    return len(filtered_dates)
    # return len(dates)

# Function to detect Double Bottom patterns and return count


def detect_double_bottoms(df):

    def calculate_slope_angle(x, y):
        # Fit a linear regression model
        model = LinearRegression().fit(x.reshape(-1, 1), y)

        # Get the slope from the linear regression model
        slope = model.coef_[0]

        # Calculate the difference in High and Low for scaling
        diff = max(df['High']) - min(df['Low'])

        # Calculate the scaled dy and dx
        dx = max(x) - min(x)
        dy = slope * dx * (len(df) / diff)

        # Calculate the angle using arctangent
        angle_rad = math.atan2(dy, dx)

        # Convert radians to degrees
        angle_deg = math.degrees(angle_rad)
        # angle_deg = abs(angle_deg)

        if angle_deg > 90:
            angle_deg = 180-angle_deg

        return slope, angle_deg

    def calculate_angle_dbot(p1, p2, angle_min, angle_max):
        x1, y1 = p1
        x2, y2 = p2
        angle_rad = atan2(y2 - y1, x2 - x1)
        angle_deg = degrees(angle_rad)
        return angle_min <= angle_deg <= angle_max

    def calculate_length_dbot(p1, p2):
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    def validate_lengths_dbot(a, b, c, d, e):
        length_ab = calculate_length_dbot((0, a), (1, b))
        length_bc = calculate_length_dbot((1, b), (2, c))
        length_cd = calculate_length_dbot((2, c), (3, d))
        length_de = calculate_length_dbot((3, d), (4, e))

        max_bc_cd = max(length_bc, length_cd)
        # a-c and d-e must be larger than b-c or c-d
        a_c_d_e = min(length_ab, length_de)

        # Length checks
        condition_1 = 0.65 <= length_bc / \
            length_cd <= 1.35 or 0.65 <= length_cd / length_bc <= 1.35
        condition_2 = a_c_d_e > max_bc_cd

        return condition_2 and condition_1

    def find_doubles_dbot(max_min):
        patterns_tops = []
        dates = []

        for i in range(5, len(max_min)):
            window = max_min.iloc[i-5:i]

            if window.index[-1] - window.index[0] > 50:
                continue

            a = window.iloc[0]['High']
            b = window.iloc[1]['Low']
            c = window.iloc[2]['High']
            d = window.iloc[3]['Low']
            e = window.iloc[4]['High']

            a_low = window.iloc[0]['Low']
            c_low = window.iloc[2]['Low']
            d_low = window.iloc[3]['Low']
            e_low = window.iloc[4]['Low']
            b_high = window.iloc[1]['High']
            a_high = window.iloc[0]['High']
            c_high = window.iloc[2]['High']
            d_high = window.iloc[3]['High']

            e_high = window.iloc[4]['High']

            if c < a and c < e:
                # if a_high > b_low and c_low > d_high and e_low > d_high:
                if a_low > b_high and b_high < c_low > d_high and e_low > d_high:
                    patterns_tops.append((a, b, c, d, e))
                    dates.append([window['Date'].iloc[0], window['Date'].iloc[1], window['Date'].iloc[2],
                                  window['Date'].iloc[3], window['Date'].iloc[4]])

        return patterns_tops, dates

    def validate_patterns_dbot(patterns_tops, dates):
        filtered_patterns = []
        filtered_dates = []

        for pattern, date in zip(patterns_tops, dates):
            a, b, c, d, e = pattern

            if (calculate_angle_dbot((0, a), (1, b), -90, -70) and
                calculate_angle_dbot((1, b), (2, c), 70, 90) and
                calculate_angle_dbot((2, c), (3, d), -90, -70) and
                calculate_angle_dbot((3, d), (4, e), 70, 90) and
                    validate_lengths_dbot(a, b, c, d, e)):  # Validate lengths with custom condition
                filtered_patterns.append(pattern)
                filtered_dates.append(date)

        return filtered_patterns, filtered_dates

    def find_local_max_min(df, window, smooth=False, smoothing_period=3):
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
    max_min = find_local_max_min(df, window, smooth=True)
    patterns_tops, dates = find_doubles_dbot(max_min)

    filtered_patterns, filtered_dates = validate_patterns_dbot(
        patterns_tops, dates)
    days = 5
    today = datetime.now()
    # Start date (from 5 days before yesterday)
    start_date = today - timedelta(days=days+1)
    end_date = today - timedelta(days=1)  # End date (yesterday)

    # Filter the date ranges
    filtered_dates = []
    for date_group in filtered_dates:
        # Check if all dates in the group are within the range
        if all(start_date <= datetime.strptime(d, '%Y-%m-%d %H:%M:%S') <= end_date for d in date_group):
            filtered_dates.append(date_group)
    return len(filtered_dates)


def save_to_csv(results, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Symbol', 'Inside Bar', 'Double top/bottom',
                        'Head and Shoulders', 'VShape'])  # Updated header row
        for symbol, counts in results.items():
            writer.writerow([
                symbol, counts['inside_bar'], counts['double_patterns'], counts['head_and_shoulders'], counts['v_shape']
            ])


def analyze_stocks(symbols, interval):
    all_patterns = {}  # To store counts for all stocks

    for symbol in symbols:
        try:
            print(f"Processing stock: {symbol}")
            data = fetch_data_from_db(symbol, interval)
            if not data:
                print(f"No data found for {symbol}. Continuing to next stock.")
                continue

            df = pd.DataFrame(data)

            # Detect patterns
            inside_bar_ranges = detect_consecutive_ibars(df, interval)
            double_top_dates = detect_double_tops(df)
            double_bottom_count = detect_double_bottoms(df)
            head_and_shoulders_count = detect_head_and_shoulders(df)
            v_shape_count = detect_v_shape_patterns(df)

            # Combine double top and double bottom counts
            double_patterns_count = len(double_top_dates) + double_bottom_count

            # Count patterns and store results
            all_patterns[symbol] = {
                'inside_bar': len(inside_bar_ranges),
                'double_patterns': double_patterns_count,  # Combined count
                'head_and_shoulders': head_and_shoulders_count,
                'v_shape': v_shape_count
            }

        except Exception as e:
            print(
                f"Error processing stock {symbol}: {e}. Skipping to next stock.")
            continue  # Skip to the next symbol in case of any error

    # Save the results to a CSV file
    save_to_csv(all_patterns, 'stock_patterns.csv')


# Example usage
symbols = [
    'NSE:360ONE-EQ',
    'NSE:3MINDIA-EQ',
    'NSE:AARTIIND-EQ',
    'NSE:AAVAS-EQ',
    'NSE:ABB-EQ',
    'NSE:ABBOTINDIA-EQ',
    'NSE:ABCAPITAL-EQ',
    'NSE:ABFRL-EQ',
    'NSE:ACC-EQ',
    'NSE:ACE-EQ',
    'NSE:ACI-EQ',
    'NSE:ADANIENSOL-EQ',
    'NSE:ADANIENT-EQ',
    'NSE:ADANIGREEN-EQ',
    'NSE:ADANIPORTS-EQ',
    'NSE:ADANIPOWER-EQ',
    'NSE:AEGISLOG-EQ',
    'NSE:AETHER-EQ',
    'NSE:AFFLE-EQ',
    'NSE:AIAENG-EQ',
    'NSE:AJANTPHARM-EQ',
    'NSE:ALKEM-EQ',
    'NSE:ALKYLAMINE-EQ',
    'NSE:ALLCARGO-EQ',
    'NSE:ALOKINDS-EQ',
    'NSE:AMBER-EQ',
    'NSE:AMBUJACEM-EQ',
    'NSE:ANANDRATHI-EQ',
    'NSE:ANGELONE-EQ',
    'NSE:ANURAS-EQ',
    'NSE:APARINDS-EQ',
    'NSE:APLAPOLLO-EQ',
    'NSE:APLLTD-EQ',
    'NSE:APOLLOHOSP-EQ',
    'NSE:APOLLOTYRE-EQ',
    'NSE:APTUS-EQ',
    'NSE:ARE-M-EQ',
    'NSE:ASAHIINDIA-EQ',
    'NSE:ASHOKLEY-EQ',
    'NSE:ASIANPAINT-EQ',
    'NSE:ASTERDM-EQ',
    'NSE:ASTRAL-EQ',
    'NSE:ASTRAZEN-EQ',
    'NSE:ATGL-EQ',
    'NSE:ATUL-EQ',
    'NSE:AUBANK-EQ',
    'NSE:AUROPHARMA-EQ',
    'NSE:AVANTIFEED-EQ',
    'NSE:AWL-EQ',
    'NSE:AXISBANK-EQ',
    'NSE:BAJAJ-AUTO-EQ',
    'NSE:BAJAJFINSV-EQ',
    'NSE:BAJAJHLDNG-EQ',
    'NSE:BAJFINANCE-EQ',
    'NSE:BALAMINES-EQ',
    'NSE:BALKRISIND-EQ',
    'NSE:BALRAMCHIN-EQ',
    'NSE:BANDHANBNK-EQ',
    'NSE:BANKBARODA-EQ',
    'NSE:BANKINDIA-EQ',
    'NSE:BATAINDIA-EQ',
    'NSE:BAYERCROP-EQ',
    'NSE:BBTC-EQ',
    'NSE:BDL-EQ',
    'NSE:BEL-EQ',
    'NSE:BEML-EQ',
    'NSE:BERGEPAINT-EQ',
    'NSE:BHARATFORG-EQ',
    'NSE:BHARTIARTL-EQ',
    'NSE:BHEL-EQ',
    'NSE:BIKAJI-EQ',
    'NSE:BIOCON-EQ',
    'NSE:BIRLACORPN-EQ',
    'NSE:BLS-EQ',
    'NSE:BLUEDART-EQ',
    'NSE:BLUESTARCO-EQ',
    'NSE:BORORENEW-EQ',
    'NSE:BOSCHLTD-EQ',
    'NSE:BPCL-EQ',
    'NSE:BRIGADE-EQ',
    'NSE:BRITANNIA-EQ',
    'NSE:BSE-EQ',
    'NSE:BSOFT-EQ',
    'NSE:CAMPUS-EQ',
    'NSE:CAMS-EQ',
    'NSE:CANBK-EQ',
    'NSE:CANFINHOME-EQ',
    'NSE:CAPLIPOINT-EQ',
    'NSE:CARBORUNIV-EQ',
    'NSE:CASTROLIND-EQ',
    'NSE:CCL-EQ',
    'NSE:CDSL-EQ',
    'NSE:CEATLTD-EQ',
    'NSE:CELLO-EQ',
    'NSE:CENTRALBK-EQ',
    'NSE:CENTURYPLY-EQ',
    'NSE:CENTURYTEX-EQ',
    'NSE:CERA-EQ',
    'NSE:CESC-EQ',
    'NSE:CGCL-EQ',
    'NSE:CGPOWER-EQ',
    'NSE:CHALET-EQ',
    'NSE:CHAMBLFERT-EQ',
    'NSE:CHEMPLASTS-EQ',
    'NSE:CHENNPETRO-EQ',
    'NSE:CHOLAFIN-EQ',
    'NSE:CHOLAHLDNG-EQ',
    'NSE:CIEINDIA-EQ',
    'NSE:CIPLA-EQ',
    'NSE:CLEAN-EQ',
    'NSE:COALINDIA-EQ',
    'NSE:COCHINSHIP-EQ',
    'NSE:COFORGE-EQ',
    'NSE:COLPAL-EQ',
    'NSE:CONCOR-EQ',
    'NSE:CONCORDBIO-EQ',
    'NSE:COROMANDEL-EQ',
    'NSE:CRAFTSMAN-EQ',
    'NSE:CREDITACC-EQ',
    'NSE:CRISIL-EQ',
    'NSE:CROMPTON-EQ',
    'NSE:CSBBANK-EQ',
    'NSE:CUB-EQ',
    'NSE:CUMMINSIND-EQ',
    'NSE:CYIENT-EQ',
    'NSE:DABUR-EQ',
    'NSE:DALBHARAT-EQ',
    'NSE:DATAPATTNS-EQ',
    'NSE:DCMSHRIRAM-EQ',
    'NSE:DEEPAKFERT-EQ',
    'NSE:DEEPAKNTR-EQ',
    'NSE:DELHIVERY-EQ',
    'NSE:DEVYANI-EQ',
    'NSE:DIVISLAB-EQ',
    'NSE:DIXON-EQ',
    'NSE:DLF-EQ',
    'NSE:DMART-EQ',
    'NSE:DOMS-EQ',
    'NSE:DRREDDY-EQ',
    'NSE:EASEMYTRIP-EQ',
    'NSE:EICHERMOT-EQ',
    'NSE:EIDPARRY-EQ',
    'NSE:EIHOTEL-EQ',
    'NSE:ELECON-EQ',
    'NSE:ELGIEQUIP-EQ',
    'NSE:EMAMILTD-EQ',
    'NSE:ENDURANCE-EQ',
    'NSE:ENGINERSIN-EQ',
    'NSE:EPL-EQ',
    'NSE:EQUITASBNK-EQ',
    'NSE:ERIS-EQ',
    'NSE:ESCORTS-EQ',
    'NSE:EXIDEIND-EQ',
    'NSE:FACT-EQ',
    'NSE:FDC-EQ',
    'NSE:FEDERALBNK-EQ',
    'NSE:FINCABLES-EQ',
    'NSE:FINEORG-EQ',
    'NSE:FINNIFTY-INDEX',
    'NSE:FINPIPE-EQ',
    'NSE:FIVESTAR-EQ',
    'NSE:FLUOROCHEM-EQ',
    'NSE:FORTIS-EQ',
    'NSE:FSL-EQ',
    'NSE:GAEL-EQ',
    'NSE:GAIL-EQ',
    'NSE:GESHIP-EQ',
    'NSE:GICRE-EQ',
    'NSE:GILLETTE-EQ',
    'NSE:GLAND-EQ',
    'NSE:GLAXO-EQ',
    'NSE:GLENMARK-EQ',
    'NSE:GLS-EQ',
    'NSE:GMDCLTD-EQ',
    'NSE:GMMPFAUDLR-EQ',
    'NSE:GMRINFRA-EQ',
    'NSE:GNFC-EQ',
    'NSE:GODFRYPHLP-EQ',
    'NSE:GODREJCP-EQ',
    'NSE:GODREJIND-EQ',
    'NSE:GODREJPROP-EQ',
    'NSE:GPIL-EQ',
    'NSE:GPPL-EQ',
    'NSE:GRANULES-EQ',
    'NSE:GRAPHITE-EQ',
    'NSE:GRASIM-EQ',
    'NSE:GRINDWELL-EQ',
    'NSE:GRSE-EQ',
    'NSE:GSFC-EQ',
    'NSE:GSPL-EQ',
    'NSE:GUJGASLTD-EQ',
    'NSE:HAL-EQ',
    'NSE:HAPPSTMNDS-EQ',
    'NSE:HATSUN-EQ',
    'NSE:HAVELLS-EQ',
    'NSE:HBLPOWER-EQ',
    'NSE:HCLTECH-EQ',
    'NSE:HDFCAMC-EQ',
    'NSE:HDFCBANK-EQ',
    'NSE:HDFCLIFE-EQ',
    'NSE:HEG-EQ',
    'NSE:HEROMOTOCO-EQ',
    'NSE:HFCL-EQ',
    'NSE:HGS-EQ',
    'NSE:HINDALCO-EQ',
    'NSE:HINDCOPPER-EQ',
    'NSE:HINDPETRO-EQ',
    'NSE:HINDUNILVR-EQ',
    'NSE:HINDZINC-EQ',
    'NSE:HLEGLAS-EQ',
    'NSE:HONAUT-EQ',
    'NSE:HUDCO-EQ',
    'NSE:ICICIBANK-EQ',
    'NSE:ICICIGI-EQ',
    'NSE:ICICIPRULI-EQ',
    'NSE:IDBI-EQ',
    'NSE:IDEA-EQ',
    'NSE:IDFC-EQ',
    'NSE:IDFCFIRSTB-EQ',
    'NSE:IEX-EQ',
    'NSE:IGL-EQ',
    'NSE:IIFL-EQ',
    'NSE:IIFLSEC-EQ',
    'NSE:INDHOTEL-EQ',
    'NSE:INDIAMART-EQ',
    'NSE:INDIANB-EQ',
    'NSE:INDIGO-EQ',
    'NSE:INDIGOPNTS-EQ',
    'NSE:INDOCO-EQ',
    'NSE:INDUSINDBK-EQ',
    'NSE:INDUSTOWER-EQ',
    'NSE:INFIBEAM-EQ',
    'NSE:INFY-EQ',
    'NSE:INGERRAND-EQ',
    'NSE:INOXGREEN-EQ',
    'NSE:INOXWIND-EQ',
    'NSE:INTELLECT-EQ',
    'NSE:IOB-EQ',
    'NSE:IOC-EQ',
    'NSE:IPCALAB-EQ',
    'NSE:IRB-EQ',
    'NSE:IRCTC-EQ',
    'NSE:IRFC-EQ',
    'NSE:ISEC-EQ',
    'NSE:ITC-EQ',
    'NSE:ITI-EQ',
    'NSE:JAMNAAUTO-EQ',
    'NSE:JBCHEPHARM-EQ',
    'NSE:JCHAC-EQ',
    'NSE:JINDALSAW-EQ',
    'NSE:JINDALSTEL-EQ',
    'NSE:JIOFIN-EQ',
    'NSE:JKCEMENT-EQ',
    'NSE:JKIL-EQ',
    'NSE:JKLAKSHMI-EQ',
    'NSE:JKPAPER-EQ',
    'NSE:JSL-EQ',
    'NSE:JSWENERGY-EQ',
    'NSE:JSWINFRA-EQ',
    'NSE:JSWSTEEL-EQ',
    'NSE:JTEKTINDIA-EQ',
    'NSE:JUBLFOOD-EQ',
    'NSE:JUBLPHARMA-EQ',
    'NSE:JUSTDIAL-EQ',
    'NSE:KALYANKJIL-EQ',
    'NSE:KANSAINER-EQ',
    'NSE:KARURVYSYA-EQ',
    'NSE:KAYNES-EQ',
    'NSE:KEC-EQ',
    'NSE:KIMS-EQ',
    'NSE:KIRLOSENG-EQ',
    'NSE:KIRLOSIND-EQ',
    'NSE:KNRCON-EQ',
    'NSE:KOLTEPATIL-EQ',
    'NSE:KOPRAN-EQ',
    'NSE:KOTAKBANK-EQ',
    'NSE:KPIGREEN-EQ',
    'NSE:KPITTECH-EQ',
    'NSE:KPRMILL-EQ',
    'NSE:KRBL-EQ',
    'NSE:KSB-EQ',
    'NSE:LALPATHLAB-EQ',
    'NSE:LAOPALA-EQ',
    'NSE:LAURUSLABS-EQ',
    'NSE:LAXMIMACH-EQ',
    'NSE:LEMONTREE-EQ',
    'NSE:LICHSGFIN-EQ',
    'NSE:LICI-EQ',
    'NSE:LINC-EQ',
    'NSE:LODHA-EQ',
    'NSE:LT-EQ',
    'NSE:LTF-EQ',
    'NSE:LTIM-EQ',
    'NSE:LTTS-EQ',
    'NSE:LUMAXIND-EQ',
    'NSE:LUMAXTECH-EQ',
    'NSE:LUPIN-EQ',
    'NSE:M-M-EQ',
    'NSE:M-MFIN-EQ',
    'NSE:MAHABANK-EQ',
    'NSE:MAHSCOOTER-EQ',
    'NSE:MANINDS-EQ',
    'NSE:MANKIND-EQ',
    'NSE:MAPMYINDIA-EQ',
    'NSE:MARATHON-EQ',
    'NSE:MARICO-EQ',
    'NSE:MARKSANS-EQ',
    'NSE:MARUTI-EQ',
    'NSE:MASFIN-EQ',
    'NSE:MASTEK-EQ',
    'NSE:MAXHEALTH-EQ',
    'NSE:MAZDOCK-EQ',
    'NSE:MCX-EQ',
    'NSE:MEDANTA-EQ',
    'NSE:MFSL-EQ',
    'NSE:MIDCPNIFTY-INDEX',
    'NSE:MOIL-EQ',
    'NSE:MOREPENLAB-EQ',
    'NSE:MOTHERSON-EQ',
    'NSE:MPHASIS-EQ',
    'NSE:MRF-EQ',
    'NSE:MRPL-EQ',
    'NSE:MUTHOOTFIN-EQ',
    'NSE:NATCOPHARM-EQ',
    'NSE:NAUKRI-EQ',
    'NSE:NAZARA-EQ',
    'NSE:NBCC-EQ',
    'NSE:NCC-EQ',
    'NSE:NDTV-EQ',
    'NSE:NESCO-EQ',
    'NSE:NESTLEIND-EQ',
    'NSE:NETWORK18-EQ',
    'NSE:NEULANDLAB-EQ',
    'NSE:NHPC-EQ',
    'NSE:NIFTY50-INDEX',
    'NSE:NIFTYBANK-INDEX',
    'NSE:NIFTYINFRA-INDEX',
    'NSE:NIFTYIT-INDEX',
    'NSE:NLCINDIA-EQ',
    'NSE:NMDC-EQ',
    'NSE:NTPC-EQ',
    'NSE:NUVOCO-EQ',
    'NSE:NYKAA-EQ',
    'NSE:OBEROIRLTY-EQ',
    'NSE:OCCL-EQ',
    'NSE:OFSS-EQ',
    'NSE:OIL-EQ',
    'NSE:ONGC-EQ',
    'NSE:ONMOBILE-EQ',
    'NSE:ORIENTELEC-EQ',
    'NSE:ORIENTPPR-EQ',
    'NSE:PAGEIND-EQ',
    'NSE:PARADEEP-EQ',
    'NSE:PATANJALI-EQ',
    'NSE:PAYTM-EQ',
    'NSE:PEL-EQ',
    'NSE:PERSISTENT-EQ',
    'NSE:PETRONET-EQ',
    'NSE:PFC-EQ',
    'NSE:PGHH-EQ',
    'NSE:PIDILITIND-EQ',
    'NSE:PIIND-EQ',
    'NSE:PNB-EQ',
    'NSE:PNCINFRA-EQ',
    'NSE:POLICYBZR-EQ',
    'NSE:POLYCAB-EQ',
    'NSE:POONAWALLA-EQ',
    'NSE:POWERGRID-EQ',
    'NSE:PRAJIND-EQ',
    'NSE:PRESTIGE-EQ',
    'NSE:PRINCEPIPE-EQ',
    'NSE:PRSMJOHNSN-EQ',
    'NSE:PSB-EQ',
    'NSE:QUESS-EQ',
    'NSE:RADICO-EQ',
    'NSE:RAIN-EQ',
    'NSE:RAJESHEXPO-EQ',
    'NSE:RALLIS-EQ',
    'NSE:RAMCOSYS-EQ',
    'NSE:RATNAMANI-EQ',
    'NSE:RAYMOND-EQ',
    'NSE:RBLBANK-EQ',
    'NSE:RCF-EQ',
    'NSE:RECLTD-EQ',
    'NSE:RELAXO-EQ',
    'NSE:RELIANCE-EQ',
    'NSE:ROSSARI-EQ',
    'NSE:RVNL-EQ',
    'NSE:SAFARI-EQ',
    'NSE:SAIL-EQ',
    'NSE:SANOFI-EQ',
    'NSE:SBICARD-EQ',
    'NSE:SBILIFE-EQ',
    'NSE:SBIN-EQ',
    'NSE:SHOPERSTOP-EQ',
    'NSE:SHREECEM-EQ',
    'NSE:SHRIRAMFIN-EQ',
    'NSE:SIEMENS-EQ',
    'NSE:SJVN-EQ',
    'NSE:SOBHA-EQ',
    'NSE:SONACOMS-EQ',
    'NSE:SRF-EQ',
    'NSE:SUNDRMFAST-EQ',
    'NSE:SUNPHARMA-EQ',
    'NSE:SUNTV-EQ',
    'NSE:SUPRAJIT-EQ',
    'NSE:SUPREMEIND-EQ',
    'NSE:SUTLEJTEX-EQ',
    'NSE:SUZLON-EQ',
    'NSE:SYNGENE-EQ',
    'NSE:TATACHEM-EQ',
    'NSE:TATACOMM-EQ',
    'NSE:TATACONSUM-EQ',
    'NSE:TATAELXSI-EQ',
    'NSE:TATAMOTORS-EQ',
    'NSE:TATAMTRDVR-EQ',
    'NSE:TATAPOWER-EQ',
    'NSE:TATASTEEL-EQ',
    'NSE:TATATECH-EQ',
    'NSE:TCS-EQ',
    'NSE:TEAMLEASE-EQ',
    'NSE:TECHM-EQ',
    'NSE:THANGAMAYL-EQ',
    'NSE:THERMAX-EQ',
    'NSE:TIINDIA-EQ',
    'NSE:TITAN-EQ',
    'NSE:TORNTPHARM-EQ',
    'NSE:TORNTPOWER-EQ',
    'NSE:TRENT-EQ',
    'NSE:TRIVENI-EQ',
    'NSE:TTML-EQ',
    'NSE:TV18BRDCST-EQ',
    'NSE:TVSMOTOR-EQ',
    'NSE:UBL-EQ',
    'NSE:UCOBANK-EQ',
    'NSE:ULTRACEMCO-EQ',
    'NSE:UNIONBANK-EQ',
    'NSE:UNITDSPR-EQ',
    'NSE:UPL-EQ',
    'NSE:UTIAMC-EQ',
    'NSE:VAIBHAVGBL-EQ',
    'NSE:VARROC-EQ',
    'NSE:VBL-EQ',
    'NSE:VEDL-EQ',
    'NSE:VIPIND-EQ',
    'NSE:VOLTAS-EQ',
    'NSE:WELCORP-EQ',
    'NSE:WHIRLPOOL-EQ',
    'NSE:WIPRO-EQ',
    'NSE:WOCKPHARMA-EQ',
    'NSE:YESBANK-EQ',
    'NSE:ZEEL-EQ',
    'NSE:ZOMATO-EQ',
    'NSE:ZYDUSLIFE-EQ',
    'NSE:ZYDUSWELL-EQ',
]  # Add more symbols as needed
interval = 15  # Interval in minutes
analyze_stocks(symbols, interval)
