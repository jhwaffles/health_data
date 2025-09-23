import numpy as numpy
import pandas as pd
import json
import os
import regex as re

"""
Process Oura Ring sleep data from JSON to CSV format. This step can take a few minutes to run, depending on number of records.

Inputs:
    - daily_sleep_data.json: Daily sleep scores and contributor metrics
    - sleep_data.json: Detailed sleep measurements including time series data

Outputs:
    - oura_combined.csv: Combined daily sleep metrics and scores.
    - oura_data_time_series.csv: Time series data for HRV, heart rate, movement, and sleep phases

"""

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
data_dir = os.path.join(parent_dir, 'data')
file_path = os.path.join(data_dir, 'sleep_data.json')
file_path_daily_sleep = os.path.join(data_dir, 'daily_sleep_data.json')

print('file path {}'.format(file_path))

with open(file_path, 'r') as file:
    data_dict = json.load(file) 

data = data_dict["data"]

single_points = []
time_series = []

time_series_fields = ['hrv', 'heart_rate', 'movement_30_sec', 'sleep_phase_5_min']

print('generating files...')

###Navigates JSON structure to extract time series data and single point data
for record in data:
    readiness=record.pop('readiness', {})
    readiness_contributors = readiness.pop('contributors', {})
    readiness_combined = {f"readiness_{k}": v for k, v in {**readiness_contributors, **readiness}.items()}
    record.update(readiness_combined)
    single_point = {k: v for k, v in record.items() if k not in time_series_fields}
    single_points.append(single_point)
    
    for field in time_series_fields:
        if field in record:
            content = record[field]
        # Handle different structures of time-series data
            if isinstance(content, dict) and "items" in content:
                interval = content.get("interval", 1)  # Default interval to 1 second if not provided
                start_timestamp = pd.to_datetime(content["timestamp"])
                for idx, value in enumerate(content["items"]):
                    if value is not None:  # Exclude nulls
                        timestamp = start_timestamp + pd.to_timedelta(idx * interval, unit="s")
                        time_series.append({
                            "day": record["day"],
                            "field": field,
                            "timestamp": timestamp,
                            "value": value
                        })
            elif isinstance(content, str):  # For movement_30_sec and sleep_phase_5_min
                for idx, value in enumerate(content):
                    timestamp = pd.to_datetime(record["bedtime_start"]) + pd.to_timedelta(idx * 30, unit="s")
                    time_series.append({
                        "day": record["day"],
                        "field": field,
                        "timestamp": timestamp,
                        "value": value
                    })

# Create DataFrames
oura_data_single_points = pd.DataFrame(single_points)
oura_data_single_points.rename(columns={'latency': 'latency_duration'}, inplace=True)

oura_data_time_series = pd.DataFrame(time_series)

with open(file_path_daily_sleep, 'r') as file:
    daily_sleep_data_dict = json.load(file)

daily_sleep_data = daily_sleep_data_dict["data"]

# Combine score info from daily sleep records with sleep_data.
daily_sleep_records = []
for record in daily_sleep_data:
    contributors = record.pop("contributors")
    record.update(contributors)
    daily_sleep_records.append(record)

daily_sleep_df = pd.DataFrame(daily_sleep_records)
oura_combined_df = pd.merge(daily_sleep_df, oura_data_single_points, on='day', how='left')

#only count long sleep, since naps and short naps go to a daily score and we want one record per day 
oura_combined_df = oura_combined_df[oura_combined_df['type']=='long_sleep']
oura_combined_df['day'] = pd.to_datetime(oura_combined_df['day'])
oura_combined_df['timestamp'] = pd.to_datetime(oura_combined_df['timestamp'], errors='coerce')  # if it exists

#sleep data is scored the day after the sleep event. Handy to have this column for analysis.
oura_combined_df['day_minus_one']=oura_combined_df['day']- pd.Timedelta(days=1)

columns_to_remove=['id_x','day','timestamp','id_y','sleep_score_delta','sleep_algorithm_version','type']
oura_combined_df=oura_combined_df.drop(columns=columns_to_remove)

output_path_combined = os.path.join(data_dir, 'oura_combined.csv')
output_path_timeseries = os.path.join(data_dir, 'oura_data_time_series.csv')
oura_combined_df.to_csv(output_path_combined)
oura_data_time_series.to_csv(output_path_timeseries)