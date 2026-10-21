import os
import pickle

import duckdb
import numpy as np
import lightgbm as lgb
from sklearn.ensemble import HistGradientBoostingRegressor, GradientBoostingRegressor

QUANTILES = [0.10, 0.50, 0.90]
EXCLUDE = ["target", "date", "row_id", "any_jump_flag", "city"]


def load_data():
    con = duckdb.connect("data/warehouse/heatwave.duckdb", read_only=True)
    df = con.execute("SELECT * FROM gold_features ORDER BY date, city").df()
    con.close()
    df["date"] = df["date"].astype("datetime64[ns]")
    df["baseline_pred"] = df["max_hi"]
    df["city_code"] = df["city"].astype("category").cat.codes
    g = df.sort_values(["city", "date"]).groupby("city")
    # .fillna(0.0) taake GradientBoosting NaN par crash na ho
    df["hum_chg"] = (df["mean_humidity"] - g["mean_humidity"].shift(1)).fillna(0.0)
    df["pres_chg"] = (df["mean_pressure"] - g["mean_pressure"].shift(1)).fillna(0.0)
    return df


def split_by_date(df):
    dates = np.sort(df["date"].unique())
    train_end = dates[int(len(dates) * 0.70)]
    val_end = dates[int(len(dates) * 0.85)]
    train = df[df["date"] < train_end].copy()
    val = df[(df["date"] >= train_end) & (df["date"] < val_end)].copy()
    test = df[df["date"] >= val_end].copy()
    return train, val, test


def get_features(df):
    drop = EXCLUDE + ["baseline_pred"]
    return [c for c in df.columns if c not in drop]


def mae(y, p):
    return float(np.mean(np.abs(np.asarray(y) - np.asarray(p))))


def train_candidate_family(name, train, feats, val):
    """Trains 0.10, 0.50, 0.90 quantiles for a given algorithm and evaluates on validation set."""
    models = {}
    y_train_residual = train["target"] - train["max_hi"]

    # Fill any remaining NaNs safely
    X_train = train[feats].fillna(0.0)
    X_val = val[feats].fillna(0.0)

    for q in QUANTILES:
        if name == "LightGBM":
            m = lgb.LGBMRegressor(
                objective="quantile", alpha=q,
                n_estimators=300, learning_rate=0.05,
                num_leaves=15, random_state=42, verbose=-1,
            )
        elif name == "HistGradientBoosting":
            m = HistGradientBoostingRegressor(
                loss="quantile", quantile=q,
                max_iter=250, learning_rate=0.05,
                max_leaf_nodes=15, random_state=42,
            )
        elif name == "GradientBoosting":
            m = GradientBoostingRegressor(
                loss="quantile", alpha=q,
                n_estimators=150, learning_rate=0.05,
                max_depth=3, random_state=42,
            )
        else:
            raise ValueError(f"Unknown candidate: {name}")

        m.fit(X_train, y_train_residual)
        models[q] = m

    # Evaluate median model (p50) on validation set
    val_pred = val["max_hi"] + models[0.50].predict(X_val)
    val_mae = mae(val["target"], val_pred)
    return models, val_mae


def run_training():
    df = load_data()
    valid_df = df.dropna(subset=["target"]).copy()
    train, val, test = split_by_date(valid_df)
    feats = get_features(df)
    
    print("=" * 60)
    print("🏆 RUNNING MULTI-MODEL TOURNAMENT (MODEL SELECTION)")
    print(f"Features ({len(feats)}):", feats)
    print(f"Dataset Splits: Train={len(train)} | Val={len(val)} | Test={len(test)}")
    print("=" * 60)

    val_base = mae(val["target"], val["baseline_pred"])
    print(f"Persistence Baseline Validation MAE: {val_base:.4f}°C\n")

    candidates = ["LightGBM", "HistGradientBoosting", "GradientBoosting"]
    results = {}

    for cand_name in candidates:
        print(f"⏳ Training {cand_name} (Quantiles: 0.10, 0.50, 0.90)...")
        models, val_mae = train_candidate_family(cand_name, train, feats, val)
        gain = (val_base - val_mae) / val_base * 100
        results[cand_name] = {"models": models, "val_mae": val_mae, "gain": gain}
        print(f"   ↳ {cand_name} Validation MAE: {val_mae:.4f}°C ({gain:+.2f}% vs Baseline)")

    # Find the winning model
    best_cand = min(results.keys(), key=lambda k: results[k]["val_mae"])
    best_models = results[best_cand]["models"]
    best_mae = results[best_cand]["val_mae"]
    best_gain = results[best_cand]["gain"]

    print("\n" + "=" * 60)
    print(f"🥇 TOURNAMENT WINNER: {best_cand}")
    print(f"Best Validation MAE: {best_mae:.4f}°C ({best_gain:+.2f}% vs Baseline)")
    print("=" * 60)

    if best_mae < val_base:
        os.makedirs("data/models", exist_ok=True)
        with open("data/models/heatwave_quantile_models.pkl", "wb") as f:
            pickle.dump({
                "models": best_models,
                "features": feats,
                "selected_algorithm": best_cand,
                "validation_mae": best_mae
            }, f)
        print(f"✅ Winning model artifact successfully saved to data/models/heatwave_quantile_models.pkl")
    else:
        print("❌ No candidate beat the baseline. Model not saved.")

    return best_models, feats, test


if __name__ == "__main__":
    run_training()