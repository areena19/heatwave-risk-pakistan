import csv, hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "manifest.csv"


def verify():
    bad = 0
    with open(MANIFEST, newline="") as f:
        for row in csv.DictReader(f):
            path = RAW / row["file"]
            if not path.exists():
                print(f"MISSING  {row['file']}")
                bad += 1
            elif hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                print(f"CHANGED  {row['file']}")
                bad += 1
            else:
                print(f"OK       {row['file']}")
    return bad


if __name__ == "__main__":
    sys.exit(1 if verify() else 0)