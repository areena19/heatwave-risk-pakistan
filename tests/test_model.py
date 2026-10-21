import json
import os
import pickle

from src.model.calibrate import get_bounds
from src.model.train import load_data, split_by_date


def test_artifacts_exist():
    assert os.path.exists("data/models/heatwave_quantile_models.pkl")
    assert os.path.exists("data/models/conformal_q.json")


def test_interval_order_and_no_target_leak():
    with open("data/models/heatwave_quantile_models.pkl", "rb") as f:
        art = pickle.load(f)
    with open("data/models/conformal_q.json") as f:
        q = json.load(f)["q"]
    feats = art["features"]
    assert "target" not in feats

    _, _, test = split_by_date(load_data())
    p10, p50, p90 = get_bounds(art["models"], feats, test)
    lo, hi = p10 - q, p90 + q
    assert (lo <= hi).all()
    assert ((lo <= p50) & (p50 <= hi)).all()