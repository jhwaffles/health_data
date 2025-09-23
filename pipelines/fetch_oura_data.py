import requests
import json
import os
current_dir = os.getcwd()
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
data_dir = os.path.abspath(os.path.join(parent_dir, 'source_data'))

token_path = os.path.join(data_dir, 'oura_token.txt')
with open(token_path, 'r') as f:
    ACCESS_TOKEN = f.read().strip()
BASE_URL = "https://api.ouraring.com/v2/usercollection/"

def fetch_oura_data(endpoint, params=None):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        response = requests.get(BASE_URL + endpoint, headers=headers, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
def fetch_oura_data_single(endpoint, doc_id, params=None):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    try:
        passed_url=BASE_URL + endpoint + "/" + doc_id
        print(passed_url)
        response = requests.get(passed_url, headers=headers, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

# Example: Fetch sleep data
def fetch_sleep_data(start_date, end_date):  #Sleep Routes Mulitiple. Detailed Data.
    endpoint = "sleep"
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    return fetch_oura_data(endpoint, params)

def fetch_daily_sleep_data(start_date, end_date):  #Daily Sleep Routes Multiple. Summarized Data.
    endpoint = "daily_sleep"
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    return fetch_oura_data(endpoint, params)

def fetch_sleep_single_data(doc_id):  #sleep routes single
    endpoint = "sleep"
    return fetch_oura_data_single(endpoint, doc_id)

def fetch_sleep_time_data(start_date, end_date):  #Summarized Sleep Time Data.
    endpoint = "sleep_time"
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    return fetch_oura_data(endpoint, params)

# Example: Fetch activity data
def fetch_activity_data(start_date, end_date):  #Daily Activity Routes (Multiiple)
    endpoint = "daily_activity"
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    return fetch_oura_data(endpoint, params)

# Example: Fetch readiness data
def fetch_readiness_data(start_date, end_date): #Daily Readiness Routes (Multiple)
    endpoint = "daily_readiness"
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    return fetch_oura_data(endpoint, params)

def fetch_resilience_data(start_date, end_date): #Daily Resilience Routes (Multiple)
    endpoint = "daily_resilience"
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    return fetch_oura_data(endpoint, params)

def fetch_spo2_data(start_date, end_date): #Daily Spo2 Routes (Multiple)
    endpoint = "daily_spo2"
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    return fetch_oura_data(endpoint, params)

def fetch_stress_data(start_date, end_date): #Daily Stress Routes (Multiple)
    endpoint = "daily_stress"
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    return fetch_oura_data(endpoint, params)

def save_to_json_file(data, filename):
    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")

# Main function to test the API connection
if __name__ == "__main__":
    # Define the date range (format: YYYY-MM-DD)
    start_date = "2024-01-01"
    end_date = "2025-01-25"

    print("Fetching sleep data...")
    sleep_data = fetch_sleep_data(start_date, end_date)
    if sleep_data:
        save_to_json_file(sleep_data, "sleep_data.json")

    print("Fetching daily sleep data...")
    daily_sleep_data = fetch_daily_sleep_data(start_date, end_date)
    if daily_sleep_data:
        save_to_json_file(daily_sleep_data, "daily_sleep_data.json")

    # doc_id="b626985c-1c32-4a42-87bd-37db9bb101e3"
    # print("Fetching single sleep data...")
    # single_sleep_data = fetch_sleep_single_data(doc_id)
    # if single_sleep_data:
    #     save_to_json_file(single_sleep_data, "single_sleep_data.json")

    # print("Fetching sleep time data...")
    # sleep_time_data = fetch_sleep_time_data(start_date, end_date)
    # if sleep_time_data:
    #     save_to_json_file(sleep_time_data, "sleep_time_data.json")

    print("\nFetching activity data...")
    activity_data = fetch_activity_data(start_date, end_date)
    if activity_data:
        save_to_json_file(activity_data, "activity_data.json")

    print("\nFetching readiness data...")
    readiness_data = fetch_readiness_data(start_date, end_date)
    if readiness_data:
        save_to_json_file(readiness_data, "readiness_data.json")

    print("\nFetching resilience data...")
    resilience_data = fetch_resilience_data(start_date, end_date)
    if resilience_data:
        save_to_json_file(resilience_data, "resilience_data.json")

    print("\nFetching spo2 data...")
    spo2_data = fetch_spo2_data(start_date, end_date)
    if spo2_data:
        save_to_json_file(spo2_data, "spo2_data.json")

    print("\nFetching stress data...")
    stress_data = fetch_stress_data(start_date, end_date)
    if stress_data:
        save_to_json_file(stress_data, "stress_data.json")