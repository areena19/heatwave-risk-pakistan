import json
import os
from datetime import datetime, timezone

LOG_PATH = "reports/quality_log.jsonl"
REPORT_PATH = "reports/dq_report.json"


def log_decision(rule, action, reason, rows_affected, path=LOG_PATH):
    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "rule": rule,
        "action": action,
        "reason": reason,
        "rows_affected": int(rows_affected),
    }
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_log(path=LOG_PATH):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def overall(results):
    statuses = {r["status"] for r in results}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def write_report(results, path=REPORT_PATH):
    report = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall": overall(results),
        "checks": results,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2,
                  default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return report