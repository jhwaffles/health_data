import numpy as numpy
import pandas as pd
import os
import regex as re
from bearable_rules import format_rules

"""
Bearable Data Processing Pipeline

This script processes exported Bearable health tracking data through a series of transformations.

Input File:
    - bearable-export-DD-MM-YYYY.csv: Raw export from Bearable app containing:
        * Daily health measurements
        * Mood and energy ratings
        * Symptoms and factors
        * Sleep data

Output File:
    - cleaned_bearable.csv: Processed data with:
        * Standardized datetime format
        * Pivoted categories as columns
        * Added time-based features (day of week, weekend indicator)
        * Aggregated daily measurements

Pipeline Steps:
    1. convert_to_datetime: Standardizes date format and removes ordinal suffixes
    2. clean_sleep: Filters out duplicate sleep entries and synced data
    3. process_data: Applies category-specific processing rules:
        - map: Converts categorical levels to numeric scores
        - symptom: Aggregates daily symptom occurrences
        - energy_mood: Averages multiple daily ratings
        - count_retain: Counts daily occurrences
    4. pivot_data_multiindex: Reshapes data to wide format with categories as columns
    5. add_day_of_week: Adds time-based features

Dependencies:
    - bearable_rules.py: Contains format_rules dictionary defining processing rules
"""

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
data_dir = os.path.join(parent_dir, 'data')
data_dir = os.path.abspath(os.path.join(parent_dir, 'data'))
file_path = os.path.join(data_dir, 'bearable-export-25-01-2025.csv')

print('file path {}'.format(file_path))

df=pd.read_csv(file_path)

#remove rows that have category 'Health Measurement'
df = df[df['category'] != 'Health measurements']

#PIPE functions
def convert_to_datetime(df, column_name, date_format=None):
    """
    Converts a column of dates in string format to pandas datetime format.
    Removes ordinal suffixes (e.g., '1st', '2nd') before conversion.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame.
        column_name (str): The name of the column containing dates.
        date_format (str): Optional date format for parsing (e.g., '%d %b %Y').

    Returns:
        pd.DataFrame: DataFrame with the converted datetime column.
    """
    try:
        #Remove ordinal suffixes
        df[column_name] = df[column_name].str.replace(r'(\d+)(st|nd|rd|th)', r'\1', regex=True)

        #Convert to datetime
        df[column_name] = pd.to_datetime(df[column_name], format=date_format, errors='coerce')

        #Log invalid rows
        invalid_dates = df[df[column_name].isna()]
        if not invalid_dates.empty:
            print("\n⚠️ WARNING: The following rows could not be converted to datetime:")
            print(invalid_dates)
    except Exception as e:
        print(f"\n❌ ERROR: Failed to convert column '{column_name}' to datetime.")
        print(e)
    
    return df

#For sleep, ditch rows if it has a time entry in 'Rating'.
def clean_sleep(df):
    """
    Filters out unwanted sleep records from the DataFrame.
    
    Parameters:
        df (pd.DataFrame): Input DataFrame containing sleep records
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with filtered sleep records
    """
    df=df[~((df['category']=='Sleep') & (df['rating/amount'].notna()))]
    df=df[~((df['category']=='Sleep') & (df['notes']=='(Synced)'))]
    return df

