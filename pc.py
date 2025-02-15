# import pandas as pd
# import mysql.connector
# from mysql.connector import Error
# from datetime import datetime, timedelta
# import numpy as np
# import math
# from scipy.signal import argrelextrema

# # Database connection configuration
# db_config3 = {
#     'host': '118.139.182.3',
#     'user': 'sqluser1',
#     'password': 'TGDp0U&[1Y4S',
#     'database': 'stocks'
# }

# # Function to create a MySQL connection
# def create_connection():
#     connection = None
#     try:
#         connection = mysql.connector.connect(**db_config3)
#         print("Connection to MySQL DB successful")
#     except Error as e:
#         print(f"The error '{e}' occurred")
#     return connection

# # Function to fetch data from the database
# def fetch_data_from_db(symbol, interval):
#     con = create_connection()
#     cur = con.cursor()

#     # Normalize the symbol name to match your database table naming convention
#     sym = symbol.split(':')[-1].replace('-', '_').replace('&', '_').lower()

#     # Check if the table for the symbol exists in the database
#     cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'stocks'")
#     tables = cur.fetchall()
#     tables = [table[0] for table in tables]

#     if sym not in tables:
#         print(f"Table for {symbol} does not exist in the database.")
#         con.close()
#         return []

#     # SQL query to fetch data for specified interval
#     query = f"""
#         SELECT t.INTERVAL_START AS `Interval`, t.`Open`, t.`High`, t.`Low`, ae.`Close`, t.`Volume`
#         FROM (
#             SELECT
#                 (UNIX_TIMESTAMP(`date`) - (UNIX_TIMESTAMP(DATE_FORMAT(`date`, '%Y-%m-%d 09:15:00')))) DIV ({interval} * 60) + UNIX_TIMESTAMP(DATE_FORMAT(`date`, '%Y-%m-%d 09:15:00')) AS interval_id,
#                 MIN(`date`) AS INTERVAL_START,
#                 `open` AS `Open`,
#                 MAX(`high`) AS `High`,
#                 MIN(`low`) AS `Low`,
#                 MAX(`date`) AS max_date,
#                 SUM(`volume`) AS `Volume`
#             FROM {sym}
#             WHERE DATE(`date`) BETWEEN CURDATE() - INTERVAL 5 DAY AND CURDATE() - INTERVAL 1 DAY  -- Previous 3 weekdays
#             AND WEEKDAY(`date`) < 5  -- Exclude weekends
#             GROUP BY interval_id
#             ORDER BY max_date DESC
#             LIMIT 5000
#         ) AS t
#         INNER JOIN {sym} ae ON ae.`date` = t.max_date
#         ORDER BY t.max_date ASC;
#     """

#     cur.execute(query)
#     rows = cur.fetchall()

#     # Storing data
#     seen = set()
#     data = []
#     for row in rows:
#         row_data = {
#             'Date': row[0].strftime('%Y-%m-%d %H:%M:%S'),
#             'Open': row[1],
#             'High': row[2],
#             'Low': row[3],
#             'Close': row[4],
#             'Volume': row[5]
#         }
#         # Convert dict to tuple for hashable set
#         row_tuple = tuple(row_data.items())
#         if row_tuple not in seen:
#             seen.add(row_tuple)
#             data.append(row_data)

#     con.close()
#     return data

# # Function to detect inside bars (iBars) and return datetime ranges
# def detect_consecutive_ibars(df, interval, max_inside_bars=12, height_ratio_threshold=0.6, similar_height_threshold=0.4, max_similar_height=2, body_to_wick_ratio=0.7):
#     consecutive_ibars = [False] * len(df)
#     i = 0
#     inside_bar_ranges = []  # To store datetime ranges of detected patterns

#     while i < len(df) - 1:
#         previous_candle = df.iloc[i]
#         main_height = previous_candle['High'] - previous_candle['Low']
#         main_body = abs(previous_candle['Open'] - previous_candle['Close'])
#         main_wick = main_height - main_body

#         # Check if the body is significantly larger than the wicks
#         if main_wick == 0 or main_body / main_wick < body_to_wick_ratio:
#             i += 1
#             continue

#         # Start looking for inside bars after the current candle
#         j = i + 1
#         count = 0
#         similar_height_count = 0
#         tall_inside_count = 0
#         while j < len(df) and \
#             (df.iloc[j]['High'] < previous_candle['High']) and \
#             (df.iloc[j]['Low'] > previous_candle['Low']) and \
#             (df.iloc[j]['Close'] < previous_candle['High']) and \
#             (df.iloc[j]['Open'] > previous_candle['Low']):

