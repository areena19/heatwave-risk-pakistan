import json
import pickle
import pandas as pd

from src.model.calibrate import get_bounds
from src.model.risk import risk_from_forecast
from src.model.train import load_data


def forecast_latest():
    with open("data/models/heatwave_quantile_models.pkl", "rb") as f:
        art = pickle.load(f)
    with open("data/models/conformal_q.json") as f:
        q = json.load(f)["q"]

    df = load_data()
    latest = df.sort_values("date").groupby("city").tail(1).copy()
    p10, p50, p90 = get_bounds(art["models"], art["features"], latest)
    latest["lo"], latest["p50"], latest["hi"] = p10 - q, p50, p90 + q

    rows = []
    for _, r in latest.iterrows():
        risk = risk_from_forecast(r["lo"], r["p50"], r["hi"])
        # Next day / tomorrow ki date
        tomorrow_date = (pd.to_datetime(r["date"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        rows.append({
            "city": r["city"],
            "input_features_from": str(r["date"].date()),
            "forecast_for_date": f"{tomorrow_date} (Tomorrow)",
            "lo": round(float(r["lo"]), 1),
            "p50": round(float(r["p50"]), 1),
            "hi": round(float(r["hi"]), 1),
            **risk,
        })
    return rows


if __name__ == "__main__":
    for row in forecast_latest():
        print(row)