from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

bp = Blueprint('support_resistance', __name__)


def calculate_sr_lines(df, prd, nsr):
    sup = df[df.low == df.low.rolling(prd, center=True).min()].low
    res = df[df.high == df.high.rolling(prd, center=True).max()].high
    lev = sup.tolist() + res.tolist()
    lev.sort()
    kmeans = KMeans(n_clusters=int(nsr), random_state=42).fit(
        np.array(lev).reshape(-1, 1))
    lset = []
    for cluster_center in kmeans.cluster_centers_:
        closest_index = np.argmin(np.abs(lev - cluster_center))
        lset.append(lev[closest_index])
    return lset


@bp.route('/support-resistance')
def get_support_resistance():
    symbol = request.args.get('symbol', 'NSE:NIFTY50-INDEX')
    interval = request.args.get('interval', '5')
    nsr = int(request.args.get('nsr', 8))
    group_size = int(request.args.get('group_size', 5000))
    start_date = request.args.get('start_date')

    data1 = fetch_data_from_db(symbol, interval)
    if compare_db_current_date(symbol):
        data2 = fetch_currentday_data(symbol, interval)
    else:
        data2 = []
    data = data1 + data2

    df = pd.DataFrame(data)
    if df.empty:
        return jsonify([])

    df = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close'])

    df.columns = ['date', 'open', 'high', 'low', 'close']
    df['date'] = pd.to_datetime(df['date'])

    # Filter the DataFrame to start from the user-selected date
    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df['date'] >= start_date]

    if df.empty:
        return jsonify({"error": "No data available for the selected date."}), 400

    prd = 30
    sr_lines_groups = []

    offset = max(len(df) - group_size, 0)
    while offset >= 0:
        group_df = df.iloc[offset:offset + group_size]
        sr_lines = calculate_sr_lines(group_df, prd, nsr)
        sr_lines_groups.append({
            "start_date": group_df['date'].iloc[0].strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": group_df['date'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S'),
            "sr_lines": sr_lines
        })
        offset -= group_size

        if offset < 0:
            break

    return jsonify(sr_lines_groups)


# @bp.route('/support-resistance')

# def get_support_resistance():
#     symbol = request.args.get('symbol', 'NSE:NIFTY50-INDEX')
#     interval = request.args.get('interval', '5')
#     nsr = int(request.args.get('nsr', 8))
#     group_size = int(request.args.get('group_size', 5000))
#     # Get the start date from the request
#     start_date = request.args.get('start_date')

#     data1 = fetch_data_from_db(symbol, interval)
#     if compare_db_current_date(symbol):
#         data2 = fetch_currentday_data(symbol, interval)
#     else:
#         data2 = []
#     data = data1 + data2

#     df = pd.DataFrame(data)

#     if df.empty:
#         return jsonify([])

#     df = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close'])
#     df.columns = ['date', 'open', 'high', 'low', 'close']
#     df['date'] = pd.to_datetime(df['date'])

#     # Filter the DataFrame to start from the user-selected date
#     if start_date:
#         start_date = pd.to_datetime(start_date)
#         df = df[df['date'] >= start_date]

#     # Check if the dataframe has any data after filtering
#     if df.empty:
#         return jsonify({"error": "No data available for the selected date."}), 400

#     prd = 30
#     sr_lines_groups = []

#     # Adjust loop to handle smaller dataframes
#     offset = max(len(df) - group_size, 0)
#     while offset >= 0:
#         group_df = df.iloc[offset:offset+group_size]
#         sr_lines = calculate_sr_lines(group_df, prd, nsr)
#         sr_lines_groups.append({
#             "start_date": group_df['date'].iloc[0].strftime('%Y-%m-%d %H:%M:%S'),
#             "end_date": group_df['date'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S'),
#             "sr_lines": sr_lines
#         })
#         offset -= group_size

#         # Break if the next offset would result in an empty dataframe
#         if offset < 0:
#             break

#     return jsonify(sr_lines_groups)
