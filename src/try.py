import pandas as pd

df = pd.read_csv("../data/era5_combined.csv", nrows=5)
print(df.columns)
print(df.head())