#             inside_height = df.iloc[j]['High'] - df.iloc[j]['Low']
#             if inside_height >= main_height * height_ratio_threshold:
#                 similar_height_count += 1
#                 if similar_height_count > max_similar_height:
#                     break

#             if inside_height >= main_height * similar_height_threshold:
#                 tall_inside_count += 1

#             count += 1
#             j += 1

#         # Check if the count of inside bars is within the allowed limit
#         if count > 3 and count <= max_inside_bars and similar_height_count <= max_similar_height:
#             if tall_inside_count / count < 0.5:  # Check if less than 50% of inside bars are tall
#                 start_time = df.iloc[i]['Date']  # Start of the pattern
#                 end_time = df.iloc[j-1]['Date']  # End of the pattern
#                 inside_bar_ranges.append(f"{start_time} - {end_time}")
#         # Move index to the end of the current sequence
#         i = j if count == 0 else i + 1

#     return inside_bar_ranges

# # Function to detect double tops and return datetime ranges
# def detect_double_tops(df):
#     def calculate_angle_and_validate(p1, p2, angle_min, angle_max):
#         x1, y1 = p1
#         x2, y2 = p2
#         angle_rad = np.arctan2(y2 - y1, x2 - x1)
#         angle_deg = np.degrees(angle_rad)
#         return angle_min <= angle_deg <= angle_max

#     def calculate_length(p1, p2):
#         return np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

#     def validate_lengths(a, b, c, d, e):
#         length_ab = calculate_length((0, a), (1, b))
#         length_bc = calculate_length((1, b), (2, c))
#         length_cd = calculate_length((2, c), (3, d))
#         length_de = calculate_length((3, d), (4, e))
#         max_length = max(length_ab, length_bc, length_cd, length_de)
#         return (length_ab >= 0.3 * max_length and
#                 length_bc >= 0.3 * max_length and
#                 length_cd >= 0.3 * max_length and
#                 length_de >= 0.3 * max_length)

#     def find_doubles_patterns(max_min):
#         patterns_tops = []
#         dates = []
#         for i in range(5, len(max_min)):
#             window = max_min.iloc[i-5:i]
#             if window.index[-1] - window.index[0] > 50:
#                 continue

#             a = window.iloc[0]['Low']
#             b = window.iloc[1]['High']
#             c = window.iloc[2]['Low']
#             d = window.iloc[3]['High']
#             e = window.iloc[4]['Low']

#             date_a = window['Date'].iloc[0]
#             date_b = window['Date'].iloc[1]
#             date_c = window['Date'].iloc[2]
#             date_d = window['Date'].iloc[3]
#             date_e = window['Date'].iloc[4]

#             if a < b and b > c and c < d and e < d and d > a and b > e and a < c and c > e:
#                 patterns_tops.append((a, b, c, d, e))
#                 dates.append([date_a, date_b, date_c, date_d, date_e])

#         return patterns_tops, dates

#     def validate_dtop(patterns_tops, dates):
#         filtered_patterns = []
#         filtered_dates = []
#         for pattern, date in zip(patterns_tops, dates):
#             a, b, c, d, e = pattern
#             if (calculate_angle_and_validate((0, a), (1, b), 70, 90) and
#                 calculate_angle_and_validate((1, b), (2, c), -90, -70) and
#                 calculate_angle_and_validate((2, c), (3, d), 70, 90) and
#                 calculate_angle_and_validate((3, d), (4, e), -90, -70)) and \
#                validate_lengths(a, b, c, d, e):
#                 filtered_patterns.append(pattern)
#                 filtered_dates.append(date)
#         return filtered_patterns, filtered_dates

#     def find_local_max_min(df, window, smooth=False, smoothing_period=3):
#         local_max_arr = []
#         local_min_arr = []
#         if smooth:
#             smooth_close = df['Close'].rolling(window=smoothing_period).mean().dropna()
#             local_max = argrelextrema(smooth_close.values, np.greater)[0]
#             local_min = argrelextrema(smooth_close.values, np.less)[0]
#         else:
#             local_max = argrelextrema(df['Close'].values, np.greater)[0]
#             local_min = argrelextrema(df['Close'].values, np.less)[0]
#         for i in local_max:
#             if (i > window) and (i < len(df) - window):
#                 local_max_arr.append(df.iloc[i-window:i+window]['Close'].idxmax())
#         for i in local_min:
#             if (i > window) and (i < len(df) - window):
#                 local_min_arr.append(df.iloc[i-window:i+window]['Close'].idxmin())
#         maxima = pd.DataFrame(df.loc[local_max_arr])
#         minima = pd.DataFrame(df.loc[local_min_arr])
#         max_min = pd.concat([maxima, minima]).sort_index()
#         max_min = max_min[~max_min.index.duplicated()]
#         return max_min

