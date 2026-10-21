import os

import pandas as pd
import yaml

from src.clean.crosscheck import load_nasa
from src.dq_agent import actions, checks, gates, reporting

CORE = ["city", "time", "temperature_2m", "relative_humidity_2m",
        "wind_speed_10m", "surface_pressure"]
OUT_PATH = "data/cleaned/hourly_dq.parquet"


def main():
    with open("config/thresholds.yaml") as f:
        t = yaml.safe_load(f)
    df = pd.read_parquet("data/cleaned/hourly_clean.parquet")

    # Actions
    df, n = actions.fix_temperature_units(df)
    print("Fixed unit rows:", n)
    df, n_fill, n_long = actions.fill_short_gaps(df, t["max_fill_gap_hours"])
    print("Filled:", n_fill, "| Long gaps kept missing:", n_long)
    df, n = actions.flag_impossible_values(df, t)
    print("Impossible values flagged:", n)
    df, n = actions.flag_source_disagreement(df, t, load_nasa())
    print("Source-disagreement rows flagged:", n)

    # Gate 1: schema (kharab rows quarantine)
    df = df.reset_index(drop=True)
    df, bad, passed = gates.run_schema_gate(df, t, "gate1_schema")
    print("Gate 1 (schema):", "PASS" if passed else f"FAIL, {len(bad)} rows quarantined")

    # Gate 2: checks (hard FAIL ho to Gold na badle)
    results = checks.run_all(df)
    report = reporting.write_report(results)
    print("Gate 2 (checks):", report["overall"])
    for r in results:
        print(f"  {r['status']:5} {r['check']:13} {r['n_bad']}/{r['n_total']}")

    if report["overall"] == "FAIL":
        gates.alert("Gate 2 failed, Gold not updated")
        gates.restore_last_good()
        raise SystemExit(1)

    os.makedirs("data/cleaned", exist_ok=True)

    df["time_pkt"] = df["time"].dt.tz_convert("Asia/Karachi")
    df = df.sort_values(["city", "time"]).reset_index(drop=True)
    df["temp_change"] = df.groupby("city")["temperature_2m"].diff().abs()
    df["jump_flag"] = df["temp_change"] > t["max_hourly_jump_c"]

    df.to_parquet(OUT_PATH, index=False)
    gates.save_last_good()
    print("Saved:", OUT_PATH, df.shape)


if __name__ == "__main__":
    main()