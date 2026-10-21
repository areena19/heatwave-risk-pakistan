import os
import shutil
from datetime import datetime, timezone

import pandera.pandas as pa

from src.dq_agent.reporting import log_decision

QUARANTINE_DIR = "data/quarantine"
GOLD_PATH = "data/processed/features.parquet"
LAST_GOOD_PATH = "data/processed/last_good/features.parquet"


def build_schema(t):
    return pa.DataFrameSchema(
        {
            "temperature_2m": pa.Column(float, pa.Check.in_range(t["temp_c"]["min"], t["temp_c"]["max"]), nullable=True),
            "relative_humidity_2m": pa.Column(float, pa.Check.in_range(t["humidity_pct"]["min"], t["humidity_pct"]["max"]), nullable=True),
            "wind_speed_10m": pa.Column(float, pa.Check.ge(0), nullable=True),
            "surface_pressure": pa.Column(float, pa.Check.in_range(800, 1100), nullable=True),
            "city": pa.Column(str),
        },
        unique=["city", "time"],
    )


def quarantine(bad, gate_name):
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = f"{QUARANTINE_DIR}/{gate_name}_{stamp}.parquet"
    bad.to_parquet(path, index=False)
    return path


def alert(message, log_path=None):
    print(f"ALERT: {message}")
    kw = {"path": log_path} if log_path else {}
    log_decision("alert", "alert", message, 0, **kw)


def run_schema_gate(df, t, gate_name, log_path=None):
    """Returns (good_rows, bad_rows, passed). Df ka index default (0..n) hona chahiye."""
    try:
        build_schema(t).validate(df, lazy=True)
        return df, df.iloc[0:0], True
    except pa.errors.SchemaErrors as e:
        idx = e.failure_cases["index"].dropna().astype(int).unique()
        if len(idx) == 0:
            raise  # schema-level masla (jaise column missing), rows alag nahi ho sakti
        bad = df.loc[idx]
        good = df.drop(index=idx)
        path = quarantine(bad, gate_name)
        kw = {"path": log_path} if log_path else {}
        log_decision(gate_name, "quarantine",
                     f"schema failed, rows saved to {path}", len(bad), **kw)
        alert(f"{gate_name} failed: {len(bad)} rows quarantined", log_path)
        return good, bad, False


def save_last_good(src=GOLD_PATH, dst=LAST_GOOD_PATH):
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        return True
    return False


def restore_last_good(src=LAST_GOOD_PATH, dst=GOLD_PATH, log_path=None):
    if os.path.exists(src):
        shutil.copy2(src, dst)
        kw = {"path": log_path} if log_path else {}
        log_decision("gate_fail", "keep_last_good",
                     "gate failed, last good Gold version kept", 0, **kw)
        return True
    return False