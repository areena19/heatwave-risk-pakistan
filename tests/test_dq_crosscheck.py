import pandas as pd

from src.dq_agent.checks import check_crosscheck, check_crosscheck_rh

T = {"source_diff_temp_c": 3, "source_diff_rh_pct": 15}


def make_data(n_days=10):
    # PKT ke 10 poore din (00:00 PKT = 19:00 UTC pichla din)
    time = pd.date_range("2025-05-31 19:00", periods=n_days * 24, freq="h", tz="UTC")
    df = pd.DataFrame({
        "city": "Karachi",
        "time": time,
        "temperature_2m": 30.0,
        "relative_humidity_2m": 50.0,
    })
    nasa = pd.DataFrame({
        "city": "Karachi",
        "time": time,
        "nasa_temp": 30.0,
        "nasa_rh": 50.0,
    })
    return df, nasa


def test_crosscheck_temp_passes_when_sources_agree(monkeypatch):
    df, nasa = make_data()
    monkeypatch.setattr("src.dq_agent.checks.load_nasa", lambda: nasa)
    r = check_crosscheck(df, T)
    assert r["status"] == "PASS"
    assert r["n_total"] == 10


def test_crosscheck_temp_warns_on_bad_day(monkeypatch):
    df, nasa = make_data()
    df.loc[24:47, "temperature_2m"] += 10  # ek poora din +10°C
    monkeypatch.setattr("src.dq_agent.checks.load_nasa", lambda: nasa)
    r = check_crosscheck(df, T)
    assert r["status"] == "WARN"
    assert r["n_bad"] == 1


def test_crosscheck_rh_passes_when_sources_agree(monkeypatch):
    df, nasa = make_data()
    monkeypatch.setattr("src.dq_agent.checks.load_nasa", lambda: nasa)
    assert check_crosscheck_rh(df, T)["status"] == "PASS"


def test_crosscheck_rh_warns_on_bad_day(monkeypatch):
    df, nasa = make_data()
    df.loc[24:47, "relative_humidity_2m"] += 30  # ek poora din +30%
    monkeypatch.setattr("src.dq_agent.checks.load_nasa", lambda: nasa)
    r = check_crosscheck_rh(df, T)
    assert r["status"] == "WARN"
    assert r["n_bad"] == 1