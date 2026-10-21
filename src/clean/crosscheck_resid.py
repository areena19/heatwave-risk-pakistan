import pandas as pd

from src.clean.crosscheck import load_nasa


def main():
    om = pd.read_parquet("data/cleaned/hourly_clean.parquet")
    om = om[["city", "time", "temperature_2m"]]
    m = om.merge(load_nasa(), on=["city", "time"], how="inner")

    pkt = m["time"].dt.tz_convert("Asia/Karachi")
    m["hour"] = pkt.dt.hour
    m["month"] = pkt.dt.month
    m["diff"] = m["temperature_2m"] - m["nasa_temp"]

    for keys in (["city", "hour"], ["city", "month", "hour"]):
        bias = m.groupby(keys)["diff"].transform("median")
        resid = (m["diff"] - bias).abs()
        out = pd.DataFrame(
            {
                "mae": resid.groupby(m["city"]).mean(),
                "p99": resid.groupby(m["city"]).quantile(0.99),
                "max_abs": resid.groupby(m["city"]).max(),
                "pct_over_3c": (resid > 3).groupby(m["city"]).mean() * 100,
            }
        )
        print("Bias removed by", keys)
        print(out.round(2))
        print()


if __name__ == "__main__":
    main()