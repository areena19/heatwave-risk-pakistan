import re, time
from datetime import date, timedelta
from pathlib import Path

import httpx
import yaml

from .manifest import log_manifest

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
PARAMS = "T2M,RH2M"
LICENCE = "NASA POWER (open data, cite NASA/POWER)"


def last_end(city):
    ends = []
    for f in RAW.glob(f"nasapower_{city}_*.json"):
        m = re.search(r"_(\d{4}-\d{2}-\d{2})\.json$", f.name)
        if m:
            ends.append(date.fromisoformat(m.group(1)))
    return max(ends) if ends else None


def fetch(lat, lon, start, end):
    params = {
        "parameters": PARAMS,
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "UTC",
    }
    for attempt in range(3):
        try:
            r = httpx.get(URL, params=params, timeout=120)
            r.raise_for_status()
            return r
        except httpx.HTTPError:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def run():
    RAW.mkdir(parents=True, exist_ok=True)
    cities = yaml.safe_load(open(ROOT / "config" / "cities.yaml"))["cities"]
    end = date.today() - timedelta(days=7)  # safe lag, we will verify

    for city, c in cities.items():
        prev = last_end(city)
        start = prev + timedelta(days=1) if prev else end - timedelta(days=730)
        if start > end:
            print(f"{city}: up to date")
            continue

        r = fetch(c["lat"], c["lon"], start, end)
        path = RAW / f"nasapower_{city}_{start}_{end}.json"
        path.write_bytes(r.content)
        log_manifest(path.name, "nasa-power", str(r.url), r.content, LICENCE)
        print(f"{city}: saved {start} → {end}")
        time.sleep(3)  # be polite, API has rate limits


if __name__ == "__main__":
    run()