from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from math import atan2, degrees
from datetime import timedelta, datetime
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data

bp = Blueprint('zonespattern', __name__)

@bp.route('/zonespattern', methods=['GET'])
def get_zones():
    # Step 1: Fetch parameters from the request
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')
    
    # Validate interval
    interval = int(interval)
    print(f"Debug: Received request for symbol {symbol} with interval {interval}")

    # Step 2: Fetch data from the database
    data1 = fetch_data_from_db(symbol, interval)
    data2 = fetch_currentday_data(symbol, interval) if compare_db_current_date(symbol) else []
    data = data1 + data2

    # Check if data is empty
    if not data:
        print("Debug: No data found for the given parameters.")
        return jsonify({'error': 'No data found for the given parameters'}), 404

    # Step 3: Process the returned data
    df = pd.DataFrame(data)
    print("Debug: Data fetched and converted to DataFrame.")

    # Capitalize the first letter of column names
    df = df.rename(columns={ 
        'open': 'Open', 
        'high': 'High', 
        'low': 'Low', 
        'close': 'Close', 
        'volume': 'Volume', 
        'date': 'Date' 
    })

    df['Date'] = pd.to_datetime(df['Date'])
    
    # Filter for last 10 trading days
    unique_dates = sorted(df['Date'].dt.date.unique())
    last_10_dates = unique_dates[-10:]
    df = df[df['Date'].dt.date.isin(last_10_dates)]
    
    df.set_index('Date', inplace=True)

    # Define time zones
    def define_zones():
        zones = {
            'zone1': ('09:15', '10:30'),
            'zone2': ('10:30', '11:30'),
            'zone3': ('11:30', '13:30'),
            'zone4': ('13:30', '14:30'),
            'zone5': ('14:30', '15:30'),
        }
        print("Debug: Defined zones:", zones)
        return zones

    # Assign candles to their respective zones based on time and day
    def assign_zones(df, zones):
        df['Zone'] = None
        df['Day'] = df.index.date  # Separate days for individual processing

        for day in df['Day'].unique():
            daily_df = df[df['Day'] == day]
            for zone_name, (start, end) in zones.items():
                daily_df.loc[
                    (daily_df.index.time >= pd.Timestamp(start).time()) & 
                    (daily_df.index.time < pd.Timestamp(end).time()), 
                    'Zone'
                ] = zone_name
            df.update(daily_df)  # Update main DataFrame with daily zones

        print("Debug: Assigned zones to DataFrame based on each trading day.")
        return df

    # Identify Uptrends and Downtrends
    def identify_trends(df):
        df['Trend'] = np.where(df['Close'] > df['Open'], 'Uptrend', 'Downtrend')
        print("Debug: Identified trends (Uptrend/Downtrend) in DataFrame.")
        return df

    # Count Uptrends and Downtrends per Zone and per Day
    def count_trends_per_zone(df):
        trend_counts = df.groupby(['Day', 'Zone', 'Trend']).size().unstack(fill_value=0).reset_index()
        print("Debug: Counted trends per zone and day:", trend_counts)
        return trend_counts

    # Categorize zones based on the number of trends
    def categorize_zone(uptrends, downtrends):
        total_trends = uptrends + downtrends
        if total_trends > 15:
            return 5  # Highly volatile
        elif total_trends > 10:
            return 4  # Good moves
        elif total_trends > 5:
            return 3  # Average moves
        elif total_trends > 2:
            return 2  # Small moves
        else:
            return 1  # Very small moves

    # Step 4: Process data
    zones = define_zones()
    df = assign_zones(df, zones)
    df = identify_trends(df)
    trend_counts = count_trends_per_zone(df)

    # Step 5: Prepare zone data with coordinates for last 10 days
    coordinates = []
    for day in df['Day'].unique():
        daily_df = df[df['Day'] == day]
        print(f"Debug: Processing data for {day}")
        
        # Sort zones to ensure they're processed in chronological order
        for zone in sorted(zones.keys()):
            zone_data = daily_df[daily_df['Zone'] == zone]
            if zone_data.empty:
                print(f"Debug: No data for {day} in zone {zone}. Skipping.")
                continue

            low = zone_data['Low'].min()
            high = zone_data['High'].max()
            start_time = zone_data.index[0]
            end_time = zone_data.index[-1]

            # Get the next zone's start time for proper boundary
            zone_num = int(zone[-1])
            next_zone = f'zone{zone_num + 1}' if zone_num < 5 else None
            next_zone_start = None
            if next_zone:
                next_zone_data = daily_df[daily_df['Zone'] == next_zone]
                if not next_zone_data.empty:
                    next_zone_start = next_zone_data.index[0]

            # Use the actual end time of the current zone
            if next_zone_start:
                box_end_time = min(next_zone_start, end_time)
            else:
                box_end_time = end_time

            # Handle cases where uptrends or downtrends are missing in some zones
            uptrends = trend_counts.loc[(trend_counts['Day'] == day) & (trend_counts['Zone'] == zone), 'Uptrend'].values[0] if 'Uptrend' in trend_counts.columns else 0
            downtrends = trend_counts.loc[(trend_counts['Day'] == day) & (trend_counts['Zone'] == zone), 'Downtrend'].values[0] if 'Downtrend' in trend_counts.columns else 0
            trend_category = categorize_zone(uptrends, downtrends)

            # Add lines in the correct order to form a complete box
            # Left vertical line
            coordinates.append({
                'day': day.strftime('%Y-%m-%d'),
                'x0': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'x1': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'y0': float(low),
                'y1': float(high),
                'zone': zone,
                'category': trend_category,
                'uptrends': int(uptrends),
                'downtrends': int(downtrends),
                'type': 'vertical_line'
            })

            # Top horizontal line
            coordinates.append({
                'day': day.strftime('%Y-%m-%d'),
                'x0': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'x1': box_end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'y0': float(high),
                'y1': float(high),
                'zone': zone,
                'category': trend_category,
                'uptrends': int(uptrends),
                'downtrends': int(downtrends),
                'type': 'horizontal_line'
            })

            # Right vertical line - using box_end_time for a straight line
            coordinates.append({
                'day': day.strftime('%Y-%m-%d'),
                'x0': box_end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'x1': box_end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'y0': float(high),
                'y1': float(low),
                'zone': zone,
                'category': trend_category,
                'uptrends': int(uptrends),
                'downtrends': int(downtrends),
                'type': 'vertical_line'
            })

            # Bottom horizontal line
            coordinates.append({
                'day': day.strftime('%Y-%m-%d'),
                'x0': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'x1': box_end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'y0': float(low),
                'y1': float(low),
                'zone': zone,
                'category': trend_category,
                'uptrends': int(uptrends),
                'downtrends': int(downtrends),
                'type': 'horizontal_line'
            })

    print("Debug: Final coordinates prepared:", coordinates)
    return jsonify(coordinates)