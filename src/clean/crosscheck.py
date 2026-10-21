import glob
import json
import os

import numpy as np
import pandas as pd


def load_nasa():
    frames = []
    for path in sorted(glob.glob("data/raw/nasapower_*.json")):
        city = os.path.basename(path).split("_")[1]
        with open(path) as f:
            d = json.load(f)
        p = d["properties"]["parameter"]
        df = pd.DataFrame({"nasa_temp": p["T2M"], "nasa_rh": p["RH2M"]})
        df.index.name = "time"
        df = df.reset_index()
        df["time"] = pd.to_datetime(df["time"], format="%Y%m%d%H", utc=True)
        df["time"] = df["time"].dt.as_unit("us")
        df["city"] = city
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)
    cols = ["nasa_temp", "nasa_rh"]
    out[cols] = out[cols].replace(-999.0, np.nan)
    return out


def main():
    om = pd.read_parquet("data/cleaned/hourly_clean.parquet")
    om = om[["city", "time", "temperature_2m", "relative_humidity_2m"]]
    nasa = load_nasa()

    print("NASA missing (-999):")
    print(nasa[["nasa_temp", "nasa_rh"]].isna().sum())

    m = om.merge(nasa, on=["city", "time"], how="inner")
    print("Overlap rows:", len(m))

    m["temp_diff"] = m["temperature_2m"] - m["nasa_temp"]
    m["abs_diff"] = m["temp_diff"].abs()

    summary = m.groupby("city").agg(
        bias=("temp_diff", "mean"),
        mae=("abs_diff", "mean"),
        max_abs=("abs_diff", "max"),
        pct_over_3c=("abs_diff", lambda s: (s > 3).mean() * 100),
    )
    print()
    print(summary.round(2))
    print()
    print("Hours with diff > 3C:", (m["abs_diff"] > 3).sum(), "of", len(m))


if __name__ == "__main__":
    main()