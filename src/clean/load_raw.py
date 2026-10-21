import glob
import json
import os

import pandas as pd


def read_files(pattern, cutoff_from_name=False):
    frames = []
    for path in sorted(glob.glob(pattern)):
        name = os.path.basename(path)
        city = name.split("_")[1]
        with open(path) as f:
            data = json.load(f)
        df = pd.DataFrame(data["hourly"])
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df["city"] = city

        if cutoff_from_name:
            # name looks like openmeteorecent_Karachi_2026-10-21T10.json
            stamp = name.rsplit("_", 1)[1].replace(".json", "")
            cutoff = pd.to_datetime(stamp, format="%Y-%m-%dT%H", utc=True)
            df = df[df["time"] <= cutoff]

        frames.append(df)
    return frames


def load_raw():
    archive = pd.concat(read_files("data/raw/openmeteo_*.json"), ignore_index=True)

    recent_frames = read_files("data/raw/openmeteorecent_*.json", cutoff_from_name=True)
    if recent_frames:
        recent = pd.concat(recent_frames, ignore_index=True)
        # files are sorted by name (oldest first), so keep the newest copy
        recent = recent.drop_duplicates(["city", "time"], keep="last")
        # archive comes first, so it wins over recent
        combined = pd.concat([archive, recent], ignore_index=True)
        combined = combined.drop_duplicates(["city", "time"], keep="first")
    else:
        combined = archive

    return combined.sort_values(["city", "time"]).reset_index(drop=True)


if __name__ == "__main__":
    df = load_raw()
    print(df.shape)
    print(df.dtypes)
    print(df.groupby("city").size())
    print(df.groupby("city")["time"].agg(["min", "max"]))
    print("Missing values:")
    print(df.isna().sum())