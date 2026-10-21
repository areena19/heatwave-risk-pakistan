from src.model.predict import forecast_latest

VALID = {"Normal", "Caution", "Extreme Caution", "Danger", "Extreme Danger"}


def test_forecast_shape_and_order():
    rows = forecast_latest()
    assert {r["city"] for r in rows} == {"Karachi", "Lahore", "Multan", "Jacobabad"}
    for r in rows:
        assert r["lo"] <= r["p50"] <= r["hi"]
        assert r["expected"] in VALID
        assert r["worst_case"] in VALID