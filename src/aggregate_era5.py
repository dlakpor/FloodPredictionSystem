import pandas as pd

print("Loading combined dataset...")
df = pd.read_csv("../data/era5_combined.csv")

# Convert time to datetime
df["time"] = pd.to_datetime(df["time"])

print("Aggregating (grouping by date, latitude, longitude)...")

# Group by date + lat/lon
daily = df.groupby([
    df["time"].dt.date,
    "latitude",
    "longitude"
], as_index=False).mean()

print("Saving output...")
daily.rename(columns={"time": "date"}, inplace=True)
daily.to_csv("../data/era5_daily.csv", index=False)

print("DONE! File saved to ../data/era5_daily.csv")
