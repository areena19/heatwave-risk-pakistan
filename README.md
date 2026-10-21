# 🌡️ PakHeat: Climate Risk & Predictive Intelligence Platform

[![Hourly Pipeline](https://github.com/areena19/heatwave-risk-pakistan/actions/workflows/hourly.yml/badge.svg)](https://github.com/areena19/heatwave-risk-pakistan/actions/workflows/hourly.yml)
[![DuckDB Lakehouse](https://img.shields.io/badge/Lakehouse-DuckDB-yellow.svg)](https://duckdb.org/)
[![Model Selection](https://img.shields.io/badge/Model-LightGBM%20Quantile-blue.svg)](https://lightgbm.readthedocs.io/)
[![Orchestration](https://img.shields.io/badge/Orchestration-Prefect%20v3-red.svg)](https://www.prefect.io/)
[![Frontend](https://img.shields.io/badge/Dashboard-Streamlit%20Bento-ff4b4b.svg)](https://streamlit.io/)

> **An automated climate intelligence and early-warning forecasting engine designed to protect vulnerable outdoor laborers (brick kiln workers, agricultural hands, construction labor, and street vendors) across four of Pakistan's highest-risk urban and semi-arid hubs: Karachi, Lahore, Multan, and Jacobabad.**

---

## 📌 Executive Summary & Humanitarian Mission

Pakistan ranks consistently among the world's most climate-vulnerable nations, suffering recurring severe heatwaves with high humid-heat loads. Standard thermometer readings (ambient dry-bulb temperature) understate human physical peril because high humidity suppresses the body's natural evaporative cooling (sweating) mechanism.

**PakHeat** bridges meteorological telemetry and actionable labor safety:

1. **Forecasts Next-Day Maximum Heat Index (`max_hi`)**: Models physiological heat strain via the NOAA/Rothfusz formulation, which combines air temperature and relative humidity.
2. **Calibrated Uncertainty via Conformal Prediction**: Replaces uncalibrated heuristics by wrapping forecasts in conformally calibrated, nominal 80% prediction intervals ($p10$ to $p90$, widened by a calibration margin $q$).
3. **Automated MLOps Architecture**: Runs on GitHub Actions on an hourly cron schedule, orchestrating multi-source ingestion, data-quality audits, DuckDB materialization, and retraining.
4. **Actionable Occupational Guidance**: Maps numerical forecasts to proposed hazard tiers, work-rest ratios, hydration quotas, and curfews, informed by **NDMA** and **WHO** heat-safety guidance (see the [verification note](#-actionable-labor-advisory-matrix)).

---

## 🏗️ System Architecture & Data Pipeline

```text
                 ┌────────────────────────┐       ┌──────────────────────┐
                 │    Open-Meteo API      │       │   NASA POWER Agro    │
                 │ (Hourly Archive/Recent)│       │ (Satellite Solar/Met)│
                 └───────────┬────────────┘       └──────────┬───────────┘
                             │                               │
                             └───────────────┬───────────────┘
                                             ▼
                                 ┌───────────────────────┐
                                 │  Data Quality Agent   │
                                 │  (Pandera + SHA-256)  │
                                 └───────────┬───────────┘
                                             ▼
                                 ┌───────────────────────┐
                                 │   DuckDB Lakehouse    │
                                 │ (cleaned, daily, lags)│
                                 └───────────┬───────────┘
                                             ▼
                    ┌─────────────────────────────────────────────────┐
                    │   Multi-Model Tournament & Conformal Engine     │
                    │ (LightGBM vs HistGradientBoosting vs Sklearn GB)│
                    └───────────┬─────────────────────────┬───────────┘
                                │                         │
                                ▼                         ▼
                    ┌───────────────────────┐ ┌───────────────────────┐
                    │ Next-Day Forecast API │ │  RAG Evidence Engine  │
                    │  (Calibrated Bounds)  │ │ (NDMA / WHO Policies) │
                    └───────────┬───────────┘ └───────────┬───────────┘
                                │                         │
                                └────────────┬────────────┘
                                             ▼
                                 ┌───────────────────────┐
                                 │ Streamlit Bento Grid  │
                                 │  Command Intelligence │
                                 └───────────────────────┘
```

---

## 🧪 Empirical Algorithm Tournament & Model Selection

To avoid arbitrary model selection, we run an automated **Multi-Model Tournament** on a strict chronological (walk-forward) split to prevent lookahead bias:

| Split | Share | Observations | Purpose |
| :--- | :---: | :---: | :--- |
| Training | 70% | 2,028 | Model fitting |
| Validation | 15% | 436 | Model selection and interval calibration |
| Test | 15% | 432 | Out-of-sample evaluation |

All algorithms predict the **day-to-day change** in maximum Heat Index relative to the persistence baseline, and the prediction is added back to today's value:

$$\Delta y_{t+1} = HI^{\max}_{t+1} - HI^{\max}_{t}, \qquad \hat{HI}^{\max}_{t+1} = HI^{\max}_{t} + \hat{\Delta y}_{t+1}$$

Thirteen engineered features are used:

- **Temporal:** `hi_lag1`, `hi_lag7`, `temp_lag1`
- **Rolling statistics:** `hi_roll7`
- **Weather variables:** `max_temp`, `max_hi`, `mean_humidity`, `mean_wind`, `mean_pressure`
- **Change features:** `hum_chg`, `pres_chg`
- **Seasonal & spatial:** `month`, `city_code`

Each candidate models the 10th, 50th, and 90th conditional quantiles. Validation MAE below is reported for the next-day forecast:

| Rank | Candidate Algorithm | Architecture | Quantiles Modeled | Validation MAE | vs Baseline | Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| 🥇 | **LightGBM Regressor** | Tree-based gradient boosting | $p10, p50, p90$ | **1.5458 °C** | **+5.29%** | **Selected** |
| 🥈 | **HistGradientBoosting** | Scikit-Learn histogram GBDT | $p10, p50, p90$ | 1.5473 °C | +5.20% | Benchmarked |
| 🥉 | **GradientBoosting** | Scikit-Learn quantile trees | $p10, p50, p90$ | 1.5714 °C | +3.72% | Benchmarked |
| — | *Persistence Baseline* | *Static ($t \to t+1$)* | — | *1.6322 °C* | *—* | *Reference* |

**Winner justification:** LightGBM achieved the lowest validation MAE ($1.5458\,^\circ\text{C}$). Its margin over HistGradientBoosting is small ($0.0015\,^\circ\text{C}$), so the two are close in accuracy; LightGBM was selected as the rule-based winner of the tournament. The selected model is serialized to `data/models/heatwave_quantile_models.pkl`.

---

## 📐 Conformal Prediction Calibration

Uncalibrated quantile regressors commonly under-cover. To improve the reliability of the intervals, we applied **Distribution-Free Split Conformal Prediction**:

1. **Non-conformity scoring**, computed on the chronological validation set:

   $$s_i = \max(p10_i - y_i, \; y_i - p90_i)$$

2. **Empirical quantile calibration:** the conformal adjustment resolved to $q = 0.668\,^\circ\text{C}$.
3. **Calibrated prediction interval:**

   $$C(x) = \left[ p10(x) - q, \; p90(x) + q \right]$$

### Calibration Results

| Interval | Coverage | Average Width |
| :--- | :---: | :---: |
| Raw (uncalibrated), validation | 61.0% | 3.29 °C |
| Calibrated, validation | **80.3%** | 4.62 °C |
| Calibrated, test | **88.2%** | 4.63 °C |

- Calibration raised validation coverage from 61.0% to 80.3%, in line with the nominal 80% target.
- Test coverage (88.2%) exceeds the target, i.e. intervals are conservative on the test period. Conformal guarantees assume exchangeable data, which time series only approximate, so coverage should be monitored over time.

---

## 📊 Out-of-Sample Test Evaluation & Fairness Slices

Evaluated on an unseen test horizon of **432** station-day observations from `2026-07-05` to `2026-10-20`:

- **Model test MAE:** **1.2418 °C** (persistence baseline: 1.2788 °C)
- **Calibrated 80% interval coverage:** **88.2%** (average width: 4.63 °C)

### Sub-Group Evaluation by Station

| Monitoring Station | Test MAE | Baseline MAE | vs Baseline | 80% Coverage | Samples | Primary Micro-Climate Factor |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Jacobabad** | 1.1568 °C | 1.1196 °C | Slightly worse | 91.7% | 108 | Extreme continental semi-arid thermal belt |
| **Karachi** | 1.1531 °C | 1.1734 °C | Better | 86.1% | 108 | Maritime humidity & sea-breeze moisture traps |
| **Multan** | 1.2285 °C | 1.2715 °C | Better | 90.7% | 108 | Arid inland heat accumulation |
| **Lahore** | 1.4286 °C | 1.5508 °C | Better | 84.3% | 108 | Urban heat island (UHI) & monsoon moisture |

The model beats persistence in Karachi, Multan, and Lahore. In Jacobabad it is slightly worse than the baseline, though interval coverage there remains high.

### Temporal Performance Slices by Season

| Season | Test MAE | Baseline MAE | vs Baseline | 80% Coverage | Samples |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Autumn (Sep–Oct)** | 1.1390 °C | 1.2099 °C | Better | 86.5% | 200 |
| **Summer (Jul–Aug)** | 1.3303 °C | 1.3382 °C | Marginally better | 89.7% | 232 |

---

## 🛡️ Autonomous Data Quality Agent & Lakehouse

Data integrity is enforced at every ingestion boundary by the **Data Quality Agent**:

- **Gate 1 (Schema & type verification):** Strict Pandera schema checks on physical bounds (e.g. $10 \le \text{Temp} \le 60\,^\circ\text{C}$, $0 \le \text{RH} \le 100\%$).
- **Gate 2 (Cross-source sensor agreement):** Compares Open-Meteo surface observations with NASA POWER satellite measurements; a difference above $4.5\,^\circ\text{C}$ raises a source-disagreement warning.
- **Gate 3 (Anomaly & step-jump detection):** Flags and quarantines implausible jumps ($\lvert\Delta T\rvert \ge 7\,^\circ\text{C}$ within a single hour).
- **Gate 4 (Cryptographic audit ledger):** Every downloaded JSON file is hashed with **SHA-256** and appended to `manifest.csv` for full data provenance.

### Materialized DuckDB Lakehouse

| Table | Contents | Size |
| :--- | :--- | :---: |
| `raw_manifest` | Cryptographic registry of every API transaction and checksum | — |
| `cleaned_hourly` | Curated hourly meteorological measurements | 70,420+ records |
| `gold_daily` | Aggregated 24-hour daily extremes | 2,932 station-days |
| `gold_features` | Temporal lags and rolling-aggregate feature vectors | 2,904 records |

---

## 👷 Actionable Labor Advisory Matrix

PakHeat translates heat index forecasts into **proposed** workplace protection protocols:

| Hazard Tier | Heat Index | Work-Rest Cycle | Hydration | Operational Curfew |
| :--- | :---: | :--- | :--- | :--- |
| **Normal** | < 27 °C | Standard continuous shifts | Standard potable access | None |
| **Caution** | 27 – < 32 °C | 50 min work / 10 min shaded rest | 500 ml ORS / hr | Provide ventilated cool zones |
| **Extreme Caution** | 32 – < 39 °C | 40 min work / 20 min rest | 750 ml – 1 L electrolytes / hr | Restrict heavy direct-sun labor 12:00–15:30 |
| **Danger** | 39 – 51 °C | 30 min work / 30 min active cooling | ≥ 1.2 L cool fluids / hr | Consider shift curfew 11:30–16:00 |
| **Extreme Danger** | > 51 °C | Suspend outdoor labor | Continuous medical monitoring | All daytime outdoor shifts suspended |

> **Note:** These thresholds, work-rest ratios, hydration quotas, and curfew windows are proposed operational responses informed by NDMA and WHO guidance. They should be verified against current official guidance before being presented as mandatory regulations.

---

## 💻 Streamlit Bento Command Center

The application features a modular **Bento Grid Command Center** (`dashboard/app.py`):

1. **National 4-City Heatwatch Bar:** Instant multi-station comparison of tomorrow's predicted Heat Index and risk level.
2. **Integrated Forecast Hub:** Predicted peak Heat Index, 80% conformal interval, and underlying atmospheric drivers (air temperature, relative humidity, wind speed).
3. **Interactive 30-Day Trajectory Chart:** Built with Altair; shows the last 30 days of observations leading into tomorrow's calibrated uncertainty band.
4. **Operational Safety Panel:** Displays labor safety protocols mapped to the predicted hazard tier.
5. **What-If Scenario Sandbox:** Interactive slider for simulating thermal-shock scenarios in real time.
6. **Climate Intelligence (RAG):** AI advisory chatbot grounded in indexed NDMA and WHO health guidelines, with similarity-matched citations.

---

## 🚀 Quickstart & Reproduction Guide

### 1. Environment Setup

```powershell
# Clone the repository
git clone https://github.com/areena19/heatwave-risk-pakistan.git
cd heatwave-risk-pakistan

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

On Linux/macOS, activate with `source .venv/bin/activate` instead.

### 2. Run the Automated Pipeline

```powershell
# Execute the complete hourly pipeline (Fetch -> Verify -> Clean -> DQ -> Warehouse -> Train -> Calibrate)
python -m src.flows.hourly

# Or execute the downstream modules individually:
python -m src.features.daily
python -m src.features.lags
python -m src.warehouse.build
python -m src.model.train      # Runs the Multi-Model Tournament
python -m src.model.calibrate  # Calibrates the conformal q
python -m src.model.evaluate   # Generates metrics.json and model_card.md
```

### 3. Launch the Command Dashboard

```powershell
streamlit run dashboard/app.py
```

---

## 📂 Repository Layout

```text
├── .github/workflows/          # GitHub Actions automated hourly cron workflow
│   └── hourly.yml
├── dashboard/                  # Modular Streamlit frontend
│   ├── app.py                  # Main conductor application
│   ├── styles.py               # Glassmorphic dark styling
│   └── tabs/                   # Modular tab views
│       ├── forecaster.py       # Bento Grid forecast & Altair trajectory
│       ├── rag.py              # NDMA/WHO policy advisory chat
│       ├── warehouse.py        # Lakehouse health & DQ audit
│       └── governance.py       # Model tournament & fairness slices
├── data/
│   ├── models/                 # heatwave_quantile_models.pkl & conformal_q.json
│   ├── warehouse/              # DuckDB database file
│   └── evidence/               # Official NDMA & WHO policy PDFs
├── reports/                    # Evaluation metrics.json & model_card.md
├── src/
│   ├── clean/                  # Hourly cleaning & preprocessing
│   ├── dq_agent/               # Data Quality Agent (Pandera gates & cross-checks)
│   ├── features/               # Heat index, daily aggregations & lag features
│   ├── fetch/                  # Open-Meteo & NASA POWER fetchers + SHA-256 verify
│   ├── flows/                  # Prefect hourly pipeline orchestrator
│   ├── model/                  # Multi-model tournament, calibration, inference
│   ├── rag/                    # Vector index, chunking & LLM insight agent
│   └── warehouse/              # DuckDB build & schema materialization
├── AI_Use_Log.md               # Transparent record of AI tool assistance
└── requirements.txt            # Project dependencies
```

---

## 📜 Ethical AI & Academic Governance

In line with hackathon standards and academic transparency:

- All architectural decisions, station choices, and labor protection adaptations are human-directed.
- AI drafting and coding assistance is disclosed in [`AI_Use_Log.md`](AI_Use_Log.md).
- Pipeline scripts and model benchmarks have been executed and validated locally.
- Forecasts and advisories support, but do not replace, official government and occupational-health guidance.
