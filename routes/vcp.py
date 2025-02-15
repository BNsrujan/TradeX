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

bp = Blueprint('vcp', __name__)

@bp.route('/vcp-pattern', methods=['GET'])
def get_vcp_patterns():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')

    # Fetch data from database
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

    # Capitalize and rename columns
    df = df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
        'Date': 'date'
    })

    def calculate_angle_and_validate(p1, p2, angle_min, angle_max):
        x1, y1 = p1
        x2, y2 = p2
        angle = degrees(atan2(y2 - y1, x2 - x1))
        # Check if the angle is within the specified range
        return angle_min <= angle <= angle_max

    def find_doubles_patterns(max_min):
        patterns_tops = []
        dates = []

        for i in range(7, len(max_min)):
            window = max_min.iloc[i-7:i]

            if window.index[-1] - window.index[0] > 200:
                continue

            a = window.iloc[0]['close']
            b = window.iloc[1]['close']
            c = window.iloc[2]['close']
            d = window.iloc[3]['close']
            e = window.iloc[4]['close']
            f = window.iloc[5]['close']

            date_a = window['date'].iloc[0]
            date_b = window['date'].iloc[1]
            date_c = window['date'].iloc[2]
            date_d = window['date'].iloc[3]
            date_e = window['date'].iloc[4]
            date_f = window['date'].iloc[5]

            # Define the points a, b, c, d, e,f
            a_high = window.iloc[0]['high']
            b_low = window.iloc[1]['low']
            c_high = window.iloc[2]['high']
            d_low = window.iloc[3]['low']
            e_high = window.iloc[4]['high']
            f_low = window.iloc[5]['low']

            if a_high < b_low and b_low > c_high and c_high < d_low and d_low > e_high and e_high < f_low:
                patterns_tops.append((a, b, c, d, e,f))
                dates.append([date_a, date_b, date_c, date_d, date_e,date_f])

        return patterns_tops, dates
        
    def validate_patterns(patterns_tops, dates):
        filtered_patterns = []
        filtered_dates = []

        for pattern, date in zip(patterns_tops, dates):
            a, b, c, d, e ,f= pattern
            filtered_patterns.append(pattern)
            filtered_dates.append(date)

        return filtered_patterns, filtered_dates


    def find_immediate_uptrend(df, start_idx, breakout_price):
        """
        Identify the immediate upward trend after the breakout point.
        """
        for i in range(start_idx + 1, len(df)):
            # Check if the trend stops (price no longer increases)
            if df['close'].iloc[i] <= df['close'].iloc[i - 1]:
                return i - 1  # Return the previous index where the trend was still valid
        return len(df) - 1  # Default to the last point if the trend continues till the end
    
    def find_local_max_min(df, window, smooth=False, smoothing_period=3):
        local_max_arr = []
        local_min_arr = []

        if smooth:
            smooth_close = df['close'].rolling(window=smoothing_period).mean().dropna()
            local_max = argrelextrema(smooth_close.values, np.greater)[0]
            local_min = argrelextrema(smooth_close.values, np.less)[0]
        else:
            local_max = argrelextrema(df['close'].values, np.greater)[0]
            local_min = argrelextrema(df['close'].values, np.less)[0]

        for i in local_max:
            if (i > window) and (i < len(df) - window):
                local_max_arr.append(df.iloc[i-window:i+window]['close'].idxmax())

        for i in local_min:
            if (i > window) and (i < len(df) - window):
                local_min_arr.append(df.iloc[i-window:i+window]['close'].idxmin())

        maxima = pd.DataFrame(df.loc[local_max_arr])
        minima = pd.DataFrame(df.loc[local_min_arr])
        max_min = pd.concat([maxima, minima]).sort_index()
        max_min = max_min[~max_min.index.duplicated()]
        #print(max_min)
        return max_min


    # Process data
    window = 4
    max_min = find_local_max_min(df, window)
    patterns, dates = find_doubles_patterns(max_min)

    # Validate patterns
    filtered_patterns, filtered_dates = validate_patterns(patterns, dates)

    # Prepare JSON response
    # coordinates = []
    # for pattern, date in zip(filtered_patterns, filtered_dates):
    #     coordinates.append({
    #         'x0': date[0].strftime('%Y-%m-%d %H:%M:%S'),
    #         'x1': date[1].strftime('%Y-%m-%d %H:%M:%S'),
    #         'x2': date[2].strftime('%Y-%m-%d %H:%M:%S'),
    #         'x3': date[3].strftime('%Y-%m-%d %H:%M:%S'),
    #         'x4': date[4].strftime('%Y-%m-%d %H:%M:%S'),
    #         'x5': date[5].strftime('%Y-%m-%d %H:%M:%S'),
    #         'y0': pattern[0],
    #         'y1': pattern[1],
    #         'y2': pattern[2],
    #         'y3': pattern[3],
    #         'y4': pattern[4],
    #         'y5': pattern[5]
    #     })

    # Prepare JSON response
    coordinates = []
    for pattern, date in zip(filtered_patterns, filtered_dates):
        coordinates.append({
            'x0': date[0].strftime('%Y-%m-%d %H:%M:%S'),
            'x1': date[1].strftime('%Y-%m-%d %H:%M:%S'),
            'x2': date[2].strftime('%Y-%m-%d %H:%M:%S'),
            'x3': date[3].strftime('%Y-%m-%d %H:%M:%S'),
            'x4': date[4].strftime('%Y-%m-%d %H:%M:%S'),
            'x5': date[5].strftime('%Y-%m-%d %H:%M:%S'),
            'y0': pattern[0],
            'y1': pattern[1],
            'y2': pattern[2],
            'y3': pattern[3],
            'y4': pattern[4],
            'y5': pattern[5]
        })



    return jsonify(coordinates)
