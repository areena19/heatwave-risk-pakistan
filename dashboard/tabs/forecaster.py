"""Tab 1: Next-Day Maximum Heat Index Forecaster & Occupational Risk Intelligence (Bento Command Grid)."""
import json
import altair as alt
import pandas as pd
import streamlit as st

# Occupational Safety Protocols based on NDMA & WHO Heat Stress Guidelines
PROTOCOLS = {
    "Normal": {
        "work_rest": "Standard shifts (No mandatory heat breaks)",
        "hydration": "250 ml water every 2 hours",
        "curfew": "No daytime operational restrictions",
        "alert": "Routine conditions. Standard workplace safety monitoring.",
        "color": "#10b981", "badge_bg": "rgba(16, 185, 129, 0.15)", "border": "rgba(16, 185, 129, 0.3)"
    },
    "Caution": {
        "work_rest": "50 min work / 10 min shaded rest per hour",
        "hydration": "500 ml ORS / electrolyte water per hour",
        "curfew": "Provide accessible, ventilated rest stations",
        "alert": "Fatigue possible with prolonged exertion. Monitor elder labor.",
        "color": "#f59e0b", "badge_bg": "rgba(245, 158, 11, 0.15)", "border": "rgba(245, 158, 11, 0.3)"
    },
    "Extreme Caution": {
        "work_rest": "40–45 min work / 15–20 min shaded recovery per hour",
        "hydration": "750 ml to 1 Liter chilled electrolyte water / hour",
        "curfew": "Cease heavy direct-sun labor from 12:00 PM – 3:30 PM",
        "alert": "High risk of Heat Exhaustion & Cramps. Strict enforcement for brick kilns & asphalt/construction crews.",
        "color": "#f97316", "badge_bg": "rgba(249, 115, 22, 0.15)", "border": "rgba(249, 115, 22, 0.35)"
    },
    "Danger": {
        "work_rest": "30 min work / 30 min active cooling rest per hour",
        "hydration": "Minimum 1.2 Liters cool electrolyte fluids per hour",
        "curfew": "Total ban on heavy physical shifts from 11:30 AM – 4:00 PM",
        "alert": "Heatstroke imminent with prolonged labor. Mandatory buddy system active.",
        "color": "#ef4444", "badge_bg": "rgba(239, 68, 68, 0.15)", "border": "rgba(239, 68, 68, 0.35)"
    },
    "Extreme Danger": {
        "work_rest": "Complete cessation of outdoor physical labor",
        "hydration": "Continuous cooling & active medical surveillance",
        "curfew": "All outdoor daytime operations suspended completely",
        "alert": "Life-threatening heatstroke risk. Emergency disaster protocol active.",
        "color": "#dc2626", "badge_bg": "rgba(220, 38, 38, 0.2)", "border": "rgba(220, 38, 38, 0.4)"
    }
}


