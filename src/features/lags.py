import pandas as pd


def main():
    df = pd.read_parquet("data/processed/daily.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["city", "date"]).reset_index(drop=True)

    g = df.groupby("city")
    df["target"] = g["max_hi"].shift(-1)
    df["hi_lag1"] = g["max_hi"].shift(1)
    df["hi_lag7"] = g["max_hi"].shift(7)
    df["temp_lag1"] = g["max_temp"].shift(1)
    df["hi_roll7"] = g["max_hi"].transform(lambda s: s.rolling(7).mean())
    df["month"] = df["date"].dt.month

    # Sirf shuru ke 7 din drop karein jinke lags nahi hain. AAKHRI DIN DROP NAHI KAREIN (wahi kal predict karega)
    df = df.dropna(subset=["hi_lag1", "hi_lag7", "temp_lag1", "hi_roll7"])
    print("Rows for features & prediction:", len(df))

    df["row_id"] = df["city"] + "_" + df["date"].dt.strftime("%Y-%m-%d")
    df.to_parquet("data/processed/features.parquet", index=False)

    # persistence baseline calculation on known targets
    valid = df.dropna(subset=["target"])
    err = (valid["target"] - valid["max_hi"]).abs()
    print("Persistence baseline MAE (overall):", round(err.mean(), 3))


if __name__ == "__main__":
    main()