import pandas as pd


def main():
    df = pd.read_parquet("data/cleaned/hourly_clean.parquet")
    df = df.sort_values(["city", "time"])

    df["gap_hours"] = df.groupby("city")["time"].diff().dt.total_seconds() / 3600

    print("Gap value counts (should be only 1.0):")
    print(df["gap_hours"].value_counts(dropna=True))
    print()

    for city, g in df.groupby("city"):
        full = pd.date_range(g["time"].min(), g["time"].max(), freq="h")
        print(city, "missing hours:", len(full) - len(g))


if __name__ == "__main__":
    main()