import pandas as pd


def main():
    df = pd.read_parquet("data/processed/daily.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["city", "date"]).reset_index(drop=True)

    # check: every day is exactly 1 day after the previous one, within each city
    gaps = df.groupby("city")["date"].diff().dt.days.dropna()
    print("Date gaps (should be only 1):")
    print(gaps.value_counts())

    g = df.groupby("city")
    df["target"] = g["max_hi"].shift(-1)
    df["hi_lag1"] = g["max_hi"].shift(1)
    df["hi_lag7"] = g["max_hi"].shift(7)
    df["temp_lag1"] = g["max_temp"].shift(1)
    df["hi_roll7"] = g["max_hi"].transform(lambda s: s.rolling(7).mean())
    df["month"] = df["date"].dt.month

    # drop rows where target or lags are missing (first 7 and last day per city)
    df = df.dropna(subset=["target", "hi_lag1", "hi_lag7", "temp_lag1", "hi_roll7"])
    print("Rows after dropping:", len(df))

    df["row_id"] = df["city"] + "_" + df["date"].dt.strftime("%Y-%m-%d")
    df.to_parquet("data/processed/features.parquet", index=False)

    # persistence baseline: predict tomorrow = today
    err = (df["target"] - df["max_hi"]).abs()
    print()
    print("Persistence baseline MAE (overall):", round(err.mean(), 3))
    print(err.groupby(df["city"]).mean().round(3))


if __name__ == "__main__":
    main()