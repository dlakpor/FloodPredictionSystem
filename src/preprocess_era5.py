import os
import xarray as xr
import pandas as pd

DATA_DIR = "../data/extracted"

def preprocess_real_nc():
    dfs = []

    for root, dirs, files in os.walk(DATA_DIR):
        for f in files:
            if f.endswith(".nc"):
                file_path = os.path.join(root, f)
                print("Reading:", file_path)

                ds = xr.open_dataset(file_path)

                # Convert to DataFrame
                df = ds[["tp", "t2m"]].to_dataframe().reset_index()

                # Rename valid_time → time
                df = df.rename(columns={"valid_time": "time"})

                dfs.append(df)

    print(f"Loaded {len(dfs)} monthly datasets")

    # Combine all
    combined = pd.concat(dfs)
    combined = combined.sort_values("time")

    # Save final CSV
    output_path = "../data/era5_combined.csv"
    combined.to_csv(output_path, index=False)

    print("\nFINAL DATASET SAVED:")
    print(output_path)
    print("Rows:", len(combined))

if __name__ == "__main__":
    preprocess_real_nc()
