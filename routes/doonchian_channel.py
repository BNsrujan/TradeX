from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

bp = Blueprint('Donchian_channel_strategy', __name__)

@bp.route('/Donchian_channel', methods=['GET'])
def get_donchian_channel():
    # Retrieve parameters with defaults
    symbol = request.args.get('symbol', 'NSE:NIFTY50-INDEX')
    interval = request.args.get('interval', '5')
    window = int(request.args.get('window', 20))  # Default to 20-period window

    # Fetch data from the database and current day
    data1 = fetch_data_from_db(symbol, interval)
    data2 = fetch_currentday_data(symbol, interval) if compare_db_current_date(symbol) else []

    # Combine data
    data = data1 + data2
    if not data:
        return jsonify([])

    # Convert to DataFrame
    df = pd.DataFrame(data)
    if "Close" not in df or "High" not in df or "Low" not in df or df.empty:
        return jsonify({"error": "No valid data found for the symbol"}), 400

    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Calculate Donchian Channel
    df["Upper_Band"] = df["High"].rolling(window=window).max()
    df["Lower_Band"] = df["Low"].rolling(window=window).min()
    df["Middle_Band"] = (df["Upper_Band"] + df["Lower_Band"]) / 2

    # Prepare data and convert to JSON
    donchian_data = df[["Date", "Middle_Band", "Upper_Band", "Lower_Band"]].dropna().to_dict(orient='records')

    # Convert datetime to string
    for item in donchian_data:
        item['Date'] = item['Date'].strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(donchian_data)