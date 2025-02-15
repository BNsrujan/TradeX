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
from flask import Blueprint, render_template
from models.data_fetch import fetch_data_for_current_month, store_data

with open("abcd.txt", 'r') as r:
    access_token = r.read()
    
# access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3MjI4MzA5MzcsImV4cCI6MTcyMjkwNDI1NywibmJmIjoxNzIyODMwOTM3LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbXNGQlpYWVdwdW5GTHJhYWpvRnFsZGdMUlVRbVdNUXpPaGZSNlIwSlhtNnVDdU5ZaUR3RkxiTVo2aXowNTFKZW5kaHRDc3dRbWpRSVJHZk1TTnlPMDIxck5jaWlCZHRkMzdFWHZfanZBZk51bUVyQT0iLCJkaXNwbGF5X25hbWUiOiJMT0tFU0ggVEFMTFVSSSIsIm9tcyI6IksxIiwiaHNtX2tleSI6IjgzZmZjNDBhNDBhNmMzMmVhODEyZmZlNjg4MDg2ZjA2NGE2NTU4OGU5NTEyNjdhOTA4MDQzMjU3IiwiZnlfaWQiOiJZTDAwMTM3IiwiYXBwVHlwZSI6MTAwLCJwb2FfZmxhZyI6Ik4ifQ.GxWlrPGFjQ0apekow-TPIb-DmMGidl0DRNZ5N71Kuiw'
client_id = "XIMVLEN5IZ-100"
fyers = fyersModel.FyersModel(
    client_id=client_id, is_async=False, token=access_token, log_path=os.getcwd())

from models.data_fetch import (
    get_livemint_data,
    get_usi_data,
    fetch_data_from_db,
    fetch_currentday_data,
    compare_db_current_date,
    read_stocks_from_file,
)
import pandas as pd

bp = Blueprint('data', __name__)

@bp.route('/news')
def news_page():
    livemint_df = get_livemint_data()
    usi_df = get_usi_data()

    # Store data in the database (implement store_data if not done)
    store_data(livemint_df, 'livemint_data')
    store_data(usi_df, 'usi_data')

    livemint_df, usi_df = fetch_data_for_current_month()
    livemint_html = livemint_df.to_html(classes='data', index=False)
    usi_html = usi_df.to_html(classes='data', index=False)

    return render_template('newsorig.html', livemint_data=livemint_html, usi_data=usi_html)

@bp.route('/analysis')
def analysis_page():
    return render_template('analysis.html')

@bp.route('/submit_stock', methods=['POST'])
def submit_stock():
    new_stock_input = request.json.get('newStockInput')
    try:
        data = {
            "symbol": new_stock_input,
            "resolution": "5",
            "date_format": "1",
            "range_from": "2024-07-03",
            "range_to": "2024-07-03",
            "cont_flag": "1"
        }
        df = pd.DataFrame(fyers.history(data=data)['candles'])
        return jsonify({'status': 1})
    except KeyError:
        return jsonify({'status': 0})

@bp.route('/get_50_stocks', methods=['GET'])
def get_50_stocks():
    stocks_50 = read_stocks_from_file()
    return jsonify(stocks_50)


@bp.route('/stock-data')
def get_data():
    symbol = request.args.get('symbol', 'NSE:NIFTY50-INDEX')
    interval = int(request.args.get('interval', '5'))

    # Fetch data from database
    data1 = fetch_data_from_db(symbol, interval)
    
    # Fetch current day data if needed
    if compare_db_current_date(symbol):
        data2 = fetch_currentday_data(symbol, interval)
    else:
        data2 = []

    data = data1 + data2
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Data not found'}), 404

@bp.route('/graph')
def graph():
    if 'email' in session:
        # Fetch symbol and patterns from the session
        symbol = session.get('symbol', '')
        patterns = session.get('patterns', [])  # Default to an empty list if not set

        # Debugging: Check the retrieved values
        # print("Symbol passed to graph:", symbol)
        # print("Patterns passed to graph:", patterns)

        # Pass both symbol and patterns to the template
        return render_template('graph.html', symbol=symbol, patterns=patterns)

    # Redirect to login if email is not in session
    return redirect(url_for('auth.login'))