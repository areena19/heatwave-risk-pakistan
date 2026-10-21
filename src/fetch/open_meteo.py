import re, time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import yaml

from .manifest import log_manifest

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
URL = "https://archive-api.open-meteo.com/v1/archive"
RECENT_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY = "temperature_2m,relative_humidity_2m,wind_speed_10m,surface_pressure"
LICENCE = "CC BY 4.0 (Open-Meteo)"


def last_end(city):
    ends = []
    for f in RAW.glob(f"openmeteo_{city}_*.json"):
        m = re.search(r"_(\d{4}-\d{2}-\d{2})\.json$", f.name)
        if m:
            ends.append(date.fromisoformat(m.group(1)))
    return max(ends) if ends else None


def fetch(lat, lon, start, end):
    params = dict(latitude=lat, longitude=lon, start_date=start, end_date=end,
                  hourly=HOURLY, timezone="UTC")
    for attempt in range(3):
        try:
            r = httpx.get(URL, params=params, timeout=60)
            r.raise_for_status()
            return r
        except httpx.HTTPError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def run():
    RAW.mkdir(parents=True, exist_ok=True)
    cities = yaml.safe_load(open(ROOT / "config" / "cities.yaml"))["cities"]
    end = date.today() - timedelta(days=2)

    for city, c in cities.items():
        prev = last_end(city)
        start = prev + timedelta(days=1) if prev else end - timedelta(days=730)
        if start > end:
            print(f"{city}: up to date")
            continue

        r = fetch(c["lat"], c["lon"], start, end)
        path = RAW / f"openmeteo_{city}_{start}_{end}.json"
        path.write_bytes(r.content)
        log_manifest(path.name, "open-meteo", str(r.url), r.content, LICENCE)
        print(f"{city}: saved {start} → {end}")


def run_recent():
    cities = yaml.safe_load(open(ROOT / "config" / "cities.yaml"))["cities"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")

    for city, c in cities.items():
        path = RAW / f"openmeteorecent_{city}_{stamp}.json"
        if path.exists():
            print(f"{city}: recent already saved for {stamp}")
            continue
        params = dict(latitude=c["lat"], longitude=c["lon"], hourly=HOURLY,
                      timezone="UTC", past_days=2, forecast_days=1)
        r = httpx.get(RECENT_URL, params=params, timeout=60)
        r.raise_for_status()
        path.write_bytes(r.content)
        log_manifest(path.name, "open-meteo-recent", str(r.url), r.content, LICENCE)
        print(f"{city}: saved recent {stamp}")


if __name__ == "__main__":
    run()
    run_recent()