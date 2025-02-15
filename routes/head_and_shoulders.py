import logging
from flask import Blueprint, request, jsonify
import pandas as pd
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data
import math

bp = Blueprint('head_and_shoulders', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@bp.route('/head-and-shoulders', methods=['GET'])
def get_head_and_shoulders():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')

    # logger.debug(f"Fetching data for symbol: {symbol}, interval: {interval}")

    data1 = fetch_data_from_db(symbol, interval)
    if compare_db_current_date(symbol):
        data2 = fetch_currentday_data(symbol, interval)
    else:
        data2 = []
    data = data1 + data2

    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    # logger.debug(f"Data fetched: {df.head()}")

    def detect_head_and_shoulders(df):
        # logger.debug("Starting head-and-shoulders detection...")

        sup = df[df['Low'] == df['Low'].rolling(12, center=True).min()]['Low']
        res = df[df['High'] == df['High'].rolling(
            12, center=True).max()]['High']
        sup = sup.to_frame()
        sup.columns = ['price']
        sup['val'] = 1
        res = res.to_frame()
        res.columns = ['price']
        res['val'] = 2
        lev = sup.combine_first(res)

        # logger.debug(f"Support and resistance levels detected:\n{lev}")

        def hsf(hs):
            ls, lb, head, rb, rs = hs
            # logger.debug(f"Checking pattern with indices - LS: {ls}, LB: {lb}, Head: {head}, RB: {rb}, RS: {rs}")

            left_shoulder_height = df['High'][ls]
            right_shoulder_height = df['High'][rs]
            head_height = df['High'][head]
            # logger.debug(f"Left Shoulder Height: {left_shoulder_height}, Right Shoulder Height: {right_shoulder_height}, Head Height: {head_height}")

            # Calculate angle between left and right shoulder tops
            x_diff = rs - ls
            y_diff = right_shoulder_height - left_shoulder_height
            angle_radians = math.atan2(y_diff, x_diff)
            angle_degrees = math.degrees(angle_radians)
            logger.debug(f"Angle between shoulders: {angle_degrees}°")

            # Validate angle
            if angle_degrees < -35 or angle_degrees > 35:
                logger.debug(
                    "Angle between shoulders is not within the acceptable range (-35° to +35°). Skipping pattern.")
                return None

            # Validate height difference between shoulders
            height_diff_percentage = abs(left_shoulder_height - right_shoulder_height) / min(
                left_shoulder_height, right_shoulder_height) * 100
            # logger.debug(f"Height Difference Percentage between shoulders: {height_diff_percentage}%")

            if height_diff_percentage > 10:
                # logger.debug("Shoulders are not similar enough. Skipping pattern.")
                return None

            if head_height <= max(left_shoulder_height, right_shoulder_height) * 1:
                # logger.debug("Head is not significantly higher than shoulders. Skipping pattern.")
                return None

            if df['High'][head] <= min(df['High'][ls], df['High'][rs]):
                # logger.debug("Head is not higher than both shoulders. Skipping pattern.")
                return None
            boundary_diff = abs(df['Low'][lb] - df['Low'][rb])
            ratio = max(df['Low'][lb], df['Low'][rb]) / \
                min(df['Low'][lb], df['Low'][rb])

            abs_threshold = 10
            ratio_threshold = 1.1

            if boundary_diff > abs_threshold and ratio > ratio_threshold:
                # logger.debug("Left and right boundaries are not symmetric enough. Skipping pattern.")
                return None

            logger.debug("The boundaries are symmetric.")

            rh = rs - head
            lh = head - ls

            if rh >= 3 * lh or lh >= 3 * rh:
                # logger.debug("Pattern is too asymmetric. Skipping pattern.")
                return None

            neck_run = rb - lb
            neck_rise = df['Low'][rb] - df['Low'][lb]
            neck_slope = neck_rise / (neck_run if neck_run != 0 else 1)

            # logger.debug(f"Neckline slope: {neck_slope}")

            pat_start = ls - int(0.5 * neck_run) if ls - \
                int(0.5 * neck_run) >= 0 else 0
            pat_end = rs + int(0.5 * neck_run) if rs + \
                int(0.5 * neck_run) < len(df) else len(df) - 1

            hs.insert(0, pat_start)
            hs.append(pat_end)
            # logger.debug(f"Valid pattern found: {hs}")
            return hs

        head_and_shoulders = []
        c = []
        p = lev.index[0]
        for i in lev.index:
            if not c:
                if lev['val'][i] == 2:
                    c.append(i)
                else:
                    p = i
                    continue
            else:
                if lev['val'][i] != lev['val'][p] and i - p > 2:
                    c.append(i)
                elif lev['val'][i] == 1:
                    c = []
                else:
                    c = [i]

            if len(c) == 5:
                hs = hsf(c)
                if hs:
                    head_and_shoulders.append(hs)
                    c = []
                else:
                    c = c[2:]
            p = i

        # logger.debug(f"Total patterns detected: {len(head_and_shoulders)}")
        return head_and_shoulders

    head_and_shoulders = detect_head_and_shoulders(df)

    coordinates = []
    for hs in head_and_shoulders:
        points = []
        for i in range(len(hs)):
            points.append({
                'x': df['Date'][hs[i]].strftime('%Y-%m-%d %H:%M:%S'),
                'y': df['Low'][hs[i]] if i % 2 == 0 else df['High'][hs[i]]
            })
        coordinates.append(points)

    # logger.debug(f"Final coordinates: {coordinates}")

    return jsonify(coordinates)
