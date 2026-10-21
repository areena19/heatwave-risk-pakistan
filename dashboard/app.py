"""Heatwave Risk Prediction & Climate Intelligence Platform - Streamlit dashboard.

Run from the project root with the venv active:
    streamlit run dashboard/app.py
"""
from __future__ import annotations

import json
import os
import pickle
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent
if not (ROOT / "data").exists():
    ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # train.load_data() and the RAG module use relative paths

DB_PATH = ROOT / "data" / "warehouse" / "heatwave.duckdb"
MODEL_PATH = ROOT / "data" / "models" / "heatwave_quantile_models.pkl"
CONFORMAL_PATH = ROOT / "data" / "models" / "conformal_q.json"
EVIDENCE_INDEX = ROOT / "data" / "processed" / "evidence_chunks.pkl"
MANIFEST_PATH = ROOT / "manifest.csv"
METRICS_PATH = ROOT / "reports" / "metrics.json"
MODEL_CARD_PATH = ROOT / "reports" / "model_card.md"
DQ_REPORT_PATH = ROOT / "reports" / "dq_report.md"
LAST_RUN_PATH = ROOT / "logs" / "last_run.json"

CITY_CANDIDATES = ["city"]
DATE_CANDIDATES = ["date", "day", "ds"]
HI_CANDIDATES = ["max_hi", "heat_index_max", "hi_max", "heat_index", "hi"]
FRESH_HOURS = 3  # a source is "late" if its last fetch is older than this

EMERGENCY_NOTE = (
    "This is information, not professional advice. In an emergency, contact local emergency services."
)

st.set_page_config(page_title="Heatwave Risk Platform", page_icon=":thermometer:", layout="wide")

