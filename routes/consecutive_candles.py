from flask import Flask, jsonify, Blueprint, request
import pandas as pd
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

bp = Blueprint('consecutive_candles', __name__)

@bp.route('/consecutive_candles', methods=['GET'])
def get_consecutive_candles():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')

    # Fetch data from the database and current day if necessary
    data1 = fetch_data_from_db(symbol, interval)
    data2 = fetch_currentday_data(symbol, interval) if compare_db_current_date(symbol) else []
    data = data1 + data2

    # Convert data to a DataFrame
    df = pd.DataFrame(data)
    df.columns = [col.capitalize() for col in df.columns]
    df['Date'] = pd.to_datetime(df['Date'])

    green_candle_dates = []
    red_candle_dates = []

    # Detect 4 or more consecutive green or red candles
    streak_type = None
    streak_count = 0
    streak_dates = []
    last_close = None  # To store the last candle's closing price

    for i in range(len(df)):
        current_candle = df.iloc[i]
        is_green = current_candle['Close'] > current_candle['Open']
        is_red = current_candle['Close'] < current_candle['Open']

        # If it's a green candle
        if is_green:
            if streak_type == "green":
                streak_count += 1  # Increment streak count for consecutive greens
            else:
                # If there was a red streak before, save the red streak if valid
                if streak_type == "red" and streak_count >= 4:
                    red_candle_dates.append({"dates": streak_dates, "value": last_close})

                streak_type = "green"  # Start a new green streak
                streak_count = 1
                streak_dates = [current_candle['Date'].isoformat()]

            last_close = current_candle['Close']  # Update last close for green candles

        # If it's a red candle
        elif is_red:
            if streak_type == "red":
                streak_count += 1  # Increment streak count for consecutive reds
            else:
                # If there was a green streak before, save the green streak if valid
                if streak_type == "green" and streak_count >= 4:
                    green_candle_dates.append({"dates": streak_dates, "value": last_close})

                streak_type = "red"  # Start a new red streak
                streak_count = 1
                streak_dates = [current_candle['Date'].isoformat()]

            last_close = current_candle['Close']  # Update last close for red candles

        streak_dates.append(current_candle['Date'].isoformat())

    # Handle any remaining streaks after the loop
    if streak_type == "green" and streak_count >= 4:
        green_candle_dates.append({"dates": streak_dates, "value": last_close})
    elif streak_type == "red" and streak_count >= 4:
        red_candle_dates.append({"dates": streak_dates, "value": last_close})

    # print("consecutive_green_candles", green_candle_dates)
    # print("consecutive_red_candles", red_candle_dates)

    return jsonify({
        "consecutive_green_candles": green_candle_dates,
        "consecutive_red_candles": red_candle_dates
    })
