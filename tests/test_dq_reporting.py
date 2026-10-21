from src.dq_agent.reporting import log_decision, overall, read_log, write_report


def r(status):
    return {"check": "x", "status": status, "n_bad": 0, "n_total": 1, "detail": {}}


def test_log_has_all_fields(tmp_path):
    p = str(tmp_path / "log.jsonl")
    log_decision("range", "flag", "bad temp", 3, path=p)
    log_decision("gaps", "fill", "gap <= 3h", 2, path=p)
    rows = read_log(p)
    assert len(rows) == 2
    assert set(rows[0]) == {"timestamp_utc", "rule", "action", "reason", "rows_affected"}


def test_overall():
    assert overall([r("PASS")]) == "PASS"
    assert overall([r("PASS"), r("WARN")]) == "WARN"
    assert overall([r("WARN"), r("FAIL")]) == "FAIL"
    assert overall([]) == "PASS"


def test_write_report(tmp_path):
    p = str(tmp_path / "rep.json")
    rep = write_report([r("WARN")], path=p)
    assert rep["overall"] == "WARN"