import pandas as pd

from src.dq_agent import gates
from src.dq_agent.reporting import read_log

T = {
    "temp_c": {"min": -5, "max": 55},
    "humidity_pct": {"min": 0, "max": 100},
}


def make_df(n=6):
    return pd.DataFrame({
        "city": "Karachi",
        "time": pd.date_range("2025-06-01", periods=n, freq="h", tz="UTC"),
        "temperature_2m": 30.0,
        "relative_humidity_2m": 50.0,
        "wind_speed_10m": 10.0,
        "surface_pressure": 1000.0,
    })


def test_clean_data_passes(tmp_path):
    good, bad, passed = gates.run_schema_gate(make_df(), T, "g", log_path=str(tmp_path / "l.jsonl"))
    assert passed and len(bad) == 0 and len(good) == 6


def test_bad_rows_quarantined(tmp_path, monkeypatch):
    monkeypatch.setattr(gates, "QUARANTINE_DIR", str(tmp_path / "q"))
    p = str(tmp_path / "l.jsonl")
    df = make_df()
    df.loc[2, "temperature_2m"] = 99
    good, bad, passed = gates.run_schema_gate(df, T, "g", log_path=p)
    assert not passed
    assert len(bad) == 1 and len(good) == 5
    actions = [r["action"] for r in read_log(p)]
    assert "quarantine" in actions and "alert" in actions
    assert len(list((tmp_path / "q").glob("*.parquet"))) == 1


def test_last_good_saved_and_restored(tmp_path):
    gold = tmp_path / "features.parquet"
    last = tmp_path / "last_good" / "features.parquet"
    pd.DataFrame({"a": [1]}).to_parquet(gold)
    assert gates.save_last_good(str(gold), str(last))
    pd.DataFrame({"a": [999]}).to_parquet(gold)  # kharab version
    assert gates.restore_last_good(str(last), str(gold), log_path=str(tmp_path / "l.jsonl"))
    assert pd.read_parquet(gold)["a"].iloc[0] == 1