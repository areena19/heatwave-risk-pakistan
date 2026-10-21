import csv, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "manifest.csv"
FIELDS = ["file", "source", "query", "fetched_at_utc", "sha256", "licence"]


def log_manifest(file, source, query, content, licence):
    new = not MANIFEST.exists() or MANIFEST.stat().st_size == 0
    with open(MANIFEST, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({
            "file": file,
            "source": source,
            "query": query,
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sha256": hashlib.sha256(content).hexdigest(),
            "licence": licence,
        })