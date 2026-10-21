import pandas as pd

from src.dq_agent.checks import check_gaps, check_jumps, check_range

T = {
    "temp_c": {"min": -10, "max": 60},
    "humidity_pct": {"min": 0, "max": 100},
    "max_hourly_jump_c": 8,
}


def make_df(n=48):
    return pd.DataFrame({
        "city": "Karachi",
        "time": pd.date_range("2025-06-01", periods=n, freq="h", tz="UTC"),
        "temperature_2m": 30.0,
        "relative_humidity_2m": 50.0,
    })


def test_clean_data_passes():
    df = make_df()
    assert check_range(df, T)["status"] == "PASS"
    assert check_jumps(df, T)["status"] == "PASS"
    assert check_gaps(df, T)["status"] == "PASS"


def test_bad_temperature_fails_range():
    df = make_df()
    df.loc[10, "temperature_2m"] = 99
    r = check_range(df, T)
    assert r["status"] == "FAIL"
    assert r["n_bad"] == 1


def test_bad_humidity_fails_range():
    df = make_df()
    df.loc[5, "relative_humidity_2m"] = 150
    assert check_range(df, T)["status"] == "FAIL"


def test_big_jump_warns():
    df = make_df()
    df.loc[10, "temperature_2m"] = 45
    r = check_jumps(df, T)
    assert r["status"] == "WARN"
    assert r["n_bad"] >= 1


def test_missing_hour_fails_gaps():
    df = make_df().drop(index=10).reset_index(drop=True)
    r = check_gaps(df, T)
    assert r["status"] == "FAIL"
    assert r["n_bad"] == 1