def remove_emojis(text):
    """
    Removes emoji characters from text using Unicode ranges.
    
    Parameters:
        text (str): Input text containing potential emoji characters
        
    Returns:
        str: Cleaned text with emojis removed and extra whitespace stripped
    """
    emoji_pattern = re.compile(
        "["  # Emoji ranges
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport & map symbols
        "\U0001F700-\U0001F77F"  # Alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric shapes extended
        "\U0001F800-\U0001F8FF"  # Supplemental arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # Chess symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and pictographs extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text).strip()  # Remove emojis and strip extra spaces

# Function to look into details, split by delimitter |, make new rows
def process_data(df,format_rules):
    """
    Processes raw data according to category-specific rules defined in format_rules.
    
    Handles different processing modes:
    - map: Maps categorical values to numeric scores
    - symptom: Aggregates symptom occurrences
    - energy_mood: Calculates average daily mood/energy scores
    - count_retain: Counts daily occurrences (e.g., bowel movements)
    - remove: Removes specified categories
    
    Parameters:
        df (pd.DataFrame): Input DataFrame with raw data
        format_rules (dict): Dictionary containing processing rules for each category
        
    Returns:
        pd.DataFrame: Processed DataFrame with standardized format
    """

    df = df.copy()
    
    # Iterate through each category in the rules
    for category, settings in format_rules.items():
        mode = settings.get('mode', 'binary')  # Default mode is 'binary'
        factors = settings.get('factors', {})

        # Filter rows for the current category
        category_mask = df['category'] == category
        category_df = df[category_mask].copy()  # Work on a copy of the filtered rows
        
        if mode == 'map':
            # Step 1: Remove emojis from the 'detail' column
            category_df['detail'] = category_df['detail'].astype(str).apply(remove_emojis)
            new_rows = []
            # Step 2: Split 'detail' by '|' and create new rows
            for _, row in category_df.iterrows():
                details = row['detail'].split(' | ')
                for factor in details:
                    clean_factor = factor.strip()
                    new_row = row.copy()
                    new_row['detail'] = clean_factor

                    # Step 3: Map 'rating/amount' based on the factors dictionary
                    value = row['rating/amount'] if pd.notna(row['rating/amount']) else 1
                    if '-' in clean_factor:
                        name, level = map(str.strip, clean_factor.split('-', 1))
                        if name in factors and level in factors[name]:
                            value = factors[name][level]
                        new_row['detail'] = name  # Standardize the detail name
                    new_row['rating/amount'] = value
                    new_rows.append(new_row)

            # After processing, remove the original rows for this category
            df = df[~category_mask]
            if new_rows:  # Ensure there are new rows to add
                df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

        elif mode == 'symptom':
            # Aggregate rows for symptoms
            category_df = df[category_mask]
            grouped_symptoms = (
                category_df
                .groupby(['date', 'category', 'detail'], as_index=False)
                .first()  # Keep the first occurrence
            )
            # Process the 'detail' column to remove text in parentheses
            grouped_symptoms['detail'] = grouped_symptoms['detail'].str.replace(r"\s*\(.*\)", "", regex=True)
            
            # Replace original rows with aggregated rows
            df = pd.concat([df[~category_mask], grouped_symptoms], ignore_index=True)

        elif mode == 'energy_mood':
            #Set 'detail' to the value of 'category' for the current category
            df.loc[category_mask, 'detail'] = df.loc[category_mask, 'category']

            #Convert 'rating/amount' to numeric (to handle potential non-numeric values)
            df.loc[category_mask, 'rating/amount'] = pd.to_numeric(
                df.loc[category_mask, 'rating/amount'], errors='coerce'
            )

            #Aggregate by 'date' and calculate the mean for 'rating/amount'
            energy_mood_agg = (
                df[category_mask]
                .groupby(['date', 'category', 'detail'], as_index=False)
                .agg({'rating/amount': 'mean'})  # Calculate average rating
            )

            #Replace the original rows for this category with the aggregated rows
            df = pd.concat([df[~category_mask], energy_mood_agg], ignore_index=True)


        elif mode == 'count_retain':
            category_df = df[category_mask]
            count_agg = (
                category_df
                .groupby(['date'], as_index=False)
                .size()
                .rename(columns={'size': 'rating/amount'})
            )

            count_agg['category'] = 'Bowel Movements'
            count_agg['detail'] = 'Number_Bowel_Movements'
            # Replace original rows with aggregated rows
            df = pd.concat([df[~category_mask], count_agg], ignore_index=True)

        elif mode == 'remove':
            # Remove rows for this category
            df = df[~category_mask]

        else:
            # Preserve rows as-is for other modes
            pass

    return df

def pivot_data_multiindex(df):
    """
    Creates a pivot table from processed data with dates as index and categories as columns.
    
    Handles duplicate detection and aggregation of multiple daily entries.
    
    Parameters:
        df (pd.DataFrame): Input DataFrame with processed data
        
    Returns:
        pd.DataFrame: Pivoted DataFrame with date index and category columns
    """
    duplicate_rows = df[df.duplicated(subset=['category','date', 'detail','rating/amount'], keep=False)]
    if not duplicate_rows.empty:
        print("\n⚠️ WARNING: Duplicate rows detected before pivoting:")
        print(duplicate_rows)

    # Create the pivot table
    pivoted_df = df.pivot_table(
        index='date',                       # Group by date
        columns=['category', 'detail'],     # Multi-index columns with category and detail
        values='rating/amount',             # Values from 'rating/amount'
        aggfunc='sum',                      # Aggregate duplicates by sum
        fill_value=0                        # Fill missing values with 0
    )

    # Flatten the multi-index columns
    pivoted_df.columns = ['_'.join(col).strip() for col in pivoted_df.columns.values]
    
    # Reset index to include 'date' as a column
    pivoted_df = pivoted_df.reset_index()
    
    return pivoted_df

def add_day_of_week(df):
    """
    Adds day of week and weekend indicator columns to the DataFrame.
    
    Adds columns:
    - day_of_week: 0-6 representing Monday-Sunday
    - is_weekend: Binary indicator (1 for Saturday/Sunday, 0 otherwise)
    
    Parameters:
        df (pd.DataFrame): Input DataFrame with date column
        
    Returns:
        pd.DataFrame: DataFrame with added time-based columns
    """
    df['day_of_week']=df['date'].dt.weekday
    df['is_weekend'] = pd.to_datetime(df['date']).dt.weekday >= 5
    df['is_weekend'] = df['is_weekend'].astype(int)  # Convert boolean to 0/1
    cols=list(df.columns)
    cols.insert(1,cols.pop(cols.index('day_of_week')))
    cols.insert(2,cols.pop(cols.index('is_weekend')))
    df=df[cols]
    return df

# Process the DataFrame using the defined functions
df=(
    df
    .pipe(lambda x: convert_to_datetime(x, column_name='date'))
    .pipe(clean_sleep)
    .pipe(process_data, format_rules)  # Process rows to split and handle keywords
    .pipe(pivot_data_multiindex)
    .pipe(add_day_of_week)
)

print("processed data:")
print(df.head())
output_path_combined = os.path.join(data_dir, 'cleaned_bearable.csv')
df.to_csv(output_path_combined)