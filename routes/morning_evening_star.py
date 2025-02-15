from flask import Flask, jsonify, Blueprint, request
import pandas as pd
from decimal import Decimal
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

app = Flask(__name__)

# Blueprint for candlestick patterns
bp = Blueprint('morning_evening_star', __name__)


@bp.route('/morning_evening_star', methods=['GET'])
def get_candlestick_patterns():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')

    # Fetch data from the database and current day if necessary
    data1 = fetch_data_from_db(symbol, interval)
    data2 = fetch_currentday_data(
        symbol, interval) if compare_db_current_date(symbol) else []
    data = data1 + data2

    # Convert data to a DataFrame
    df = pd.DataFrame(data)
    df.columns = [col.capitalize() for col in df.columns]
    df['Date'] = pd.to_datetime(df['Date'])

    morning_star_dates, morning_star_values = [], []
    evening_star_dates, evening_star_values = [], []

    # Detect Morning Star and Evening Star patterns
    for i in range(2, len(df) - 2):
        first, second, third = df.iloc[i-1], df.iloc[i], df.iloc[i+1]

        def candle_length(open, close):
            return abs(open - close)

        # Morning Star criteria
        if first['Close'] < first['Open'] and second['Close'] > second['Open'] and third['Close'] > third['Open']:
            len_first = candle_length(first['Open'], first['Close'])
            len_second = candle_length(second['Open'], second['Close'])
            len_third = candle_length(third['Open'], third['Close'])

            if (len_second < 0.25 * len_first and
                second['Open'] > first['Close'] and second['Close'] < first['Open'] and
                    len_third > 0.6 * len_first):
                morning_star_dates.append(df['Date'][i])
                morning_star_values.append(df['High'][i])

        # Evening Star criteria
        elif first['Close'] > first['Open'] and second['Close'] < second['Open'] and third['Close'] < third['Open']:
            len_first = candle_length(first['Open'], first['Close'])
            len_second = candle_length(second['Open'], second['Close'])
            len_third = candle_length(third['Open'], third['Close'])

            if (len_second < 0.25 * len_first and
                second['Open'] < first['Close'] and second['Close'] > first['Open'] and
                    len_third > 0.6 * len_first):
                evening_star_dates.append(df['Date'][i])
                evening_star_values.append(df['High'][i])

    # Prepare response
    morning_star_data = [{"date": date.isoformat(), "value": value}
                         for date, value in zip(morning_star_dates, morning_star_values)]
    evening_star_data = [{"date": date.isoformat(), "value": value}
                         for date, value in zip(evening_star_dates, evening_star_values)]

    return jsonify({
        "morning_star": morning_star_data,
        "evening_star": evening_star_data
    })
