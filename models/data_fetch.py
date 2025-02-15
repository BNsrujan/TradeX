import pandas as pd
from models.db import create_connection
from fyers_apiv3 import fyersModel
import datetime as dt
from models.db import execute_query, create_connection
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import os
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
from config import db_config3, db_config2
import datetime

dtime_datetime = dt.datetime.now()

# Check if the current day is Saturday (5) or Sunday (6)
if dtime_datetime.weekday() in (5, 6):  # Saturday is 5 and Sunday is 6
    dtime = ""  # Empty string if it's a weekend
else:
    # dtime_datetime += timedelta(hours=12, minutes=30)
    # Format date if it's a weekday
    dtime = dtime_datetime.strftime("%Y-%m-%d")

# Initialize fyers
def init_fyers():
    with open("abcd.txt", 'r') as r:
        access_token = r.read()
    client_id = "XIMVLEN5IZ-100"
    return fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path=os.getcwd())

fyers = init_fyers()

def fetch_from_fyers(symbol, interval):
    dtime = dt.datetime.now().strftime("%Y-%m-%d")
    prev = dt.datetime.strptime(dtime, "%Y-%m-%d")
    prev_date = prev - relativedelta(months=1 if interval == '1' else 2)
    prev_date = prev_date.strftime("%Y-%m-%d")
    
    data = {
        "symbol": symbol,
        "resolution": interval,
        "date_format": "1",
        "range_from": prev_date,
        "range_to": dtime,
        "cont_flag": "1"
    }
    
    df = fyers.history(data=data)
    if df['s'] == 'no_data':
        return []
    
    df = pd.DataFrame(df['candles'])
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date'], unit='s').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
    df_sorted = df.sort_values(by=['date'], ascending=True).drop_duplicates(subset='date', keep='first')
    df_sorted.reset_index(drop=True, inplace=True)
    df_sorted['date'] = df_sorted['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return df_sorted.rename(columns={'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}).to_dict(orient='records')

# Add other fetching functions...
nse_holidays_2024 = [
    date(2024, 1, 26),  # Republic Day
    date(2024, 3, 8),   # Mahashivratri
    date(2024, 3, 25),  # Holi
    date(2024, 3, 29),  # Good Friday
    date(2024, 4, 11),  # Id-Ul-Fitr
    date(2024, 4, 17),  # Shri Ram Navami
    date(2024, 5, 1),   # Maharashtra Day
    date(2024, 6, 17),  # Bakri Id
    date(2024, 7, 17),  # Muharram
    date(2024, 8, 15),  # Independence Day
    date(2024, 10, 3),  # Mahatma Gandhi Jayanti
    date(2024, 11, 1),  # Diwali - Laxmi Pujan
    date(2024, 11, 15),  # Gurunanak Jayanti
    date(2024, 12, 25)  # Christmas
]

# Function to check if the current date is a holiday


def is_market_open(current_date):
    return current_date not in nse_holidays_2024

def fetch_currentday_data(symbol, interval):
    # Check if the market is open
    today = datetime.date.today()
    if not is_market_open(today):
        print(f"No data fetched. Market is closed on {today} (Holiday).")
        return []

    # The rest of the function remains the same if the market is open
    interval = int(interval)

    dtime = datetime.datetime.now().strftime("%Y-%m-%d")
    data = {
        "symbol": symbol,
        "resolution": '5S',
        "date_format": "1",
        "range_from": dtime,
        "range_to": dtime,
        "cont_flag": "1"
    }

    # Fetch historical data using the fyers API (assuming fyers is already initialized)
    df = fyers.history(data=data)

    # If no data is available, return empty list
    if df['s'] == 'no_data':
        return []

    # Processing the data into a DataFrame
    df = pd.DataFrame(df['candles'])
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date'], unit='s')
    df.date = (df.date.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata'))
    df['date'] = df['date'].dt.tz_localize(None)

    # Sort and remove duplicates
    df_sorted = df.sort_values(by=['date'], ascending=True)
    df = df_sorted.drop_duplicates(subset='date', keep='first')
    df.reset_index(drop=True, inplace=True)

    # Group the data based on the interval
    df['group'] = (df.index // (interval * 12))
    df2 = df.groupby('group').agg({
        'date': 'first',
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).reset_index(drop=True)

    # Format the date and prepare the final data
    df2['date'] = df2['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    data2 = df2.rename(columns={
        'date': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }).to_dict(orient='records')

    return data2

def read_stocks_from_file(filename='500stocks.txt'):
    """
    Reads stock symbols from a specified file and returns them as a list.
    
    Parameters:
    filename (str): The path to the file containing stock symbols. Default is '500stocks.txt'.
    
    Returns:
    list: A list of stock symbols.
    
    Raises:
    FileNotFoundError: If the specified file does not exist.
    IOError: If there is an issue reading the file.
    """
    stocks = []
    try:
        with open(filename, 'r') as file:  # Use the provided filename
            for line in file:
                stocks.append(line.strip())  # Strip whitespace/newline characters
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
    except IOError:
        print(f"Error: Could not read the file {filename}.")
    # print(stocks)
    return stocks


def fetch_data_from_db(symbol, interval):

    con = mysql.connector.connect(**db_config3)
    cur = con.cursor()
    sym = symbol
    parts = sym.split(':')[-1].replace('-', '_').replace('&', '_')
    sym = parts.lower()

    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'stocks'")
    tables = cur.fetchall()
    tables = [table[0] for table in tables]
    if sym not in tables or interval == '1' or interval == '3':
        return []
    # Example SQL query (adjust as per your schema)
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
            LIMIT 2000 
        ) AS t
        INNER JOIN {sym} ae ON ae.`date` = t.max_date
        ORDER BY t.max_date ASC;
            """
    cur.execute(query)
    rows = cur.fetchall()
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

def compare_db_current_date(symbol):
    con = mysql.connector.connect(**db_config3)
    cur = con.cursor()
    sym = symbol
    parts = sym.split(':')[-1].replace('-', '_').replace('&', '_')
    sym = parts.lower()
    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'stocks'")
    tables = cur.fetchall()
    tables = [table[0] for table in tables]
    if sym not in tables:
        return True
    cur.execute(f"SELECT MAX(`date`) FROM {sym}")
    ltime = cur.fetchall()
    ltime = ltime[0][0].strftime('%Y-%m-%d')
    if dtime > ltime:
        return True
    return False


def is_email_registered(email):
    conn = mysql.connector.connect(**db_config2)
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE mailid = %s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is not None

def insert_user(user_data):
    conn = mysql.connector.connect(**db_config2)
    cursor = conn.cursor()

    # Insert user data into the database
    insert_query = """
    INSERT INTO users (name, lastname, mailid, phone, experience, capital, password, user_type, trader_type)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        user_data['name'],
        user_data['lastname'],
        user_data['mailid'],
        user_data['phone'],
        user_data['experience'],
        user_data['capital'],
        user_data['password'],
        user_data['user_type'],
        # Insert the trader types as a comma-separated string
        user_data['trader_type']
    ))

    conn.commit()
    cursor.close()
    conn.close()

