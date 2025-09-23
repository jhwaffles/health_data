import pandas as pd
import os

"""
Health Data Integration Pipeline

This script combines from preprocessed bearable and oura data and merges on date.

Input Files:
    - cleaned_bearable.csv
    - oura_combined.csv
    - oura_data_time_series.csv

Output File:
    - result.csv
"""

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
data_dir = os.path.abspath(os.path.join(parent_dir, 'data'))
file_path_bearable = os.path.join(data_dir, 'cleaned_bearable.csv')
file_path_oura = os.path.join(data_dir, 'oura_combined.csv')
file_path_oura_time_series = os.path.join(data_dir, 'oura_data_time_series.csv')

df_bearable=pd.read_csv(file_path_bearable)
df_oura=pd.read_csv(file_path_oura)
df_time_series=pd.read_csv(file_path_oura_time_series)

result = pd.merge(df_bearable, df_oura, left_on='date', right_on='day_minus_one', how='left')

result.head()
columns_to_remove=['Unnamed: 0_x','Unnamed: 0_y']

result=result.drop(columns=columns_to_remove)
result = result[result.isna().sum(axis=1) < 10]

print("Merged Data to results.csv")
output_path_combined = os.path.join(data_dir, 'result.csv')
result.to_csv(output_path_combined)