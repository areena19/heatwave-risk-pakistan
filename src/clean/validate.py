import yaml

from src.clean.load_raw import load_raw


def main():
    with open("config/thresholds.yaml") as f:
        print("Thresholds file:", yaml.safe_load(f))

    df = load_raw()
    df["time_pkt"] = df["time"].dt.tz_convert("Asia/Karachi")

    print(df[["time", "time_pkt"]].head(3))
    print(df.describe().T[["min", "max"]])


if __name__ == "__main__":
    main()