import argparse
import json
import os
from datetime import date

import requests

from oura_auth import get_access_token

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(REPO_ROOT, "source_data")
BASE_URL = "https://api.ouraring.com/v2/usercollection/"

DEFAULT_START_DATE = "2024-01-01"


def fetch_oura_data(endpoint, params=None, access_token=None):
    headers = {"Authorization": f"Bearer {access_token or get_access_token()}"}
    query = dict(params or {})
    records = []
    next_token = None

    try:
        while True:
            if next_token:
                query["next_token"] = next_token
            else:
                query.pop("next_token", None)
            response = requests.get(
                BASE_URL + endpoint, headers=headers, params=query, timeout=60
            )
            if response.status_code == 401:
                headers["Authorization"] = f"Bearer {get_access_token(force_login=False)}"
                response = requests.get(
                    BASE_URL + endpoint, headers=headers, params=query, timeout=60
                )
            if not response.ok:
                print(f"HTTP {response.status_code} for {endpoint}: {response.text}")
            response.raise_for_status()
            payload = response.json()
            records.extend(payload.get("data", []))
            next_token = payload.get("next_token")
            if not next_token:
                extra = {k: v for k, v in payload.items() if k != "data"}
                extra["data"] = records
                extra["next_token"] = None
                return extra
    except requests.exceptions.RequestException as e:
        print(f"An error occurred fetching {endpoint}: {e}")
        return None


def fetch_oura_data_single(endpoint, doc_id, params=None, access_token=None):
    headers = {"Authorization": f"Bearer {access_token or get_access_token()}"}
    try:
        passed_url = BASE_URL + endpoint + "/" + doc_id
        print(passed_url)
        response = requests.get(passed_url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def fetch_sleep_data(start_date, end_date, access_token=None):
    return fetch_oura_data(
        "sleep",
        {"start_date": start_date, "end_date": end_date},
        access_token=access_token,
    )


def fetch_daily_sleep_data(start_date, end_date, access_token=None):
    return fetch_oura_data(
        "daily_sleep",
        {"start_date": start_date, "end_date": end_date},
        access_token=access_token,
    )


def fetch_sleep_single_data(doc_id, access_token=None):
    return fetch_oura_data_single("sleep", doc_id, access_token=access_token)


def fetch_sleep_time_data(start_date, end_date, access_token=None):
    return fetch_oura_data(
        "sleep_time",
        {"start_date": start_date, "end_date": end_date},
        access_token=access_token,
    )


def fetch_activity_data(start_date, end_date, access_token=None):
    return fetch_oura_data(
        "daily_activity",
        {"start_date": start_date, "end_date": end_date},
        access_token=access_token,
    )


def fetch_readiness_data(start_date, end_date, access_token=None):
    return fetch_oura_data(
        "daily_readiness",
        {"start_date": start_date, "end_date": end_date},
        access_token=access_token,
    )


def fetch_resilience_data(start_date, end_date, access_token=None):
    return fetch_oura_data(
        "daily_resilience",
        {"start_date": start_date, "end_date": end_date},
        access_token=access_token,
    )


def fetch_spo2_data(start_date, end_date, access_token=None):
    return fetch_oura_data(
        "daily_spo2",
        {"start_date": start_date, "end_date": end_date},
        access_token=access_token,
    )


def fetch_stress_data(start_date, end_date, access_token=None):
    return fetch_oura_data(
        "daily_stress",
        {"start_date": start_date, "end_date": end_date},
        access_token=access_token,
    )


def save_to_json_file(data, filename):
    os.makedirs(SOURCE_DIR, exist_ok=True)
    path = filename if os.path.isabs(filename) else os.path.join(SOURCE_DIR, filename)
    try:
        with open(path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully saved to {path}")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch Oura data into source_data/")
    parser.add_argument("--start", default=DEFAULT_START_DATE, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=date.today().isoformat(), help="End date YYYY-MM-DD")
    parser.add_argument("--login", action="store_true", help="Force a new Oura browser login")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    token = get_access_token(force_login=args.login)
    start_date = args.start
    end_date = args.end

    probe = requests.get(
        BASE_URL + "personal_info",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    print(f"personal_info check: HTTP {probe.status_code} {probe.text[:500]}")
    if probe.status_code == 403:
        print(
            "Oura accepted the token but blocked data. Enable every data scope on "
            "https://cloud.ouraring.com/oauth/applications then rerun with --login, "
            "or renew the Oura membership if it is expired."
        )

    pulls = [
        ("sleep data", fetch_sleep_data, "sleep_data.json"),
        ("daily sleep data", fetch_daily_sleep_data, "daily_sleep_data.json"),
        ("activity data", fetch_activity_data, "activity_data.json"),
        ("readiness data", fetch_readiness_data, "readiness_data.json"),
        ("resilience data", fetch_resilience_data, "resilience_data.json"),
        ("spo2 data", fetch_spo2_data, "spo2_data.json"),
        ("stress data", fetch_stress_data, "stress_data.json"),
    ]

    for label, fetcher, filename in pulls:
        print(f"\nFetching {label}...")
        payload = fetcher(start_date, end_date, access_token=token)
        if payload:
            save_to_json_file(payload, filename)
