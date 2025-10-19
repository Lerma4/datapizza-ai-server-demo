from datapizza.tools import tool
import openmeteo_requests

import json
import pandas as pd
import requests_cache
from retry_requests import retry

@tool
def get_weather(latitude: str, longitude: str, when: str) -> str:
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "precipitation",
            "precipitation_probability",
            "visibility",
            "wind_speed_10m",
            "wind_speed_80m",
        ],
        "timezone": "auto",
        "start_date": when,
        "end_date": when,
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(2).ValuesAsNumpy()
    hourly_visibility = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(4).ValuesAsNumpy()
    hourly_wind_speed_80m = hourly.Variables(5).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left",
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["precipitation_probability"] = hourly_precipitation_probability
    hourly_data["visibility"] = hourly_visibility
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["wind_speed_80m"] = hourly_wind_speed_80m

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    # Compute local 12:00 target and map to UTC timestamps in the dataframe
    utc_offset_seconds = response.UtcOffsetSeconds()
    target_utc = pd.Timestamp(f"{when} 12:00:00", tz="UTC") - pd.Timedelta(seconds=utc_offset_seconds)

    if target_utc in set(hourly_dataframe["date"]):
        row = hourly_dataframe.loc[hourly_dataframe["date"] == target_utc].iloc[0]
    else:
        # Fallback to closest hour if the exact 12:00 entry is not present
        diffs = (hourly_dataframe["date"] - target_utc).abs()
        row = hourly_dataframe.loc[diffs.idxmin()]

    timezone = response.Timezone()
    timezone_abbr = response.TimezoneAbbreviation()
    if isinstance(timezone, (bytes, bytearray)):
        timezone = timezone.decode("utf-8", errors="replace")
    if isinstance(timezone_abbr, (bytes, bytearray)):
        timezone_abbr = timezone_abbr.decode("utf-8", errors="replace")

    result = {
        "requested_local_time": f"{when} 12:00:00",
        "matched_utc_time": row["date"].isoformat(),
        "latitude": float(response.Latitude()),
        "longitude": float(response.Longitude()),
        "timezone": timezone,
        "timezone_abbr": timezone_abbr,
        "temperature_2m": float(row["temperature_2m"]),
        "precipitation": float(row["precipitation"]),
        "precipitation_probability": float(row["precipitation_probability"]),
        "visibility": float(row["visibility"]),
        "wind_speed_10m": float(row["wind_speed_10m"]),
        "wind_speed_80m": float(row["wind_speed_80m"]),
    }

    return json.dumps(result)