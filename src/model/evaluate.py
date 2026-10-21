import json
import os
import pickle

import numpy as np

from src.model.calibrate import get_bounds
from src.model.train import load_data, split_by_date, mae

SEASONS = {12: "Winter", 1: "Winter", 2: "Winter",
           3: "Spring", 4: "Spring", 5: "Spring",
           6: "Summer", 7: "Summer", 8: "Summer",
           9: "Autumn", 10: "Autumn", 11: "Autumn"}
METRICS_PATH = "reports/metrics.json"
CARD_PATH = "reports/model_card.md"


def slice_table(df, col):
    g = df.groupby(col).agg(mae=("err_model", "mean"),
                            baseline_mae=("err_base", "mean"),
                            coverage_80=("covered", "mean"),
                            rows=("err_model", "size")).round(4)
    return g.reset_index().to_dict(orient="records")


def write_model_card(m, feats):
    def rows(items, key):
        out = ["| " + key + " | MAE | Baseline MAE | 80% coverage | Rows |",
               "|---|---|---|---|---|"]
        for r in items:
            out.append(f"| {r[key]} | {r['mae']} | {r['baseline_mae']} | "
                       f"{r['coverage_80'] * 100:.1f}% | {r['rows']} |")
        return "\n".join(out)

    gain = (m["baseline_mae"] - m["test_mae"]) / m["baseline_mae"] * 100
    card = f"""# Model Card: Next-day Max Heat Index

## Model
- Algorithm: LightGBM quantile regression (10th, 50th, 90th percentile).
- Target: next-day maximum heat index (C), learned as the change from today's max heat index.
- Interval: 10th to 90th percentile widened by a conformal margin, nominal 80%.
- Cities: Karachi, Lahore, Multan, Jacobabad.
- Features ({len(feats)}): {", ".join(feats)}.

## Data and split
- Source: gold_features table (Open-Meteo, checked by the Data Quality Agent).
- Split by date: train 70%, validation 15%, test 15%.
- Test window: {m['test_start']} to {m['test_end']} ({m['test_rows']} rows).

## Test results
| Metric | Value |
|---|---|
| Model MAE | {m['test_mae']} |
| Baseline MAE (tomorrow = today) | {m['baseline_mae']} |
| Improvement over baseline | {gain:.1f}% |
| Calibrated 80% interval coverage | {m['coverage_80'] * 100:.1f}% |
| Raw interval coverage | {m['raw_coverage'] * 100:.1f}% |
| Average interval width (C) | {m['interval_width']} |

## Slices
{rows(m['by_city'], 'city')}

{rows(m['by_season'], 'season')}

## Limitations
- The gain over the persistence baseline is small. Treat the median forecast as a modest improvement, not a large one.
- The test window covers only some seasons (see the season table). It does not represent a full year.
- Coverage is above the nominal 80%, so intervals are on the wide side.
- Risk levels are placeholders based on US NWS heat index bands, not PMD/NDMA thresholds.
- Values are gridded model data, not thermometer readings.
- The data is historical, so the forecast is not live for tomorrow.
"""
    os.makedirs("reports", exist_ok=True)
    with open(CARD_PATH, "w", encoding="utf-8") as f:
        f.write(card)


def evaluate():
    with open("data/models/heatwave_quantile_models.pkl", "rb") as f:
        art = pickle.load(f)
    models, feats = art["models"], art["features"]
    with open("data/models/conformal_q.json") as f:
        q = json.load(f)["q"]

    _, _, test = split_by_date(load_data())
    y = test["target"].values
    p10, p50, p90 = get_bounds(models, feats, test)
    lo, hi = p10 - q, p90 + q

    test = test.assign(err_model=np.abs(y - p50),
                       err_base=np.abs(y - test["baseline_pred"]),
                       covered=(y >= lo) & (y <= hi),
                       season=test["month"].map(SEASONS))

    metrics = {
        "test_rows": int(len(test)),
        "test_mae": round(mae(y, p50), 4),
        "baseline_mae": round(mae(y, test["baseline_pred"]), 4),
        "coverage_80": round(float(test["covered"].mean()), 4),
        "raw_coverage": round(float(np.mean((y >= p10) & (y <= p90))), 4),
        "interval_width": round(float(np.mean(hi - lo)), 2),
        "test_start": str(test["date"].min().date()),
        "test_end": str(test["date"].max().date()),
        "by_city": slice_table(test, "city"),
        "by_season": slice_table(test, "season"),
    }

    os.makedirs("reports", exist_ok=True)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Test rows: {metrics['test_rows']}  ({metrics['test_start']} to {metrics['test_end']})")
    print(f"Baseline MAE: {metrics['baseline_mae']}")
    print(f"Model MAE:    {metrics['test_mae']}")
    print(f"Calibrated coverage: {metrics['coverage_80'] * 100:.1f}%  width {metrics['interval_width']}")
    print("\nBy city:", metrics["by_city"])
    print("\nBy season:", metrics["by_season"])

    write_model_card(metrics, feats)
    print("\nSaved:", METRICS_PATH)
    print("Saved:", CARD_PATH)


if __name__ == "__main__":
    evaluate()