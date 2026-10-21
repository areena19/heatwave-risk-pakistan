"""Tab 4: Model Governance & Performance Slices."""
import json
import pandas as pd
import streamlit as st


def render_governance(metrics_path, model_card_path):
    st.markdown("### 📋 Model Governance, Slicing & Fairness Evaluation")
    metrics = None
    if metrics_path.exists():
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception as exc:
            st.warning(f"Failed to read evaluation metrics: {exc}")

    if metrics is None:
        st.info("Performance metrics report pending. Run `python -m src.model.evaluate`.")
        return

    mae, base = metrics.get("test_mae"), metrics.get("baseline_mae")
    cov = metrics.get("coverage_80")

    m1, m2, m3 = st.columns(3)
    if mae is not None and base:
        gain = (base - mae) / base * 100
        m1.metric("Test MAE (Quantile Model)", f"{mae:.3f}°C", f"{gain:+.1f}% vs Baseline")
        m2.metric("Persistence Baseline MAE", f"{base:.3f}°C")
    if cov is not None:
        m3.metric("Conformal 80% Coverage", f"{(cov * 100 if cov <= 1 else cov):.1f}%", "Nominal 80.0%", delta_color="off")

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        rows_city = metrics.get("by_city")
        if rows_city:
            st.markdown("##### 🏙️ Sub-Group Evaluation: Error by City")
            df_c = pd.DataFrame(rows_city)
            num_cols = [c for c in ("mae", "baseline_mae") if c in df_c.columns]
            if num_cols:
                st.bar_chart(df_c.set_index(df_c.columns[0])[num_cols], height=250)
            st.dataframe(df_c, hide_index=True, use_container_width=True)

    with c2:
        rows_season = metrics.get("by_season")
        if rows_season:
            st.markdown("##### 🌦️ Temporal Evaluation: Error by Season")
            df_s = pd.DataFrame(rows_season)
            num_cols = [c for c in ("mae", "baseline_mae") if c in df_s.columns]
            if num_cols:
                st.bar_chart(df_s.set_index(df_s.columns[0])[num_cols], height=250)
            st.dataframe(df_s, hide_index=True, use_container_width=True)

    if model_card_path.exists() and model_card_path.stat().st_size > 0:
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        with st.expander("📄 Official Model Card (model_card.md)"):
            st.markdown(model_card_path.read_text(encoding="utf-8"))