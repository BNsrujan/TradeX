from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import logging
from datetime import timedelta
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data


bp = Blueprint('darvas_box', __name__)


@bp.route('/darvas-box', methods=['GET'])
def get_darvas_box_patterns():
    logging.basicConfig(level=logging.DEBUG)
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
    df = df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'date': 'Date'
    })
    df['Date'] = pd.to_datetime(df['Date'])

    def find_darvas_boxes(df, nbc=20, price_range_limit=150, chart_width_cm=100, chart_height_cm=50):
        df['rolling_high'] = df['High'].rolling(window=nbc).max()
        df['rolling_low'] = df['Low'].rolling(window=nbc).min()

        boxes = []
        active_box = None

        # Scaling factors
        candles_visible = len(df)  # Approximation of visible candles
        cm_per_candle = chart_width_cm / candles_visible
        cm_per_price_unit = chart_height_cm / \
            (df['High'].max() - df['Low'].min())

        for i in range(nbc - 1, len(df)):
            current_high = df['rolling_high'].iloc[i]
            current_low = df['rolling_low'].iloc[i]
            current_close = df['Close'].iloc[i]

            price_range = current_high - current_low
            if price_range <= price_range_limit:
                if active_box is None:
                    if i >= nbc:
                        active_box = {
                            'start_idx': i - nbc + 1,
                            'top': current_high,
                            'bottom': current_low,
                            'width': 1
                        }
                else:
                    if current_close > active_box['top']:
                        # Breakout - form new box
                        start_date = df['Date'].iloc[active_box['start_idx']]
                        end_date = df['Date'].iloc[i]

                        # Physical dimensions
                        box_width = (
                            i - active_box['start_idx'] + 1) * cm_per_candle
                        box_height = (
                            active_box['top'] - active_box['bottom']) * cm_per_price_unit

                        logging.debug(
                            f"Box dimensions - Width: {box_width} cm, Height: {box_height} cm")

                        # Validate height-width ratio
                        if (box_height / box_width) > 1.9:
                            logging.debug(
                                f"Box failed height-width validation: Width {box_width}, Height {box_height}")
                            active_box = None
                            continue

                        # Validate 80% candles within box
                        box_candles = df.iloc[active_box['start_idx']:i + 1]
                        inside_candles = box_candles[
                            (box_candles['High'] <= active_box['top']) &
                            (box_candles['Low'] >= active_box['bottom'])
                        ]
                        if len(inside_candles) / len(box_candles) < 0.8:
                            logging.debug(
                                f"Box failed inside-candles validation: {len(inside_candles)}/{len(box_candles)}")
                            active_box = None
                            continue

                        boxes.append({
                            'x0': start_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'x1': end_date.strftime('%Y-%m-%d %H:%M:%S'),
                            'y0': float(active_box['bottom']),
                            'y1': float(active_box['top']),
                            'pattern_type': 'darvas_box'
                        })
                        active_box = {
                            'start_idx': i - nbc + 1,
                            'top': current_high,
                            'bottom': current_low
                        }
                    elif current_close < active_box['bottom']:
                        if i - active_box['start_idx'] >= nbc:
                            start_date = df['Date'].iloc[active_box['start_idx']]
                            end_date = df['Date'].iloc[i]

                            # Physical dimensions
                            box_width = (
                                i - active_box['start_idx'] + 1) * cm_per_candle
                            box_height = (
                                active_box['top'] - active_box['bottom']) * cm_per_price_unit

                            logging.debug(
                                f"Box dimensions - Width: {box_width} cm, Height: {box_height} cm")

                            # Validate height-width ratio
                            if box_height / box_width > 0.3:
                                logging.debug(
                                    f"Box failed height-width validation: Width {box_width}, Height {box_height}")
                                active_box = None
                                continue

                            # Validate 80% candles within box
                            box_candles = df.iloc[active_box['start_idx']:i + 1]
                            inside_candles = box_candles[
                                (box_candles['High'] <= active_box['top']) &
                                (box_candles['Low'] >= active_box['bottom'])
                            ]
                            if len(inside_candles) / len(box_candles) < 0.8:
                                logging.debug(
                                    f"Box failed inside-candles validation: {len(inside_candles)}/{len(box_candles)}")
                                active_box = None
                                continue

                            boxes.append({
                                'x0': start_date.strftime('%Y-%m-%d %H:%M:%S'),
                                'x1': end_date.strftime('%Y-%m-%d %H:%M:%S'),
                                'y0': float(active_box['bottom']),
                                'y1': float(active_box['top']),
                                'pattern_type': 'darvas_box'
                            })
                        active_box = None

        return boxes

    if not df.empty:
        boxes = find_darvas_boxes(df)
        return jsonify(boxes)
    else:
        return jsonify([])
