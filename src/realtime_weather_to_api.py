import os
import requests
import joblib
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Cyprus (example location)
LAT = 35.1856
LON = 33.3823

API_URL = "https://api.openweathermap.org/data/2.5/weather"

def fetch_weather(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()

def build_features(weather):
    rain_1h = weather.get("rain", {}).get("1h", 0.0)

    features = [
        rain_1h,                   # tp_lag1
        rain_1h,                   # tp_lag2
        rain_1h,                   # tp_lag3
        rain_1h * 3,               # tp_3d_sum
        rain_1h * 7,               # tp_7d_sum
        weather["main"]["temp"],   # t2m_7d_mean
        weather["wind"]["speed"],  # wind speed
        weather["main"]["pressure"], # pressure
        weather["main"]["humidity"], # humidity
        weather["clouds"]["all"]     # cloud cover
    ]

    return features

def send_to_api(features):
    payload = {
        "features": features
    }
    response = requests.post(
        "http://127.0.0.1:8000/predict",
        json=payload
    )
    return response.json()

if __name__ == "__main__":
    weather = fetch_weather(LAT, LON)
    features = build_features(weather)

    print("Live features:", features)

    result = send_to_api(features)
    print("\nFlood Prediction Result:")
    print(result)
