import pandas as pd


def main():
    df = pd.read_parquet("data/cleaned/hourly_clean.parquet")
    df = df.sort_values(["city", "time"])

    df["temp_change"] = df.groupby("city")["temperature_2m"].diff().abs()

    print(df["temp_change"].describe())
    print()
    print("Jumps > 5C:", (df["temp_change"] > 5).sum())
    print("Jumps > 8C:", (df["temp_change"] > 8).sum())
    print()
    print("Top 10 biggest jumps:")
    cols = ["city", "time_pkt", "temperature_2m", "temp_change"]
    print(df.nlargest(10, "temp_change")[cols])


if __name__ == "__main__":
    main()