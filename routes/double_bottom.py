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


bp = Blueprint('double_bottoms', __name__)

@bp.route('/double-bottoms', methods=['GET'])
def get_double_bottoms():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')

    # Fetch historical and possibly current data from the database
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

    # Prepare JSON data
    coordinates = []
    for pattern, date in zip(filtered_patterns, filtered_dates):
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
