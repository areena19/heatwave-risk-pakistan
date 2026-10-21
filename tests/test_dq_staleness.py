import pandas as pd

from src.dq_agent.checks import check_staleness

T = {"stale_after_hours": 3}


def make_df(last):
    return pd.DataFrame({"city": ["Karachi"], "time": [pd.Timestamp(last, tz="UTC")]})


def test_fresh_data_passes():
    now = pd.Timestamp("2025-06-01 12:00", tz="UTC")
    assert check_staleness(make_df("2025-06-01 11:00"), T, now=now)["status"] == "PASS"


def test_old_data_warns():
    now = pd.Timestamp("2025-06-01 12:00", tz="UTC")
    r = check_staleness(make_df("2025-06-01 06:00"), T, now=now)
    assert r["status"] == "WARN"
    assert r["detail"]["Karachi"] == 6.0