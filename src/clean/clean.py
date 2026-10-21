import os
import pandas as pd
import pandera.pandas as pa
import yaml

from src.clean.load_raw import load_raw


def build_schema(t):
    return pa.DataFrameSchema(
        {
            "temperature_2m": pa.Column(
                float, pa.Check.in_range(t["temp_c"]["min"], t["temp_c"]["max"])
            ),
            "relative_humidity_2m": pa.Column(
                int,
                pa.Check.in_range(t["humidity_pct"]["min"], t["humidity_pct"]["max"]),
            ),
            "wind_speed_10m": pa.Column(float, pa.Check.ge(0)),
            "surface_pressure": pa.Column(float, pa.Check.in_range(800, 1100)),
            "city": pa.Column(str),
        },
        unique=["city", "time"],
    )


def main():
    with open("config/thresholds.yaml") as f:
        t = yaml.safe_load(f)

    df = load_raw()
    df["time_pkt"] = df["time"].dt.tz_convert("Asia/Karachi")
    df = df.sort_values(["city", "time"]).reset_index(drop=True)

    df["temp_change"] = df.groupby("city")["temperature_2m"].diff().abs()
    df["jump_flag"] = df["temp_change"] > t["max_hourly_jump_c"]
    print("Flagged jumps:", df["jump_flag"].sum())

    build_schema(t).validate(df)
    print("Pandera checks passed")

    os.makedirs("data/cleaned", exist_ok=True)
    df.to_parquet("data/cleaned/hourly_clean.parquet", index=False)
    print("Saved:", df.shape)


if __name__ == "__main__":
    main()