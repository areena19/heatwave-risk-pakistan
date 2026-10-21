import os

import pandas as pd

from src.features.heat_index import heat_index_c


def main():
    df = pd.read_parquet("data/cleaned/hourly_dq.parquet")
    df["heat_index"] = heat_index_c(
        df["temperature_2m"].to_numpy(), df["relative_humidity_2m"].to_numpy()
    )
    df["date"] = df["time_pkt"].dt.date

    daily = (
        df.groupby(["city", "date"])
        .agg(
            n_hours=("heat_index", "count"),
            max_temp=("temperature_2m", "max"),
            max_hi=("heat_index", "max"),
            mean_humidity=("relative_humidity_2m", "mean"),
            mean_wind=("wind_speed_10m", "mean"),
            mean_pressure=("surface_pressure", "mean"),
            any_jump_flag=("jump_flag", "max"),
        )
        .reset_index()
    )

    print("Days before dropping partial days:", len(daily))
    daily = daily[daily["n_hours"] == 24].drop(columns="n_hours")
    print("Days after dropping partial days:", len(daily))

    os.makedirs("data/processed", exist_ok=True)
    daily.to_parquet("data/processed/daily.parquet", index=False)

    print(daily.groupby("city")["max_hi"].describe()[["min", "mean", "max"]])


if __name__ == "__main__":
    main()