st.markdown(
    """
<style>
.block-container {padding-top: 1.2rem; max-width: 1200px;}
.hero {background: linear-gradient(120deg,#0b2545 0%,#13315c 55%,#8d2f1f 100%); color:#fff;
       padding:1.4rem 1.6rem; border-radius:14px; margin-bottom:1rem;}
.hero h1 {margin:0; font-size:1.7rem; color:#fff;}
.hero p {margin:.3rem 0 0 0; color:#dbe4ee; font-size:.95rem;}
.card {background:#f6f8fb; border:1px solid #dde3ea; border-radius:12px; padding:.9rem 1.1rem; color:#1b2a3a;}
.card b {color:#0b2545;}
.footer {font-size:.8rem; color:#6b7a8a; border-top:1px solid #e1e6ec; margin-top:2rem; padding-top:.6rem;}
</style>
<div class="hero"><h1>Heatwave Risk Prediction &amp; Climate Intelligence</h1>
<p>Checked weather data, quantile forecasts with an uncertainty range, and evidence-cited guidance.</p></div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- helpers
def pick(columns, candidates):
    lower = {str(c).lower(): c for c in columns}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    return None


@st.cache_data(ttl=60, show_spinner=False)
def query_df(sql: str) -> pd.DataFrame:
    """Short-lived read-only connection so the pipeline can keep writing."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()


def norm_quantile(key):
    m = re.search(r"\d*\.?\d+", str(key))
    if not m:
        return None
    v = float(m.group())
    return v / 100 if v > 1 else v


@st.cache_resource(ttl=300, show_spinner=False)
def load_model_bundle():
    """Returns (bundle, error). bundle = {'models': {0.1|0.5|0.9: model}, 'features': [...]}."""
    if not MODEL_PATH.exists():
        return None, f"Model file not found: {MODEL_PATH.name}. Run the training step first; no numbers are shown until then."
    try:
        try:
            import joblib
            raw = joblib.load(MODEL_PATH)
        except Exception:
            with open(MODEL_PATH, "rb") as f:
                raw = pickle.load(f)
    except Exception as exc:  # e.g. lightgbm not installed
        return None, f"Could not load the model ({type(exc).__name__}: {exc}). Only load files you created yourself."
    if not isinstance(raw, dict) or "models" not in raw or "features" not in raw:
        return None, "Unexpected model file layout (expected a dict with 'models' and 'features')."

    models = {}
    for k, v in raw["models"].items():
        q = norm_quantile(k)
        if q is not None and hasattr(v, "predict"):
            models[round(q, 2)] = v
    if not all(q in models for q in (0.1, 0.5, 0.9)):
        return None, f"Need 10th, 50th and 90th percentile models; found {sorted(models)}."
    return {"models": models, "features": [str(f) for f in raw["features"]]}, None


@st.cache_data(ttl=300, show_spinner=False)
def load_feature_frame():
    """Same frame the model was trained on (adds city_code, hum_chg, pres_chg) plus split boundaries."""
    from src.model.train import load_data, split_by_date
    df = load_data()
    tr, va, _ = split_by_date(df)
    return df, tr["date"].max(), va["date"].max()


# ---------------------------------------------------------------- data guard
if not DB_PATH.exists():
    st.error(f"Warehouse not found at {DB_PATH}. Run the data build first.")
    st.stop()

try:
    gf = query_df("SELECT * FROM gold_features")
except Exception as exc:
    st.error(f"Could not read gold_features: {exc}")
    st.stop()

city_col = pick(gf.columns, CITY_CANDIDATES)
date_col = pick(gf.columns, DATE_CANDIDATES)
hi_col = pick(gf.columns, HI_CANDIDATES)
if not city_col or not date_col:
    st.error(f"Could not find city/date columns in gold_features. Columns: {list(gf.columns)}")
    st.stop()

cities = sorted(gf[city_col].dropna().unique().tolist())
city = st.sidebar.selectbox("City", cities)
st.sidebar.caption("Data comes from the warehouse; it lags real time by design.")

sub = gf[gf[city_col] == city].sort_values(date_col)
latest = sub.iloc[-1]
latest_date = str(pd.to_datetime(latest[date_col]).date())
row_id = str(latest["row_id"]) if "row_id" in sub.columns else f"{city}:{latest_date}"
baseline_val = float(latest[hi_col]) if hi_col and pd.notna(latest[hi_col]) else None

tab1, tab2, tab3, tab4 = st.tabs(
    ["Risk & Uncertainty Forecaster", "Climate Intelligence (RAG)", "Warehouse & Data Quality", "Model Card & Slices"]
)

# ---------------------------------------------------------------- tab 1
with tab1:
    st.subheader(f"Next-day max heat index: {city}")
    bundle, err = load_model_bundle()
    if err:
        st.warning(err)
    else:
        try:
            from src.model.calibrate import get_bounds
            df_all, train_end, val_end = load_feature_frame()
        except Exception as exc:
            st.error(f"Could not load the training code or data: {type(exc).__name__}: {exc}")
            st.stop()

        cdf = df_all[df_all["city"] == city].sort_values("date")
        dates = cdf["date"].tolist()[::-1]
        chosen = st.selectbox(
            "Day (the model predicts the NEXT day from this day's features)",
            dates, key=f"day_{city}", format_func=lambda d: str(pd.Timestamp(d).date()),
        )
        row = cdf[cdf["date"] == chosen].copy()
        today_hi = float(row["max_hi"].iloc[0])
        if st.checkbox("What-if: override today's max heat index (other features stay as observed)", key=f"ovr_{city}"):
            today_hi = st.number_input("Today's max heat index (C)", value=today_hi, format="%.1f", key=f"hi_{city}")
            row["max_hi"] = today_hi

        try:
            p10, p50, p90 = [float(x[0]) for x in get_bounds(bundle["models"], bundle["features"], row)]
        except Exception as exc:
            st.error(f"get_bounds failed: {type(exc).__name__}: {exc}")
            st.stop()

        if CONFORMAL_PATH.exists():
            q = json.loads(CONFORMAL_PATH.read_text())["q"]
            lo, hi, note = p10 - q, p90 + q, "calibrated 80% range"
        else:
            lo, hi, note = p10, p90, "UNCALIBRATED range (conformal_q.json missing)"

        c1, c2, c3 = st.columns(3)
        c1.metric("Median forecast", f"{p50:.1f}", f"{p50 - today_hi:+.1f} vs baseline")
        c2.metric(note, f"{lo:.1f} to {hi:.1f}")
        c3.metric("Baseline (tomorrow = today)", f"{today_hi:.1f}")

        d = pd.Timestamp(chosen)
        block = "training" if d <= train_end else ("validation" if d <= val_end else "test")
        actual = float(row["target"].iloc[0])
        st.caption(
            f"Row {city}:{d.date()} | actual next-day value (already known): {actual:.1f} | "
            f"this day is in the {block} period."
        )
        if block == "training":
            st.caption("Predictions on training days look better than real performance; see the Model Card tab for test results.")
        st.caption(
            "The range is a nominal 80% interval, not a guarantee. Risk categories are not shown until thresholds "
            "are verified against an official source."
        )
        st.warning(
            "This is not a live forecast for tomorrow. The newest day has no feature row in gold_features yet, "
            "so a live forecast needs the lags step extended (a later change)."
        )

# ---------------------------------------------------------------- tab 2
with tab2:
    st.subheader("Ask about heat action plans and guidelines")
    st.markdown(
        f"<div class='card'>Latest stored row: <b>{row_id}</b>"
        f"{'' if baseline_val is None else f' (max heat index {baseline_val:.1f} on {latest_date})'}. "
        "Guidance comes only from the indexed documents.</div>",
        unsafe_allow_html=True,
    )
    if not EVIDENCE_INDEX.exists():
        st.warning("Evidence index not built yet. Run: python -m src.rag.ingest")

    @st.cache_resource(ttl=300, show_spinner=False)
    def load_agent():
        try:
            from src.rag.answer import InsightAgent
            return InsightAgent(), None
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"

    agent, agent_err = load_agent()
    if agent_err:
        st.error(f"RAG module could not be loaded: {agent_err}")
    else:
        st.session_state.setdefault("chat", [])
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander("Sources"):
                        for s in msg["sources"]:
                            st.markdown(f"- {s}")
        prompt = st.chat_input("e.g. What precautions should outdoor workers take during a heatwave?")
        if prompt:
            st.session_state.chat.append({"role": "user", "content": prompt})
            sources = []
            try:
                res = agent.generate_answer(prompt)
                text = getattr(res, "text", res)
                text = str(text) if text else "I don't know"
                try:
                    for h in agent.retriever.retrieve(prompt, top_k=3):
                        sources.append(f"{h['source']}, p. {h['page']} (similarity {h['score']:.2f})")
                except Exception:
                    pass
            except Exception as exc:
                text = f"The agent failed: {type(exc).__name__}: {exc}"
            text += f"\n\n*{EMERGENCY_NOTE}*"
            st.session_state.chat.append({"role": "assistant", "content": text, "sources": sources})
            st.rerun()

# ---------------------------------------------------------------- tab 3
with tab3:
    st.subheader("Warehouse overview")
    try:
        tables = query_df("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY 1")["table_name"].tolist()
        counts = [{"table": t, "rows": int(query_df(f'SELECT COUNT(*) AS n FROM "{t}"')["n"][0])} for t in tables]
        st.dataframe(pd.DataFrame(counts), hide_index=True)
    except Exception as exc:
        tables = []
        st.error(f"Could not list tables: {exc}")

    if "gold_daily" in tables:
        gd = query_df("SELECT * FROM gold_daily")
        gc, gdte = pick(gd.columns, CITY_CANDIDATES), pick(gd.columns, DATE_CANDIDATES)
        if gc and gdte:
            cov = gd.groupby(gc)[gdte].agg(first_day="min", last_day="max", days="count").reset_index()
            st.markdown("**Coverage per city (gold_daily)**")
            st.dataframe(cov, hide_index=True)

    st.subheader("Data freshness")
    if MANIFEST_PATH.exists():
        m = pd.read_csv(MANIFEST_PATH)
        tcol = pick(m.columns, ["fetched_at_utc", "fetch_timestamp_utc"])
        scol = pick(m.columns, ["source", "source_id"])
        if tcol and scol:
            m[tcol] = pd.to_datetime(m[tcol], utc=True, errors="coerce")
            g = m.groupby(scol)[tcol].max().reset_index()
            g["age_hours"] = ((pd.Timestamp.now(tz="UTC") - g[tcol]).dt.total_seconds() / 3600).round(1)
            g["late"] = g["age_hours"] > FRESH_HOURS
            g.columns = ["source", "last_fetch_utc", "age_hours", "late"]
            st.dataframe(g, hide_index=True)
            st.caption(f"A source is flagged late when its last fetch is older than {FRESH_HOURS} hours.")
    else:
        st.info("manifest.csv not found.")

    st.subheader("Last pipeline run")
    if LAST_RUN_PATH.exists():
        try:
            st.json(json.loads(LAST_RUN_PATH.read_text(encoding="utf-8")))
        except Exception as exc:
            st.warning(f"Could not read {LAST_RUN_PATH.name}: {exc}")
    else:
        st.info("No run recorded yet (logs/last_run.json is missing).")

    st.subheader("Data Quality Agent")
    if "quality_log" in tables:
        ql = query_df("SELECT * FROM quality_log")
        acol = pick(ql.columns, ["action"])
        if acol:
            st.dataframe(ql[acol].value_counts().rename_axis("action").reset_index(name="decisions"), hide_index=True)
        st.dataframe(ql.tail(50), hide_index=True)
    else:
        st.info("No quality_log table in the warehouse yet; the agent's decisions have not been logged.")
    if DQ_REPORT_PATH.exists() and DQ_REPORT_PATH.stat().st_size > 0:
        with st.expander("dq_report.md"):
            st.markdown(DQ_REPORT_PATH.read_text(encoding="utf-8"))

# ---------------------------------------------------------------- tab 4
with tab4:
    st.subheader("Model card and performance slices")
    metrics = None
    if METRICS_PATH.exists():
        try:
            metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            st.warning(f"Could not read metrics.json: {exc}")
    if metrics is None:
        st.info(
            "No saved evaluation yet (reports/metrics.json). This tab only displays results written by evaluate.py; "
            "it never re-scores the test set."
        )
    else:
        mae, base = metrics.get("test_mae"), metrics.get("baseline_mae")
        cov = metrics.get("coverage_80")
        c1, c2, c3 = st.columns(3)
        if mae is not None and base:
            c1.metric("Test MAE (model)", f"{mae:.3f}", f"{(base - mae) / base * 100:+.1f}% vs baseline")
            c2.metric("Test MAE (baseline)", f"{base:.3f}")
        if cov is not None:
            c3.metric("80% interval coverage", f"{(cov * 100 if cov <= 1 else cov):.1f}%", "nominal 80%", delta_color="off")
        for key, title in (("by_city", "Error by city"), ("by_season", "Error by season")):
            rows = metrics.get(key)
            if rows:
                df = pd.DataFrame(rows)
                st.markdown(f"**{title}**")
                st.dataframe(df, hide_index=True)
                name_col = df.columns[0]
                num = [c for c in ("mae", "baseline_mae") if c in df.columns]
                if num:
                    st.bar_chart(df.set_index(name_col)[num])
    if MODEL_CARD_PATH.exists() and MODEL_CARD_PATH.stat().st_size > 0:
        with st.expander("model_card.md", expanded=metrics is None):
            st.markdown(MODEL_CARD_PATH.read_text(encoding="utf-8"))

st.markdown(
    f"<div class='footer'>Weather data by Open-Meteo.com and NASA POWER. Gridded model values, not thermometer readings. "
    f"{EMERGENCY_NOTE}</div>",
    unsafe_allow_html=True,
)