import pandas as pd

from src.clean.crosscheck import load_nasa


def summarize(g, a, b, name):
    d = g[a] - g[b]
    out = pd.DataFrame(
        {
            "bias": d.groupby(g["city"]).mean(),
            "mae": d.abs().groupby(g["city"]).mean(),
            "max_abs": d.abs().groupby(g["city"]).max(),
            "pct_over_3c": (d.abs() > 3).groupby(g["city"]).mean() * 100,
        }
    )
    print(name)
    print(out.round(2))
    print()


def main():
    om = pd.read_parquet("data/cleaned/hourly_clean.parquet")
    om = om[["city", "time", "temperature_2m"]]
    m = om.merge(load_nasa(), on=["city", "time"], how="inner")

    pkt = m["time"].dt.tz_convert("Asia/Karachi")
    m["date"] = pkt.dt.date
    m["hour"] = pkt.dt.hour

    # by-hour bias (PKT): OpenMeteo minus NASA
    m["diff"] = m["temperature_2m"] - m["nasa_temp"]
    print("Bias by PKT hour (OpenMeteo - NASA):")
    print(m.pivot_table(index="hour", columns="city", values="diff").round(2))
    print()

    # daily values, full 24-hour days only
    g = m.groupby(["city", "date"]).agg(
        n=("time", "count"),
        om_max=("temperature_2m", "max"),
        nasa_max=("nasa_temp", "max"),
        om_mean=("temperature_2m", "mean"),
        nasa_mean=("nasa_temp", "mean"),
    ).reset_index()
    g = g[g["n"] == 24]

    summarize(g, "om_max", "nasa_max", "DAILY MAX temp (OpenMeteo - NASA):")
    summarize(g, "om_mean", "nasa_mean", "DAILY MEAN temp (OpenMeteo - NASA):")


if __name__ == "__main__":
    main()