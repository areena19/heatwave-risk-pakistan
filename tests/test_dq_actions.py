import numpy as np
import pandas as pd

from src.dq_agent import actions
from src.dq_agent.reporting import read_log

T = {
    "temp_c": {"min": -5, "max": 55},
    "humidity_pct": {"min": 0, "max": 100},
    "source_diff_temp_c": 3,
    "source_diff_rh_pct": 15,
}


def make_df(n=12, drop=None):
    df = pd.DataFrame({
        "city": "Karachi",
        "time": pd.date_range("2025-06-01", periods=n, freq="h", tz="UTC"),
        "temperature_2m": np.arange(n, dtype=float) + 20,
        "relative_humidity_2m": 50.0,
        "wind_speed_10m": 10.0,
        "surface_pressure": 1000.0,
    })
    if drop:
        df = df.drop(index=drop).reset_index(drop=True)
    return df


def test_kelvin_fixed(tmp_path):
    p = str(tmp_path / "log.jsonl")
    df = make_df()
    df["temperature_2m"] += 273.15
    out, n = actions.fix_temperature_units(df, log_path=p)
    assert n == 12
    assert out["temperature_2m"].max() < 60
    assert read_log(p)[0]["action"] == "fix"


def test_celsius_untouched(tmp_path):
    p = str(tmp_path / "log.jsonl")
    out, n = actions.fix_temperature_units(make_df(), log_path=p)
    assert n == 0 and read_log(p) == []


def test_short_gap_filled(tmp_path):
    p = str(tmp_path / "log.jsonl")
    out, n_fill, n_long = actions.fill_short_gaps(make_df(drop=[4, 5]), 3, log_path=p)
    assert (n_fill, n_long) == (2, 0)
    assert len(out) == 12
    assert out["is_imputed"].sum() == 2
    assert out["temperature_2m"].notna().all()


def test_long_gap_stays_missing(tmp_path):
    p = str(tmp_path / "log.jsonl")
    out, n_fill, n_long = actions.fill_short_gaps(make_df(drop=[3, 4, 5, 6]), 3, log_path=p)
    assert (n_fill, n_long) == (0, 4)
    assert out["temperature_2m"].isna().sum() == 4
    assert out["is_imputed"].sum() == 0


def test_impossible_value_flagged_and_missing(tmp_path):
    p = str(tmp_path / "log.jsonl")
    df = make_df()
    df.loc[3, "temperature_2m"] = 99
    df.loc[6, "relative_humidity_2m"] = 150
    out, n = actions.flag_impossible_values(df, T, log_path=p)
    assert n == 2
    assert out["flag_impossible"].sum() == 2
    assert np.isnan(out.loc[3, "temperature_2m"])
    assert np.isnan(out.loc[6, "relative_humidity_2m"])


def test_source_disagreement_flagged(tmp_path):
    p = str(tmp_path / "log.jsonl")
    time = pd.date_range("2025-05-31 19:00", periods=10 * 24, freq="h", tz="UTC")
    df = pd.DataFrame({"city": "Karachi", "time": time,
                       "temperature_2m": 30.0, "relative_humidity_2m": 50.0})
    nasa = pd.DataFrame({"city": "Karachi", "time": time,
                         "nasa_temp": 30.0, "nasa_rh": 50.0})
    df.loc[24:47, "temperature_2m"] += 10  # ek poora din
    out, n = actions.flag_source_disagreement(df, T, nasa, log_path=p)
    assert n == 24
    assert out["flag_source_diff"].sum() == 24
    assert out["temperature_2m"].notna().all()  # values delete nahi hui