def render_forecaster(city, cdf_all, bundle, conformal_path):
    from src.model.calibrate import get_bounds
    from src.model.risk import risk_from_forecast

    q_val = json.loads(conformal_path.read_text())["q"] if conformal_path.exists() else 0.0

    # 1. TOP STRIP: Compact National Heatwatch Bar
    all_cities = sorted(cdf_all["city"].dropna().unique().tolist())
    cols = st.columns(len(all_cities))

    for i, c_name in enumerate(all_cities):
        c_latest = cdf_all[cdf_all["city"] == c_name].sort_values("date").iloc[-1:]
        p10_c, p50_c, p90_c = [float(x[0]) for x in get_bounds(bundle["models"], bundle["features"], c_latest)]
        r_c = risk_from_forecast(p10_c - q_val, p50_c, p90_c + q_val)
        exp_c = r_c.get("expected", "Normal")
        
        is_active = (c_name == city)
        border_style = "1.5px solid #38bdf8" if is_active else "1px solid rgba(255, 255, 255, 0.08)"
        bg_style = "linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%)" if is_active else "rgba(15, 23, 42, 0.5)"

        with cols[i]:
            city_card_html = (
                f'<div style="background:{bg_style}; border:{border_style}; border-radius:12px; padding:0.65rem 0.8rem; text-align:center; backdrop-filter:blur(8px);">'
                f'<div style="font-size:0.75rem; font-weight:700; color:{"#38bdf8" if is_active else "#94a3b8"}; text-transform:uppercase; letter-spacing:0.04em;">{c_name} {"📍" if is_active else ""}</div>'
                f'<div style="font-size:1.35rem; font-weight:800; color:#f8fafc; margin:1px 0;">{p50_c:.1f}°C</div>'
                f'<div style="font-size:0.72rem; font-weight:600; color:{"#fb923c" if "Caution" in exp_c else "#34d399"};">{exp_c}</div>'
                f'</div>'
            )
            st.markdown(city_card_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    # 2. FILTER DATA FOR ACTIVE CITY
    city_df = cdf_all[cdf_all["city"] == city].sort_values("date").reset_index(drop=True)
    dates = city_df["date"].tolist()[::-1]

    ctrl_col1, ctrl_col2 = st.columns([2.5, 1])
    with ctrl_col1:
        chosen = st.selectbox(
            f"Select Observation Date for {city.upper()} (Day t features forecast Day t+1):",
            dates,
            key=f"day_{city}",
            format_func=lambda d: f"{pd.Timestamp(d).strftime('%A, %b %d, %Y')} {'[LATEST OBSERVATION]' if d == dates[0] else ''}",
        )
    with ctrl_col2:
        st.write("")
        st.write("")
        sim_active = st.checkbox("🧪 What-If Simulator", key=f"ovr_{city}")

    row = city_df[city_df["date"] == chosen].iloc[0:1].copy()
    today_hi = float(row["max_hi"].iloc[0])
    ambient_temp = float(row["max_temp"].iloc[0]) if "max_temp" in row.columns else today_hi - 3.5
    humidity_val = float(row["mean_humidity"].iloc[0]) if "mean_humidity" in row.columns else 55.0
    wind_val = float(row["mean_wind"].iloc[0]) if "mean_wind" in row.columns else 12.0

    if sim_active:
        today_hi = st.slider("Simulated Heat Index (°C) Override", 20.0, 58.0, today_hi, 0.5)
        row["max_hi"] = today_hi

    # Inference Execution
    p10, p50, p90 = [float(x[0]) for x in get_bounds(bundle["models"], bundle["features"], row)]
    lo, hi = p10 - q_val, p90 + q_val

    risk_info = risk_from_forecast(lo, p50, hi)
    expected_risk = risk_info.get("expected", "Normal")
    proto = PROTOCOLS.get(expected_risk, PROTOCOLS["Caution"])

    tomorrow_dt = pd.to_datetime(chosen) + pd.Timedelta(days=1)
    tomorrow_str = tomorrow_dt.strftime("%A, %B %d, %Y")
    diff = p50 - today_hi
    diff_color = "#f87171" if diff > 0 else "#4ade80"

    # 3. ASYMMETRIC BENTO GRID
    grid_left, grid_right = st.columns([1.5, 1])

    with grid_left:
        # Zero-Indentation Safe HTML for Hero Forecast Card
        hero_html = (
            f'<div style="background:linear-gradient(135deg, rgba(17, 34, 64, 0.95) 0%, rgba(10, 25, 47, 0.95) 100%); border:1px solid rgba(255, 255, 255, 0.1); border-radius:16px; padding:1.4rem 1.6rem; margin-bottom:1.2rem; box-shadow:0 8px 24px rgba(0,0,0,0.3); backdrop-filter:blur(10px);">'
            f'<div style="display:flex; justify-content:space-between; align-items:flex-start;">'
            f'<div>'
            f'<span style="font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#38bdf8;">🎯 Target Variable: Next-Day Maximum Heat Index</span>'
            f'<div style="font-size:1.02rem; font-weight:700; color:#f8fafc; margin-top:2px;">Forecast for Tomorrow: <span style="color:#ffffff; text-decoration:underline decoration-sky-500;">{tomorrow_str}</span></div>'
            f'</div>'
            f'<span style="background:{proto["badge_bg"]}; border:1px solid {proto["border"]}; color:{proto["color"]}; padding:0.35rem 0.9rem; border-radius:999px; font-size:0.8rem; font-weight:800; text-transform:uppercase; letter-spacing:0.04em;">{expected_risk}</span>'
            f'</div>'
            f'<div style="display:flex; align-items:baseline; gap:1.2rem; margin:1.2rem 0 0.8rem 0;">'
            f'<div style="font-size:3.2rem; font-weight:800; color:#ffffff; line-height:1; letter-spacing:-0.03em;">{p50:.1f}°C</div>'
            f'<div>'
            f'<div style="font-size:0.95rem; font-weight:600; color:#94a3b8;">Calibrated 80% Band: <b style="color:#ffffff;">{lo:.1f}° to {hi:.1f}°C</b></div>'
            f'<div style="font-size:0.82rem; font-weight:500; color:{diff_color}; margin-top:2px;">{diff:+.1f}°C vs Today\'s Peak ({today_hi:.1f}°C Baseline)</div>'
            f'</div>'
            f'</div>'
            f'<div style="border-top:1px solid rgba(255, 255, 255, 0.08); padding-top:0.85rem; margin-top:0.9rem; display:flex; justify-content:space-between; font-size:0.82rem; color:#cbd5e1;">'
            f'<span>🌡️ <b>Air Temp:</b> {ambient_temp:.1f}°C</span>'
            f'<span>💧 <b>Humidity:</b> {humidity_val:.1f}% <i>(Vapor Load)</i></span>'
            f'<span>💨 <b>Wind:</b> {wind_val:.1f} km/h</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(hero_html, unsafe_allow_html=True)

        # 30-Day Heat Trajectory Altair Chart
        st.markdown(f"##### 📈 30-Day Heat Trajectory ({city.upper()}) & Tomorrow's Horizon")
        hist_window = city_df[city_df["date"] <= chosen].tail(30).copy()
        hist_chart_data = [
            {"date": pd.Timestamp(r["date"]).strftime("%Y-%m-%d"), "Heat Index": float(r["max_hi"]), "Lower": float(r["max_hi"]), "Upper": float(r["max_hi"]), "Type": "Observed Peak"}
            for _, r in hist_window.iterrows()
        ]
        hist_chart_data.append({"date": tomorrow_dt.strftime("%Y-%m-%d"), "Heat Index": p50, "Lower": lo, "Upper": hi, "Type": "Forecast (Tomorrow)"})

        chart_df = pd.DataFrame(hist_chart_data)
        base = alt.Chart(chart_df).encode(x=alt.X("date:T", title="Timeline", axis=alt.Axis(format="%b %d", labelAngle=-30, tickCount=15, labelColor="#94a3b8", titleColor="#94a3b8")))
        band = base.mark_area(opacity=0.3, color="#f97316").encode(y=alt.Y("Lower:Q", scale=alt.Scale(zero=False), title="Max Heat Index (°C)", axis=alt.Axis(labelColor="#94a3b8", titleColor="#94a3b8")), y2="Upper:Q")
        line = base.mark_line(strokeWidth=3).encode(y="Heat Index:Q", color=alt.Color("Type:N", scale=alt.Scale(domain=["Observed Peak", "Forecast (Tomorrow)"], range=["#38bdf8", "#fb923c"]), legend=alt.Legend(orient="top", title=None, labelColor="#f8fafc")))
        points = base.mark_circle(size=60).encode(y="Heat Index:Q", color=alt.Color("Type:N", scale=alt.Scale(domain=["Observed Peak", "Forecast (Tomorrow)"], range=["#38bdf8", "#fb923c"])))

        st.altair_chart((band + line + points).properties(height=310).interactive(), use_container_width=True)

    with grid_right:
        # Zero-Indentation Safe HTML for Decision Support Hub
        right_html = (
            f'<div style="background:rgba(15, 23, 42, 0.7); border:1px solid rgba(255, 255, 255, 0.08); border-radius:16px; padding:1.3rem 1.4rem; backdrop-filter:blur(10px); height:100%;">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:0.6rem;">'
            f'<span style="font-size:0.95rem; font-weight:800; color:#f8fafc;">👷 Mandatory Labor Protocols</span>'
            f'<span style="font-size:0.75rem; color:#94a3b8; font-weight:600;">NDMA / WHO Guidelines</span>'
            f'</div>'
            f'<div style="display:flex; flex-direction:column; gap:0.75rem;">'
            f'<div style="background:rgba(255, 255, 255, 0.04); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:0.75rem 0.9rem;">'
            f'<div style="font-size:0.75rem; font-weight:700; color:#38bdf8; text-transform:uppercase;">⏱️ Work-Rest Cycle</div>'
            f'<div style="font-size:0.86rem; font-weight:600; color:#f1f5f9; margin-top:2px;">{proto["work_rest"]}</div>'
            f'</div>'
            f'<div style="background:rgba(255, 255, 255, 0.04); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:0.75rem 0.9rem;">'
            f'<div style="font-size:0.75rem; font-weight:700; color:#38bdf8; text-transform:uppercase;">💧 Mandatory Hydration Quota</div>'
            f'<div style="font-size:0.86rem; font-weight:600; color:#f1f5f9; margin-top:2px;">{proto["hydration"]}</div>'
            f'</div>'
            f'<div style="background:rgba(255, 255, 255, 0.04); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:0.75rem 0.9rem;">'
            f'<div style="font-size:0.75rem; font-weight:700; color:#f87171; text-transform:uppercase;">🚫 Peak Direct-Sun Curfew</div>'
            f'<div style="font-size:0.86rem; font-weight:600; color:#f1f5f9; margin-top:2px;">{proto["curfew"]}</div>'
            f'</div>'
            f'</div>'
            f'<div style="background:{proto["badge_bg"]}; border:1px solid {proto["border"]}; border-radius:10px; padding:0.8rem 0.9rem; margin-top:0.9rem;">'
            f'<div style="font-size:0.75rem; font-weight:700; color:{proto["color"]}; text-transform:uppercase; margin-bottom:2px;">⚠️ Sector Vulnerability Directive</div>'
            f'<div style="font-size:0.8rem; color:#f1f5f9; line-height:1.35;">{proto["alert"]}</div>'
            f'</div>'
            f'<div style="margin-top:1.1rem; border-top:1px solid rgba(255,255,255,0.06); padding-top:0.8rem;">'
            f'<div style="font-size:0.74rem; font-weight:700; color:#94a3b8; margin-bottom:0.4rem; text-transform:uppercase;">NDMA Hazard Threshold Matrix:</div>'
            f'<div style="display:flex; flex-direction:column; gap:3px; font-size:0.74rem; color:#cbd5e1;">'
            f'<div style="display:flex; justify-content:space-between;"><span>Normal:</span> <span style="color:#34d399;">&lt; 27°C</span></div>'
            f'<div style="display:flex; justify-content:space-between;"><span>Caution:</span> <span style="color:#fbbf24;">27°C – 32°C</span></div>'
            f'<div style="display:flex; justify-content:space-between; font-weight:700; color:#fb923c; background:rgba(249,115,22,0.15); padding:1px 6px; border-radius:4px;"><span>Extreme Caution (Active):</span> <span>32°C – 39°C</span></div>'
            f'<div style="display:flex; justify-content:space-between;"><span>Danger:</span> <span style="color:#f87171;">39°C – 51°C</span></div>'
            f'<div style="display:flex; justify-content:space-between;"><span>Extreme Danger:</span> <span style="color:#ef4444;">&gt; 51°C</span></div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(right_html, unsafe_allow_html=True)