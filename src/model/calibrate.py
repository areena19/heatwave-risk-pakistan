import json
import pickle

import numpy as np

from src.model.train import load_data, split_by_date


def get_bounds(models, feats, df):
    base = df["max_hi"].values
    p10 = base + models[0.10].predict(df[feats])
    p50 = base + models[0.50].predict(df[feats])
    p90 = base + models[0.90].predict(df[feats])
    return p10, p50, p90


def main():
    with open("data/models/heatwave_quantile_models.pkl", "rb") as f:
        art = pickle.load(f)
    models, feats = art["models"], art["features"]

    _, val, _ = split_by_date(load_data())
    y = val["target"].values
    p10, p50, p90 = get_bounds(models, feats, val)

    before = np.mean((y >= p10) & (y <= p90)) * 100
    print(f"Before: coverage {before:.1f}%  width {np.mean(p90 - p10):.2f}")

    scores = np.maximum(p10 - y, y - p90)
    n = len(scores)
    level = min(1.0, np.ceil((n + 1) * 0.80) / n)
    q = float(np.quantile(scores, level))

    lo, hi = p10 - q, p90 + q
    after = np.mean((y >= lo) & (y <= hi)) * 100
    print(f"q = {q:.3f}")
    print(f"After:  coverage {after:.1f}%  width {np.mean(hi - lo):.2f}")

    with open("data/models/conformal_q.json", "w") as f:
        json.dump({"q": q}, f)
    print("Saved: data/models/conformal_q.json")


if __name__ == "__main__":
    main()