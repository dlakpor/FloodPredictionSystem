import xarray as xr

path = "../data/extracted/era5_2023_02/data_0.nc"

ds = xr.open_dataset(path)

print(ds)
print("\nVariables:", list(ds.variables))
