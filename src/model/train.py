import os
import pickle

import duckdb
import numpy as np
import lightgbm as lgb

QUANTILES = [0.10, 0.50, 0.90]
EXCLUDE = ["target", "date", "row_id", "any_jump_flag", "city"]


def load_data():
    con = duckdb.connect("data/warehouse/heatwave.duckdb", read_only=True)
    df = con.execute("SELECT * FROM gold_features ORDER BY date, city").df()
    con.close()
    df["date"] = df["date"].astype("datetime64[ns]")
    # Persistence baseline: kal ka HI = aaj ka HI
    df["baseline_pred"] = df["max_hi"]
    df["city_code"] = df["city"].astype("category").cat.codes
    g = df.sort_values(["city", "date"]).groupby("city")
    df["hum_chg"] = df["mean_humidity"] - g["mean_humidity"].shift(1)
    df["pres_chg"] = df["mean_pressure"] - g["mean_pressure"].shift(1)
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


def run_training():
    df = load_data()
    train, val, test = split_by_date(df)
    feats = get_features(df)
    print("Features:", feats)
    print(f"Rows  train={len(train)}  val={len(val)}  test={len(test)}")

    models = {}
    for q in QUANTILES:
        m = lgb.LGBMRegressor(
            objective="quantile", alpha=q,
            n_estimators=300, learning_rate=0.05,
            num_leaves=15, random_state=42, verbose=-1,
        )
        m.fit(train[feats], train["target"] - train["max_hi"])
        models[q] = m

    val_mae = mae(val["target"], val["max_hi"] + models[0.50].predict(val[feats]))
    val_base = mae(val["target"], val["baseline_pred"])
    print(f"Validation MAE: {val_mae:.4f} | Baseline MAE: {val_base:.4f}")

    if val_mae < val_base:
        os.makedirs("data/models", exist_ok=True)
        with open("data/models/heatwave_quantile_models.pkl", "wb") as f:
            pickle.dump({"models": models, "features": feats}, f)
        print("Model saved.")
    else:
        print("Model did not beat baseline. Not saved.")

    return models, feats, test


if __name__ == "__main__":
    run_training()