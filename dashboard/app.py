"""PakHeat Climate Risk & Forecast Intelligence Platform - Main Application."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

# Environment & Paths
ROOT = Path(__file__).resolve().parent
if not (ROOT / "data").exists():
    ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dashboard.styles import CUSTOM_CSS
from dashboard.tabs.forecaster import render_forecaster
from dashboard.tabs.governance import render_governance
from dashboard.tabs.rag import render_rag
from dashboard.tabs.warehouse import render_warehouse

# Constants
DB_PATH = ROOT / "data" / "warehouse" / "heatwave.duckdb"
MODEL_PATH = ROOT / "data" / "models" / "heatwave_quantile_models.pkl"
CONFORMAL_PATH = ROOT / "data" / "models" / "conformal_q.json"
EVIDENCE_INDEX = ROOT / "data" / "processed" / "evidence_chunks.pkl"
MANIFEST_PATH = ROOT / "manifest.csv"
METRICS_PATH = ROOT / "reports" / "metrics.json"
MODEL_CARD_PATH = ROOT / "reports" / "model_card.md"
DQ_REPORT_PATH = ROOT / "reports" / "dq_report.md"

st.set_page_config(page_title="PakHeat Climate Risk Platform", page_icon="🌡️", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=60, show_spinner=False)
def query_df(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()


# Guard
if not DB_PATH.exists():
    st.error(f"🚨 Warehouse missing at `{DB_PATH}`. Please run data pipeline first.")
    st.stop()

gf = query_df("SELECT * FROM gold_features")
cities = sorted(gf["city"].dropna().unique().tolist())

# Sidebar
with st.sidebar:
    st.markdown("### 🌐 Operational Scope")
    city = st.selectbox("Monitoring Station", cities, index=0)
    st.markdown("---")
    st.markdown("### ⚙️ Calibration Specs")
    st.info(
        "**Active Engine:** LightGBM  \n*(🏆 3-Model Tournament Winner)*\n\n"
        "**Conformal Guarantee:** 80% nominal\n\n"
        "**Feeds:** Open-Meteo & NASA POWER"
    )

sub = gf[gf["city"] == city].sort_values("date")

# Header Banner
st.markdown(
    f"""
    <div class="brand-banner">
        <div>
            <h1 class="brand-title">PakHeat Climate Risk &amp; Forecasting Platform</h1>
            <div class="brand-subtitle">Automated Early-Warning Engine with Conformal Uncertainty Bounds</div>
        </div>
        <div style="text-align: right;">
            <span class="system-pill"><span class="pulse-dot"></span> Station Active: {city.upper()}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 4 Main Tabs
t1, t2, t3, t4 = st.tabs([
    "📊 Forecaster & Uncertainty",
    "💬 Climate Intelligence (RAG)",
    "🏭 Warehouse & Quality Agent",
    "📋 Model Governance & Slices",
])

with t1:
    from src.model.train import load_data
    import pickle
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    cdf_all = load_data()
    render_forecaster(city, cdf_all, bundle, CONFORMAL_PATH)

with t2:
    render_rag(EVIDENCE_INDEX)

with t3:
    render_warehouse(query_df, MANIFEST_PATH, DQ_REPORT_PATH)

with t4:
    render_governance(METRICS_PATH, MODEL_CARD_PATH)

# Footer
st.markdown(
    """
    <div class="app-footer">
        <div>Weather feeds by <b>Open-Meteo</b> &amp; <b>NASA POWER</b>.</div>
        <div>Official NDMA &amp; WHO Protocol. In emergencies, dial 1122.</div>
    </div>
    """,
    unsafe_allow_html=True,
)