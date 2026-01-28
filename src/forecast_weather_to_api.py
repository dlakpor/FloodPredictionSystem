import os
import requests
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = 35.1856   # Cyprus
LON = 33.3823

API_URL = "https://api.openweathermap.org/data/2.5/forecast"

def fetch_forecast():
    params = {
        "lat": LAT,
        "lon": LON,
        "appid": API_KEY,
        "units": "metric"
    }
    r = requests.get(API_URL, params=params)
    r.raise_for_status()
    return r.json()

def build_features(data):
    # Next 24 hours (8 intervals of 3h)
    next_24h = data["list"][:8]

    rain = []
    temps = []
    pressure = []
    humidity = []
    clouds = []
    wind = []

    for item in next_24h:
        rain.append(item.get("rain", {}).get("3h", 0.0))
        temps.append(item["main"]["temp"])
        pressure.append(item["main"]["pressure"])
        humidity.append(item["main"]["humidity"])
        clouds.append(item["clouds"]["all"])
        wind.append(item["wind"]["speed"])

    # Build 10-feature vector
    features = [
        rain[0], rain[1], rain[2],        # tp_lag1-3
        sum(rain[:3]),                     # tp_3d_sum
        sum(rain),                         # tp_7d_sum proxy
        np.mean(temps),                    # t2m_7d_mean
        np.mean(wind),
        np.mean(pressure),
        np.mean(humidity),
        np.mean(clouds)
    ]

    return features

def send_to_api(features):
    payload = {"features": features}
    r = requests.post("http://127.0.0.1:8000/predict", json=payload)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    forecast = fetch_forecast()
    features = build_features(forecast)
    print("Forecast-based features:", features)

    result = send_to_api(features)
    print("\nFlood Forecast (Next 24h):")
    print(result)
