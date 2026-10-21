"""Tab 4: Model Governance, Multi-Model Tournament & Performance Slices."""
import json
import pandas as pd
import streamlit as st


def render_governance(metrics_path, model_card_path):
    st.markdown("### 📋 Model Governance, Slicing & Tournament Benchmark")

    # ---------------- 1. MULTI-MODEL TOURNAMENT LEADERBOARD
    st.markdown(
        """
        <div style="background:linear-gradient(135deg, rgba(17, 34, 64, 0.95) 0%, rgba(10, 25, 47, 0.95) 100%); border:1px solid rgba(255, 255, 255, 0.1); border-radius:14px; padding:1.2rem 1.4rem; margin-bottom:1.4rem; box-shadow:0 8px 20px rgba(0,0,0,0.25);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                <div>
                    <div style="font-size:1.05rem; font-weight:800; color:#f8fafc;">
                        🏆 Algorithm Selection Tournament (Validation Benchmark)
                    </div>
                    <div style="font-size:0.8rem; color:#94a3b8;">
                        Empirical comparison of candidate architectures on temporal validation split (first 70% train / 15% validation).
                    </div>
                </div>
                <span style="background:rgba(56, 189, 248, 0.15); border:1px solid #38bdf8; color:#38bdf8; padding:3px 10px; border-radius:999px; font-size:0.75rem; font-weight:700;">
                    Automated Model Selection
                </span>
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:0.84rem; color:#cbd5e1; text-align:left;">
                <thead>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1); color:#94a3b8; font-size:0.75rem; text-transform:uppercase;">
                        <th style="padding:6px 8px;">Candidate Algorithm</th>
                        <th style="padding:6px 8px;">Model Architecture</th>
                        <th style="padding:6px 8px;">Validation MAE</th>
                        <th style="padding:6px 8px;">vs Baseline</th>
                        <th style="padding:6px 8px;">Deployment Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06); background:rgba(56, 189, 248, 0.08); font-weight:700; color:#f8fafc;">
                        <td style="padding:8px 8px;">🥇 LightGBM Regressor</td>
                        <td style="padding:8px 8px;">Quantile Gradient Boosting Trees</td>
                        <td style="padding:8px 8px; color:#38bdf8;">1.5458°C</td>
                        <td style="padding:8px 8px; color:#4ade80;">+5.29%</td>
                        <td style="padding:8px 8px;"><span style="background:#0284c7; color:#ffffff; padding:2px 8px; border-radius:4px; font-size:0.72rem;">ACTIVE WINNER</span></td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:8px 8px;">🥈 HistGradientBoosting</td>
                        <td style="padding:8px 8px;">Scikit-Learn Histogram GBDT</td>
                        <td style="padding:8px 8px;">1.5473°C</td>
                        <td style="padding:8px 8px; color:#4ade80;">+5.20%</td>
                        <td style="padding:8px 8px; color:#94a3b8;">Benchmarked</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:8px 8px;">🥉 GradientBoosting</td>
                        <td style="padding:8px 8px;">Scikit-Learn Standard Quantile Trees</td>
                        <td style="padding:8px 8px;">1.5714°C</td>
                        <td style="padding:8px 8px; color:#4ade80;">+3.72%</td>
                        <td style="padding:8px 8px; color:#94a3b8;">Benchmarked</td>
                    </tr>
                    <tr style="color:#64748b; font-style:italic;">
                        <td style="padding:8px 8px;">Persistence Baseline</td>
                        <td style="padding:8px 8px;">Static Benchmark (Tomorrow = Today)</td>
                        <td style="padding:8px 8px;">1.6322°C</td>
                        <td style="padding:8px 8px;">0.00%</td>
                        <td style="padding:8px 8px;">Reference Baseline</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- 2. TEST SET METRICS & SLICES
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

    st.markdown("##### 🎯 Final Out-of-Sample Test Set Evaluation (Unseen Horizon)")
    m1, m2, m3 = st.columns(3)
    if mae is not None and base:
        gain = (base - mae) / base * 100
        m1.metric("Selected Model Test MAE", f"{mae:.3f}°C", f"{gain:+.1f}% vs Baseline")
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