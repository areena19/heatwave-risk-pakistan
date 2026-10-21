import yaml


def load_levels():
    with open("config/thresholds.yaml") as f:
        levels = yaml.safe_load(f)["risk_levels"]
    return sorted(levels, key=lambda x: x["min_hi_c"])


def risk_level(hi_value, levels=None):
    levels = levels or load_levels()
    name = levels[0]["name"]
    for lv in levels:
        if hi_value >= lv["min_hi_c"]:
            name = lv["name"]
    return name


def risk_from_forecast(lo, p50, hi):
    levels = load_levels()
    return {
        "expected": risk_level(p50, levels),
        "worst_case": risk_level(hi, levels),
    }