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

bp = Blueprint('double_top', __name__)

@bp.route('/double-top', methods=['GET'])
def get_double_top_patterns():
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

    # Capitalize the first letter of 'open', 'high', 'low', 'close', 'volume', and 'date'
    df = df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'date': 'Date'
    })

    df['Date'] = pd.to_datetime(df['Date'])

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
    filtered_patterns_dtop, filtered_dates_dtop = validate_patterns(
        patterns_tops, dates)

    # Prepare JSON data
    coordinates = []
    for pattern, date in zip(filtered_patterns_dtop, filtered_dates_dtop):
        coordinates.append({
            'x0': date[0].strftime('%Y-%m-%d %H:%M:%S'),
            'x1': date[1].strftime('%Y-%m-%d %H:%M:%S'),
            'x2': date[2].strftime('%Y-%m-%d %H:%M:%S'),
            'x3': date[3].strftime('%Y-%m-%d %H:%M:%S'),
            'x4': date[4].strftime('%Y-%m-%d %H:%M:%S'),
            'y0': pattern[0],
            'y1': pattern[1],
            'y2': pattern[2],
            'y3': pattern[3],
            'y4': pattern[4]
        })

    return jsonify(coordinates)