#     window = 10
#     max_min = find_local_max_min(df, window, smooth=True)
#     patterns_tops, dates = find_doubles_patterns(max_min)
#     filtered_patterns, dtop_dates = validate_dtop(patterns_tops, dates)

#     double_top_ranges = []
#     for pattern, date in zip(filtered_patterns, dtop_dates):
#         double_top_ranges.append(f"{date[0].strftime('%Y-%m-%d %H:%M:%S')} - {date[4].strftime('%Y-%m-%d %H:%M:%S')}")

#     return double_top_ranges

# # List of stock symbols to process
# stocks = [
#     "NSE:ABB-EQ", "NSE:ACC-EQ", "NSE:APLAPOLLO-EQ", "NSE:AUBANK-EQ",
#     "NSE:ADANIENSOL-EQ", "NSE:ADANIENT-EQ", "NSE:ADANIGREEN-EQ"
# ]

# # Only use 15-minute interval
# intervals = ['15']

# # Initialize results dictionary
# results = {symbol: {interval: {'iBars': [], 'Double Tops': []} for interval in intervals} for symbol in stocks}

# # Process each stock symbol and interval
# for symbol in stocks:
#     print(f"Processing symbol: {symbol}")
#     for interval in intervals:
#         print(f"  Processing interval: {interval} minutes")
#         data = fetch_data_from_db(symbol, interval)

#         if not data:
#             print(f"    No data fetched for interval {interval} minutes.")
#             continue

#         df = pd.DataFrame(data)
#         df['Date'] = pd.to_datetime(df['Date'])

#         # Detect inside bars and collect datetime ranges
#         ibar_ranges = detect_consecutive_ibars(df, interval)
#         results[symbol][interval]['iBars'] = ibar_ranges

#         # Detect double tops and collect datetime ranges
#         double_top_ranges = detect_double_tops(df)
#         results[symbol][interval]['Double Tops'] = double_top_ranges

# # Convert results to DataFrame
# results_df = pd.DataFrame(results).T

# # Filter to only show symbols with detected patterns
# filtered_results_df = results_df[(results_df.applymap(lambda x: len(x['iBars']) > 0 or len(x['Double Tops']) > 0)).any(axis=1)]

# print(filtered_results_df)


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
            WHERE DATE(`date`) BETWEEN CURDATE() - INTERVAL 5 DAY AND CURDATE() - INTERVAL 1 DAY  -- Previous 3 weekdays
            AND WEEKDAY(`date`) < 5  -- Exclude weekends
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

    return inside_bar_ranges

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

    alldays = set(df['Date'][0] + timedelta(x)
                  for x in range((df['Date'].iloc[-1] - df['Date'][0]).days))

    window = 4
    max_min = find_custom_peaks(df, window)
    patterns_tops, dates = find_doubles_patterns(max_min)

    # Validate and filter patterns
    filtered_patterns, dtop_dates = validate_patterns(
        patterns_tops, dates)

    double_top_ranges = []
    for pattern, date in zip(filtered_patterns, dtop_dates):
        double_top_ranges.append(
            f"{date[0].strftime('%Y-%m-%d %H:%M:%S')} - {date[4].strftime('%Y-%m-%d %H:%M:%S')}")

    return double_top_ranges


# List of stock symbols to process
stocks = ['NSE:360ONE-EQ',
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
          'MCX:SILVER24DECFUT',
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
          'MCX:CRUDEOILM24SEPFUT'
          ]

# Only use 15-minute interval
intervals = ['15']

# Initialize results list to store the data
results = []

# Process each stock symbol and interval
for symbol in stocks:
    for interval in intervals:
        data = fetch_data_from_db(symbol, interval)

        if not data:
            continue

        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])

        # Detect inside bars and collect datetime ranges
        ibar_ranges = detect_consecutive_ibars(df, interval)

        # Detect double tops and collect datetime ranges
        double_top_ranges = detect_double_tops(df)

        # Append results
        for ibar in ibar_ranges:
            results.append({'Stock': symbol, 'Interval': interval,
                           'Pattern': 'Inside Bar', 'Date Range': ibar})
        for double_top in double_top_ranges:
            results.append({'Stock': symbol, 'Interval': interval,
                           'Pattern': 'Double Top', 'Date Range': double_top})

# Convert results to DataFrame
results_df = pd.DataFrame(results)

# Save the results to a CSV file
csv_file_path = "stock_patterns.csv"
results_df.to_csv(csv_file_path, index=False)

csv_file_path
