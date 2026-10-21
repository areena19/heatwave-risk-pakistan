from src.model.risk import risk_level, risk_from_forecast


def test_levels():
    assert risk_level(20) == "Normal"
    assert risk_level(27) == "Caution"
    assert risk_level(35) == "Extreme Caution"
    assert risk_level(45) == "Danger"
    assert risk_level(60) == "Extreme Danger"


def test_worst_case_can_be_higher():
    r = risk_from_forecast(38, 40, 43)
    assert r["expected"] == "Extreme Caution"
    assert r["worst_case"] == "Danger"