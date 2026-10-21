import pickle

import numpy as np

from src.model.calibrate import get_bounds
from src.model.train import load_data, split_by_date, mae

RECENT_DAYS = 7
DRIFT_RATIO = 1.5


def check_drift():
    with open("data/models/heatwave_quantile_models.pkl", "rb") as f:
        art = pickle.load(f)
    models, feats = art["models"], art["features"]

    df = load_data()
    _, val, _ = split_by_date(df)

    cutoff = np.sort(df["date"].unique())[-RECENT_DAYS]
    recent = df[df["date"] >= cutoff]

    _, p50_val, _ = get_bounds(models, feats, val)
    _, p50_rec, _ = get_bounds(models, feats, recent)
    val_mae = mae(val["target"], p50_val)
    recent_mae = mae(recent["target"], p50_rec)
    return recent_mae > DRIFT_RATIO * val_mae, val_mae, recent_mae


if __name__ == "__main__":
    drift, val_mae, recent_mae = check_drift()
    print(f"Validation MAE: {val_mae:.3f}")
    print(f"Last {RECENT_DAYS} days MAE: {recent_mae:.3f}")
    print(f"Drift: {drift}")