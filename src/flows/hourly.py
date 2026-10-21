import os
import subprocess
import sys
from pathlib import Path

import json
from datetime import datetime, timezone

from prefect import flow, task

ROOT = Path(__file__).resolve().parents[2]


def run_module(module):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable, "-m", module],
        cwd=ROOT, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr[-2000:])
        raise RuntimeError(f"{module} failed (exit code {result.returncode})")


@task(retries=2, retry_delay_seconds=30)
def fetch_open_meteo():
    run_module("src.fetch.open_meteo")


@task(retries=2, retry_delay_seconds=30)
def fetch_nasa_power():
    run_module("src.fetch.nasa_power")


@task
def verify_raw():
    run_module("src.fetch.verify")


@task
def clean_hourly():
    run_module("src.clean.clean")


@task
def dq_agent():
    run_module("src.dq_agent.agent")


@task
def build_daily():
    run_module("src.features.daily")


@task
def build_lags():
    run_module("src.features.lags")


@task
def build_warehouse():
    run_module("src.warehouse.build")


@task
def retrain_if_needed():
    run_module("src.model.retrain")


@task
def reindex_docs():
    pdfs = list((ROOT / "data" / "evidence").glob("*.pdf"))
    index = ROOT / "data" / "processed" / "evidence_chunks.pkl"
    if index.exists() and all(p.stat().st_mtime <= index.stat().st_mtime for p in pdfs):
        print("No new documents. Skipping re-index.")
        return
    run_module("src.rag.ingest")

@task
def write_last_run():
    path = ROOT / "logs" / "last_run.json"
    path.parent.mkdir(exist_ok=True)
    info = {"finished_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "success"}
    path.write_text(json.dumps(info, indent=2), encoding="utf-8")

@flow(name="hourly-pipeline", log_prints=True)
def hourly_pipeline():
    fetch_open_meteo()
    fetch_nasa_power()
    verify_raw()
    clean_hourly()
    dq_agent()
    build_daily()
    build_lags()
    build_warehouse()
    retrain_if_needed()
    reindex_docs()
    write_last_run()

if __name__ == "__main__":
    if "--serve" in sys.argv:
        hourly_pipeline.serve(name="hourly-pipeline", cron="5 * * * *")
    else:
        hourly_pipeline()