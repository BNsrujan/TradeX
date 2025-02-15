from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

bp = Blueprint('Bollinger_bands', __name__)

@bp.route('/Bollinger_bands', methods=['GET'])
def get_bollinger_bands():
    # Retrieve parameters with defaults
    symbol = request.args.get('symbol', 'NSE:NIFTY50-INDEX')
    interval = request.args.get('interval', '5')

    # Fetch data from the database and current day
    data1 = fetch_data_from_db(symbol, interval)
    data2 = fetch_currentday_data(symbol, interval) if compare_db_current_date(symbol) else []

    # Combine data
    data = data1 + data2
    if not data:
        return jsonify([])

    # Convert to DataFrame
    df = pd.DataFrame(data)
    if "Close" not in df or df.empty:
        return jsonify({"error": "No valid data found for the symbol"}), 400

    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Calculate Bollinger Bands
    df["Middle_Band"] = df["Close"].rolling(window=20).mean()
    df["Upper_Band"] = df["Middle_Band"] + (df["Close"].rolling(window=20).std() * 2)
    df["Lower_Band"] = df["Middle_Band"] - (df["Close"].rolling(window=20).std() * 2)

    # Prepare data and convert to JSON
    bollinger_data = df[["Date", "Middle_Band", "Upper_Band", "Lower_Band"]].dropna().to_dict(orient='records')
    
    # Convert datetime to string
    for item in bollinger_data:
        item['Date'] = item['Date'].strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(bollinger_data)