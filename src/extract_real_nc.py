import os
import zipfile
import tarfile
from glob import glob

DATA_DIR = "../data"
OUTPUT_DIR = "../data/extracted"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def try_extract(archive_path):
    name = os.path.basename(archive_path).replace(".nc", "")
    out_folder = os.path.join(OUTPUT_DIR, name)
    os.makedirs(out_folder, exist_ok=True)

    print(f"Extracting {archive_path} -> {out_folder}")

    # Try ZIP
    try:
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(out_folder)
            return True
    except:
        pass

    # Try TAR
    try:
        with tarfile.open(archive_path, "r:*") as t:
            t.extractall(out_folder)
            return True
    except:
        pass

    print(f"❌ Could not extract: {archive_path}")
    return False


archives = glob(os.path.join(DATA_DIR, "era5_*.nc"))

print(f"Found {len(archives)} raw archive files")

for f in archives:
    try_extract(f)

print("\n✔ Extraction complete.")
print("Check folder:", OUTPUT_DIR)
