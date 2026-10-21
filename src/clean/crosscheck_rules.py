import pandas as pd

from src.clean.crosscheck import load_nasa


def main():
    om = pd.read_parquet("data/cleaned/hourly_clean.parquet")
    om = om[["city", "time", "temperature_2m"]]
    m = om.merge(load_nasa(), on=["city", "time"], how="inner")
    m = m.sort_values(["city", "time"]).reset_index(drop=True)

    pkt = m["time"].dt.tz_convert("Asia/Karachi")
    m["hour"] = pkt.dt.hour
    m["month"] = pkt.dt.month
    m["date"] = pkt.dt.date
    m["diff"] = m["temperature_2m"] - m["nasa_temp"]
    m["resid"] = m["diff"] - m.groupby(["city", "month", "hour"])["diff"].transform("median")

    # Rule 1: |resid| > 3C for 3+ consecutive hours
    m["over"] = m["resid"].abs() > 3
    run_id = (m["over"] != m.groupby("city")["over"].shift()).cumsum()
    run_len = m.groupby(run_id)["over"].transform("size")
    m["persistent"] = m["over"] & (run_len >= 3)

    print("Rule 1: persistent hours (3+ in a row over 3C)")
    r1 = m.groupby("city").agg(
        hours=("persistent", "sum"),
        pct=("persistent", lambda s: s.mean() * 100),
    )
    r1["runs"] = (
        m[m["persistent"]].groupby("city")["time"].count() * 0
        + m[m["persistent"]].groupby(["city", run_id[m["persistent"]]]).ngroups
    )
    print(r1[["hours", "pct"]].round(2))
    print()

    # Rule 2: daily mean residual
    d = m.groupby(["city", "date"]).agg(n=("time", "count"), mr=("resid", "mean")).reset_index()
    d = d[d["n"] == 24]
    print("Rule 2: days where |daily mean residual| is above:")
    for thr in (1, 1.5, 2, 3):
        pct = (d["mr"].abs() > thr).groupby(d["city"]).mean() * 100
        print(f"  > {thr}C:", pct.round(2).to_dict())
    print("Max |daily mean residual|:", d["mr"].abs().groupby(d["city"]).max().round(2).to_dict())


if __name__ == "__main__":
    main()