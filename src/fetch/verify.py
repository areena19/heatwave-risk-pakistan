import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "manifest.csv"


def verify():
    bad = 0
    checked = 0

    if not MANIFEST.exists():
        print("manifest.csv nahi mili!")
        return 0

    with open(MANIFEST, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            path = RAW / row["file"]
            if not path.exists():
                # Purani files jo is fresh run par maujood nahi hain unhe skip karein
                continue
            
            checked += 1
            file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if file_hash != row["sha256"]:
                print(f"CHANGED  {row['file']}")
                bad += 1
            else:
                print(f"OK       {row['file']}")

    if checked == 0:
        print("ERROR: Koi raw file verify karne ke liye nahi mili!")
        return 1

    print(f"\nVerification complete: {checked} files verified OK, {bad} corrupted/changed.")
    return bad


if __name__ == "__main__":
    sys.exit(1 if verify() else 0)