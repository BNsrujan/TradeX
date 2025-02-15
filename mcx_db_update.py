import mysql.connector
from fyers_apiv3 import fyersModel
import pandas as pd
import os
import pandas as pd
import plotly.graph_objects as go
import datetime as dt
from datetime import timedelta, datetime
from fyers_apiv3.FyersWebsocket import data_ws
with open("abcd.txt", 'r') as r:
    access_token = r.read()
client_id = "DZO41L3M36-100"
fyers = fyersModel.FyersModel(
    client_id=client_id, is_async=False, token=access_token, log_path=os.getcwd())
fyers.get_profile()

lines = [
    'NSE:MCX-EQ',
    'MCX:SILVER24DECFUT',
    'MCX:CRUDEOILM24SEPFUT',
    'MCX:SILVERM24NOVFUT',
    'MCX:GOLD25FEBFUT',
    'MCX:SILVER25MARFUT',
    'BSE:SENSEX-INDEX'
]

# Database configuration
db_config = {
    'host': '118.139.182.3',
    'user': 'sqluser1',
    'password': 'TGDp0U&[1Y4S',
    'database': 'stocks'
}

# Connect to MySQL database
con = mysql.connector.connect(**db_config)
cur = con.cursor()

# Define date for data fetching
yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

# Loop through each stock symbol and fetch data
for line in lines:
    try:
        line = line.strip()
        data = {
            "symbol": line,
            "resolution": "5",
            "date_format": "1",
            "range_from": yesterday,
            "range_to": yesterday,
            "cont_flag": "1"
        }

        # Fetching historical data from Fyers API
        df = fyers.history(data=data)
        df = pd.DataFrame(df['candles'])
        df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        df['date'] = pd.to_datetime(df['date'], unit='s')
        df['date'] = df['date'].dt.tz_localize(
            'UTC').dt.tz_convert('Asia/Kolkata')
        df['date'] = df['date'].dt.tz_localize(None)

        # Sorting and removing duplicates
        df_sorted = df.sort_values(by=['date'], ascending=True)
        df = df_sorted.drop_duplicates(subset='date', keep='first')
        df.reset_index(drop=True, inplace=True)

        # Prepare table name from stock symbol
        parts = line.split(':')[-1].replace('-', '_').replace('&', '_')
        table_name = parts.lower()

        # Insert data into database
        for _, row in df.iterrows():
            query = f"""
                INSERT IGNORE INTO {table_name} 
                VALUES ('{row['date']}', {row['open']}, {row['high']}, {row['low']}, {row['close']}, {row['volume']})
            """
            cur.execute(query)

        con.commit()
        print(f"Database for {table_name.upper()} updated successfully.")

    except Exception as e:
        # Print error message and skip to the next stock
        print(
            f"Error fetching data for {line}: {str(e)}. Skipping to next stock...")

# Close database connection
con.close()
