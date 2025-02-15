from flask import Blueprint, request, jsonify
import pandas as pd
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

bp = Blueprint('ema_series', __name__)

@bp.route('/ema-series', methods=['GET'])
def get_ema():
    symbol = request.args.get('symbol', 'NSE:NIFTY50-INDEX')
    interval = int(request.args.get('interval', '5'))
    periods = request.args.get('periods', '20')
    periods = [int(p) for p in periods.split(',') if p.isdigit() and int(p) > 0]

    data1 = fetch_data_from_db(symbol, interval)
    if compare_db_current_date(symbol):
        data2 = fetch_currentday_data(symbol, interval)
    else:
        data2 = []
    data = data1 + data2

    df = pd.DataFrame(data)

    if df.empty:
        return jsonify([])

    df['Date'] = pd.to_datetime(df['Date'])

    def calculate_ema(prices, period):
        alpha = 2 / (period + 1)
        ema = [None] * len(prices)
        initial_sma = sum(prices[:period]) / period
        ema[period - 1] = initial_sma
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i - 1]) * alpha + ema[i - 1]
        return ema

    ema_data = {"Date": df["Date"].dt.strftime('%Y-%m-%d %H:%M:%S')}
    for period in periods:
        ema_key = f"EMA{period}"
        df[ema_key] = calculate_ema(df["Close"], period)
        ema_data[ema_key] = df[ema_key]

    ema_data = df[["Date"] + [f"EMA{period}" for period in periods]].dropna().to_dict(orient='records')

    return jsonify(ema_data)
