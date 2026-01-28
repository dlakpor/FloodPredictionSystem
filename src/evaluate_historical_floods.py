import pandas as pd
import requests
from sklearn.metrics import classification_report, roc_auc_score

API_URL = "http://127.0.0.1:8000/predict"
FLOOD_EVENTS = "data/cyprus_flood_events.csv"

df = pd.read_csv(FLOOD_EVENTS, parse_dates=["date"])

y_true = []
y_pred = []
y_proba = []

for _, row in df.iterrows():
    # Dummy features (replace with real lagged features if stored)
    features = [
        0.2, 0.1, 0.05,  # tp lags
        0.35, 0.6,      # rolling sums
        14.5,           # temp
        1015,           # pressure
        80,             # humidity
        90,             # cloud cover
        1               # wind proxy
    ]

    response = requests.post(API_URL, json={"features": features})
    result = response.json()

    flood_prob = result["flood_probability"]
    flood_risk = result["flood_risk"]

    y_true.append(1)  # known flood
    y_pred.append(1 if flood_risk != "Low" else 0)
    y_proba.append(flood_prob)

print("\nClassification Report:")
print(classification_report(y_true, y_pred))

print("ROC-AUC:", roc_auc_score(y_true, y_proba))
