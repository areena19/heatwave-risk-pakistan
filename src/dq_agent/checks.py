import pandas as pd
import yaml

from src.clean.crosscheck import load_nasa

def result(name, kind, n_bad, n_total, detail=None):
    if n_bad == 0:
        status = "PASS"
    else:
        status = "FAIL" if kind == "hard" else "WARN"
    return {"check": name, "status": status, "n_bad": int(n_bad),
            "n_total": int(n_total), "detail": detail or {}}


def check_range(df, t):
    temp_ok = df["temperature_2m"].between(t["temp_c"]["min"], t["temp_c"]["max"]) | df["temperature_2m"].isna()
    rh_ok = df["relative_humidity_2m"].between(t["humidity_pct"]["min"], t["humidity_pct"]["max"]) | df["relative_humidity_2m"].isna()
    return result("range", "hard", (~(temp_ok & rh_ok)).sum(), len(df))


def check_jumps(df, t):
    d = df.sort_values(["city", "time"])
    change = d.groupby("city")["temperature_2m"].diff().abs()
    bad = change > t["max_hourly_jump_c"]
    return result("jumps", "soft", bad.sum(), len(df),
                  bad.groupby(d["city"]).sum().to_dict())


def check_gaps(df, t):
    missing = {}
    for city, g in df.groupby("city"):
        full = pd.date_range(g["time"].min(), g["time"].max(), freq="h")
        missing[city] = len(full) - len(g)
    return result("gaps", "hard", sum(missing.values()), len(df), missing)


def _crosscheck(df, t, col, ncol, thr, name):
    m = df[["city", "time", col]].merge(load_nasa(), on=["city", "time"])
    pkt = m["time"].dt.tz_convert("Asia/Karachi")
    m["hour"] = pkt.dt.hour
    m["month"] = pkt.dt.month
    m["date"] = pkt.dt.date
    m["diff"] = m[col] - m[ncol]
    m["resid"] = m["diff"] - m.groupby(["city", "month", "hour"])["diff"].transform("median")
    d = m.groupby(["city", "date"]).agg(n=("time", "count"), mr=("resid", "mean")).reset_index()
    d = d[d["n"] == 24]
    bad = d["mr"].abs() > thr
    return result(name, "soft", bad.sum(), len(d), bad.groupby(d["city"]).sum().to_dict())


def check_crosscheck(df, t):
    return _crosscheck(df, t, "temperature_2m", "nasa_temp", t["source_diff_temp_c"], "crosscheck")


def check_crosscheck_rh(df, t):
    return _crosscheck(df, t, "relative_humidity_2m", "nasa_rh", t["source_diff_rh_pct"], "crosscheck_rh")


def check_staleness(df, t, now=None):
    now = now or pd.Timestamp.now(tz="UTC")
    age = {c: round((now - g["time"].max()).total_seconds() / 3600, 1)
           for c, g in df.groupby("city")}
    stale = {c: a for c, a in age.items() if a > t["stale_after_hours"]}
    return result("staleness", "soft", len(stale), len(age), age)


CHECKS = [check_range, check_jumps, check_gaps, check_crosscheck,
          check_crosscheck_rh, check_staleness]


def run_all(df=None):
    with open("config/thresholds.yaml") as f:
        t = yaml.safe_load(f)
    if df is None:
        df = pd.read_parquet("data/cleaned/hourly_clean.parquet")
    return [check(df, t) for check in CHECKS]


if __name__ == "__main__":
    for r in run_all():
        print(f"{r['status']:5} {r['check']:13} {r['n_bad']}/{r['n_total']}  {r['detail']}")