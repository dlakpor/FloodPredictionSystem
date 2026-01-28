# create_labels.py
import pandas as pd
import numpy as np

IN = "../data/era5_daily.csv"
OUT = "../data/era5_labeled.csv"

print("Loading daily ERA5...")
df = pd.read_csv(IN, parse_dates=["date"])

# Make sure columns exist
# columns: date, latitude, longitude, tp, t2m, ...
print("Columns:", df.columns.tolist())

# Use overall 95th percentile of daily rainfall as flood threshold (can be tuned)
threshold = df["tp"].quantile(0.95)
print("Flood threshold (95th percentile) = {:.3f} mm".format(threshold))

# Sort and compute next-day rainfall target and flood label
df = df.sort_values(["latitude", "longitude", "date"]).reset_index(drop=True)

# shift tp by -1 per location to get next-day rainfall
df["next_tp"] = df.groupby(["latitude", "longitude"])["tp"].shift(-1)

# drop rows where next_tp is NaN (end of series)
df = df.dropna(subset=["next_tp"]).reset_index(drop=True)

# binary flood label: next day rainfall above threshold
df["flood_label"] = (df["next_tp"] >= threshold).astype(int)

print("Saving labeled dataset:", OUT)
df.to_csv(OUT, index=False)
print("Done. Rows:", len(df))
