import numpy as np
import pandas as pd

from src.dq_agent.reporting import log_decision

VALUE_COLS = ["temperature_2m", "relative_humidity_2m",
              "wind_speed_10m", "surface_pressure"]
KELVIN_OFFSET = 273.15
KELVIN_MEDIAN_LIMIT = 150


def _kw(log_path):
    return {"path": log_path} if log_path else {}


# ---------- 1. FIX: galat unit (Kelvin -> Celsius) ----------
def fix_temperature_units(df, log_path=None):
    df = df.copy()
    fixed = 0
    for city, idx in df.groupby("city").groups.items():
        median = df.loc[idx, "temperature_2m"].median()
        if median > KELVIN_MEDIAN_LIMIT:
            df.loc[idx, "temperature_2m"] -= KELVIN_OFFSET
            fixed += len(idx)
            log_decision("unit_check", "fix",
                         f"{city}: temperature in Kelvin (median {median:.1f}), converted to Celsius",
                         len(idx), **_kw(log_path))
    return df, fixed


# ---------- 2. FILL: gap <= max_gap ghante (is_imputed) ----------
def _fill_city(g, max_gap):
    g = g.set_index("time").sort_index()
    full = pd.date_range(g.index.min(), g.index.max(), freq="h", tz=g.index.tz)
    g = g.reindex(full)
    g.index.name = "time"
    g["city"] = g["city"].ffill().bfill()

    missing = g["temperature_2m"].isna()
    run_id = (missing != missing.shift()).cumsum()
    run_len = missing.groupby(run_id).transform("sum")
    fillable = missing & (run_len <= max_gap)
    too_long = missing & (run_len > max_gap)

    filled = g[VALUE_COLS].interpolate(method="linear", limit_area="inside")
    g["is_imputed"] = False
    for col in VALUE_COLS:
        g.loc[fillable, col] = filled.loc[fillable, col]
    g.loc[fillable, "is_imputed"] = True
    return g.reset_index(), int(fillable.sum()), int(too_long.sum())


def fill_short_gaps(df, max_gap, log_path=None):
    parts, n_fill, n_long = [], 0, 0
    for _, g in df.groupby("city"):
        out, f, l = _fill_city(g.copy(), max_gap)
        parts.append(out)
        n_fill += f
        n_long += l
    result = pd.concat(parts, ignore_index=True)
    if n_fill:
        log_decision("gap_fill", "fill",
                     f"gap <= {max_gap}h, linear interpolation, is_imputed=True",
                     n_fill, **_kw(log_path))
    if n_long:
        log_decision("gap_long", "flag",
                     f"gap > {max_gap}h, kept as missing", n_long, **_kw(log_path))
    return result, n_fill, n_long


# ---------- 3. FLAG: impossible value -> missing ----------
def flag_impossible_values(df, t, log_path=None):
    df = df.copy()
    temp, rh = df["temperature_2m"], df["relative_humidity_2m"]
    temp_bad = temp.notna() & ~temp.between(t["temp_c"]["min"], t["temp_c"]["max"])
    rh_bad = rh.notna() & ~rh.between(t["humidity_pct"]["min"], t["humidity_pct"]["max"])
    df["flag_impossible"] = temp_bad | rh_bad
    df.loc[temp_bad, "temperature_2m"] = np.nan
    df.loc[rh_bad, "relative_humidity_2m"] = np.nan
    n = int(df["flag_impossible"].sum())
    if n:
        log_decision("range", "flag",
                     "impossible temperature/humidity, set to missing", n, **_kw(log_path))
    return df, n


# ---------- 4. FLAG: Open-Meteo vs NASA farq ----------
def flag_source_disagreement(df, t, nasa, log_path=None):
    df = df.reset_index(drop=True).copy()
    df["_date"] = df["time"].dt.tz_convert("Asia/Karachi").dt.date
    df["flag_source_diff"] = False
    pairs = [("temperature_2m", "nasa_temp", t["source_diff_temp_c"], "temperature"),
             ("relative_humidity_2m", "nasa_rh", t["source_diff_rh_pct"], "humidity")]
    for col, ncol, thr, name in pairs:
        m = df[["city", "time", "_date", col]].merge(
            nasa[["city", "time", ncol]], on=["city", "time"])
        pkt = m["time"].dt.tz_convert("Asia/Karachi")
        m["diff"] = m[col] - m[ncol]
        m["resid"] = m["diff"] - m.groupby(["city", pkt.dt.month, pkt.dt.hour])["diff"].transform("median")
        d = m.groupby(["city", "_date"]).agg(n=("time", "count"), mr=("resid", "mean")).reset_index()
        d = d[(d["n"] == 24) & (d["mr"].abs() > thr)]
        hit = df.merge(d[["city", "_date"]].assign(_b=True),
                       on=["city", "_date"], how="left")["_b"].notna().values
        df["flag_source_diff"] |= hit
        if hit.sum():
            log_decision("source_crosscheck", "flag",
                         f"Open-Meteo vs NASA {name} daily residual above {thr}, values kept",
                         int(hit.sum()), **_kw(log_path))
    n = int(df["flag_source_diff"].sum())
    return df.drop(columns="_date"), n