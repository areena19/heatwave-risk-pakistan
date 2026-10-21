"""Tab 3: Warehouse Governance & Data Quality Agent."""
import pandas as pd
import streamlit as st


def render_warehouse(query_df, manifest_path, dq_report_path):
    st.markdown("### 🏭 DuckDB Warehouse Topology & Quality Enforcement")
    try:
        tables = query_df("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY 1")["table_name"].tolist()
        counts = [{"Warehouse Table": t, "Row Count": int(query_df(f'SELECT COUNT(*) AS n FROM "{t}"')["n"][0])} for t in tables]

        s1, s2, s3 = st.columns(3)
        total_rows = sum(c["Row Count"] for c in counts)
        s1.metric("Storage Engine", "DuckDB (In-Process)")
        s2.metric("Total Warehouse Tables", len(tables))
        s3.metric("Indexed Records", f"{total_rows:,}")

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        col_t1, col_t2 = st.columns([1, 1.4])
        with col_t1:
            st.markdown("##### 📦 Relational Schemas")
            st.dataframe(pd.DataFrame(counts), hide_index=True, use_container_width=True)

        with col_t2:
            if "gold_daily" in tables:
                st.markdown("##### 📍 Geographic Coverage Span")
                gd = query_df("SELECT * FROM gold_daily")
                cov = gd.groupby("city")["date"].agg(first_record="min", latest_record="max", days="count").reset_index()
                st.dataframe(cov, hide_index=True, use_container_width=True)
    except Exception as exc:
        st.error(f"Warehouse introspection failure: {exc}")

    st.markdown("---")
    st.markdown("#### 🛰️ Data Freshness & Pipeline Latency")
    if manifest_path.exists():
        try:
            m = pd.read_csv(manifest_path)
            if "fetched_at_utc" in m.columns and "source" in m.columns:
                m["fetched_at_utc"] = pd.to_datetime(m["fetched_at_utc"], utc=True, errors="coerce")
                g = m.groupby("source")["fetched_at_utc"].max().reset_index()
                g["Latency (Hours)"] = ((pd.Timestamp.now(tz="UTC") - g["fetched_at_utc"]).dt.total_seconds() / 3600).round(1)
                
                # NASA POWER is on a 24-48 hr satellite validation cycle; Open-Meteo is hourly
                def evaluate_freshness(row):
                    src = str(row["source"]).lower()
                    allowed_latency = 48.0 if "nasa" in src else 8.0
                    return "🟢 FRESH" if row["Latency (Hours)"] <= allowed_latency else "🟡 DELAYED"

                g["Operational Status"] = g.apply(evaluate_freshness, axis=1)
                g.columns = ["Data Feed Stream", "Latest Fetch (UTC)", "Latency (Hours)", "Operational Status"]
                st.dataframe(g, hide_index=True, use_container_width=True)
        except Exception as e:
            st.info(f"Manifest note: {e}")

    if dq_report_path.exists() and dq_report_path.stat().st_size > 0:
        st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
        with st.expander("🛡️ Data Quality Agent Audit Report (dq_report.md)"):
            st.markdown(dq_report_path.read_text(encoding="utf-8"))