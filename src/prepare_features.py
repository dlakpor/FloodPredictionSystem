# prepare_features.py
import pandas as pd
import numpy as np

IN = "../data/era5_labeled.csv"
OUT = "../data/features_for_ml.csv"
SEQ_DAYS = 7  # how many days of history to use

print("Loading labeled data...")
df = pd.read_csv(IN, parse_dates=["date"])

# Sort for grouping
df = df.sort_values(["latitude", "longitude", "date"]).reset_index(drop=True)

rows = []
for (lat, lon), g in df.groupby(["latitude", "longitude"]):
    g = g.reset_index(drop=True)
    # compute rolling sums / means
    g["tp_3d_sum"] = g["tp"].rolling(3, min_periods=1).sum()
    g["tp_7d_sum"] = g["tp"].rolling(7, min_periods=1).sum()
    g["t2m_7d_mean"] = g["t2m"].rolling(7, min_periods=1).mean()

    # create lag features: tp_{1..SEQ_DAYS}
    for lag in range(1, SEQ_DAYS+1):
        g[f"tp_lag{lag}"] = g["tp"].shift(lag)

    # drop rows with insufficient history
    g = g.dropna(subset=[f"tp_lag{SEQ_DAYS}", "next_tp"])

    rows.append(g)

feat = pd.concat(rows, ignore_index=True)

# Define feature columns
lag_cols = [f"tp_lag{l}" for l in range(1, SEQ_DAYS+1)]
feat_cols = lag_cols + ["tp_3d_sum", "tp_7d_sum", "t2m_7d_mean"]

# Save feature dataset
out_df = feat[["date","latitude","longitude"] + feat_cols + ["next_tp","flood_label"]]
out_df.to_csv(OUT, index=False)
print("Saved features to", OUT)
print("Rows:", len(out_df))
