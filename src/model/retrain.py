import os
import pickle
import shutil

from src.model.calibrate import get_bounds, main as recalibrate
from src.model.drift import check_drift
from src.model.train import load_data, run_training, split_by_date, mae

MODEL = "data/models/heatwave_quantile_models.pkl"
BACKUP = "data/models/heatwave_quantile_models.bak"


def val_mae_of(path):
    with open(path, "rb") as f:
        art = pickle.load(f)
    _, val, _ = split_by_date(load_data())
    _, p50, _ = get_bounds(art["models"], art["features"], val)
    return mae(val["target"], p50)


def main():
    old = None
    if os.path.exists(MODEL):
        drift, val_mae, recent_mae = check_drift()
        print(f"Validation MAE: {val_mae:.3f} | Last 7 days MAE: {recent_mae:.3f}")
        if not drift:
            print("No drift. Keeping current model.")
            return
        print("Drift found. Retraining...")
        shutil.copy(MODEL, BACKUP)
        old = val_mae_of(BACKUP)
    else:
        print("No model found. Training the first model...")

    run_training()

    if not os.path.exists(MODEL):
        print("No model saved (did not beat baseline).")
        return

    new = val_mae_of(MODEL)
    if old is not None and new >= old:
        shutil.copy(BACKUP, MODEL)
        print(f"New model not better ({new:.4f} vs {old:.4f}). Old model restored.")
        return

    recalibrate()
    print(f"New model kept (validation MAE {new:.4f}).")


if __name__ == "__main__":
    main()