def check_user_credentials(email, password):
    conn = mysql.connector.connect(**db_config2)
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE mailid = %s AND password = %s AND user_type = 'admin'"
    cursor.execute(query, (email, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_livemint_data():
    url = "https://www.livemint.com/market/quarterly-results-calendar"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')
    headers = ["stocks", "result_date", "purpose"]
    rows = []
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        cells_text = [cell.text.strip() for cell in cells]
        rows.append(cells_text)

    df = pd.DataFrame(rows, columns=headers)

    def parse_result_date(date_str):
        try:
            return pd.to_datetime(date_str, format='%d %b %Y').strftime('%Y-%m-%d')
        except ValueError:
            return None

    df['result_date'] = df['result_date'].apply(parse_result_date)
    df = df.dropna(subset=['result_date'])

    return df


def get_usi_data():
    url = "https://www.usinflationcalculator.com/inflation/consumer-price-index-release-schedule/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    rows = soup.select('tbody > tr')
    headers = ["release_date", "release_time"]
    data = []
    for row in rows:
        cells = [cell.text.strip() for cell in row.find_all('td')]
        # Skip the month column and fetch only release_date and release_time
        data.append(cells[1:3])

    df = pd.DataFrame(data, columns=headers)

    def parse_release_date(date_str):
        if not date_str:
            return None
        try:
            return pd.to_datetime(date_str, format='%b. %d, %Y').strftime('%Y-%m-%d')
        except ValueError:
            try:
                return pd.to_datetime(date_str, format='%b %d, %Y').strftime('%Y-%m-%d')
            except ValueError:
                return None

    df['release_date'] = df['release_date'].apply(parse_release_date)
    df = df.dropna(subset=['release_date'])

    return df

def fetch_data_for_current_month():
    current_month = datetime.now().month
    current_year = datetime.now().year

    connection = create_connection()
    cursor = connection.cursor()

    # Fetch LiveMint data for the current month
    query_livemint = """
    SELECT stocks, DATE_FORMAT(result_date, '%Y-%m-%d') as result_date, purpose
    FROM livemint_data
    WHERE MONTH(result_date) = %s AND YEAR(result_date) = %s
    ORDER BY result_date;
    """
    cursor.execute(query_livemint, (current_month, current_year))
    livemint_data = cursor.fetchall()
    livemint_df = pd.DataFrame(livemint_data, columns=[
                               "stocks", "result_date", "purpose"])

    # Fetch USI data for the current month
    query_usi = """
    SELECT DATE_FORMAT(release_date, '%Y-%m-%d') as release_date, release_time
    FROM usi_data
    WHERE MONTH(release_date) = %s AND YEAR(release_date) = %s
    ORDER BY release_date;
    """
    cursor.execute(query_usi, (current_month, current_year))
    usi_data = cursor.fetchall()
    usi_df = pd.DataFrame(usi_data, columns=["release_date", "release_time"])

    cursor.close()
    connection.close()

    return livemint_df, usi_df

def store_data(df, table_name):
    existing_data = fetch_existing_data(table_name)
    existing_rows = set([tuple(row[1:])
                        for row in existing_data])  # Exclude the id column

    new_data = [tuple(row) for row in df.values]
    new_rows = [row for row in new_data if row not in existing_rows]

    if new_rows:
        placeholders = ", ".join(["%s"] * len(df.columns))
        columns = ", ".join(df.columns)
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        execute_query(query, new_rows)

def fetch_existing_data(table_name):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    existing_data = cursor.fetchall()
    cursor.close()
    connection.close()
    return existing_data
