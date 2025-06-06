"""This scripts fetches solar generation forecasts for Great Britain using the Quartz API.

The API requires authentication via a Bearer token and returns forecast data for a specified time
period. The forecast data includes predicted solar generation values at half hourly intervals.

Example:
    - Set access token in the "get_solar_forecast" function at "INSERT ACCESS TOKEN HERE".
    - Set the start_time to when you want to pull forecasts from.
    - Adjust the days parameter in end_time variable. (example is a week)

Notes:
    - Before 2024-06-01 adjustments where made to how pvalues are stored, which this current script
      does not account for.
"""

from datetime import timedelta

import pandas as pd
import requests
from tqdm import tqdm

start_time = pd.to_datetime("2024-06-01")
end_time = start_time + timedelta(days=1)  # Example pull a week of data
output_file_path = "./quartz_production_backtest.csv"


def get_solar_forecast(start_datetime):
    """
    Get solar forecast for GB from Quartz API for a specific start time and creation limit

    Args:
        start_datetime: Start datetime

    Returns:
        pandas.DataFrame: Forecast data with columns:
            - targetTime
            - expectedPowerGenerationMegawatts
            - plevel_10
            - plevel_90
            - creation_time_utc
    """
    end_datetime = start_datetime + timedelta(days=2)
    creation_limit = start_datetime

    # API endpoint and parameters
    url = "https://api.quartz.solar/v0/solar/GB/national/forecast"
    params = {
        "include_metadata": "false",
        "start_datetime_utc": start_datetime,
        "end_datetime_utc": end_datetime,
        "creation_limit_utc": creation_limit,
        "model_name": "blend",
    }

    access_token = "INSERT ACCESS TOKEN HERE"

    # Request headers
    headers = {"accept": "application/json", "Authorization": f"Bearer {access_token}"}

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")

    forecast_data = response.json()

    df = pd.DataFrame(forecast_data)

    # extract plevels into separate columns and drop the plevels dictionary column
    df["plevel_10"] = df["plevels"].apply(lambda x: x["plevel_10"])
    df["plevel_90"] = df["plevels"].apply(lambda x: x["plevel_90"])
    df = df.drop("plevels", axis=1)

    df["targetTime"] = pd.to_datetime(df["targetTime"])
    df["creation_time_utc"] = pd.to_datetime(start_datetime, utc=True)

    return df


timestamps = []
current_time = start_time

while current_time < end_time:
    timestamps.append(current_time)
    current_time += timedelta(minutes=30)

# get forecasts for each timestamp
all_forecasts = []
for ts in tqdm(timestamps, desc="Retrieving forecasts"):
    try:
        forecast_df = get_solar_forecast(ts)
        all_forecasts.append(forecast_df)
    except Exception as e:
        print(f"Failed to get forecast for {ts}: {str(e)}")

# combine all forecasts
if all_forecasts:
    combined_forecasts = pd.concat(all_forecasts, ignore_index=True)
    combined_forecasts.to_csv(output_file_path, index=False)
    print(f"Backtest saved to {output_file_path}")
