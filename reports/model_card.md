# Model Card: Next-day Max Heat Index

## Model
- Algorithm: LightGBM quantile regression (10th, 50th, 90th percentile).
- Target: next-day maximum heat index (C), learned as the change from today's max heat index.
- Interval: 10th to 90th percentile widened by a conformal margin, nominal 80%.
- Cities: Karachi, Lahore, Multan, Jacobabad.
- Features (13): max_temp, max_hi, mean_humidity, mean_wind, mean_pressure, hi_lag1, hi_lag7, temp_lag1, hi_roll7, month, city_code, hum_chg, pres_chg.

## Data and split
- Source: gold_features table (Open-Meteo, checked by the Data Quality Agent).
- Split by date: train 70%, validation 15%, test 15%.
- Test window: 2026-07-03 to 2026-10-19 (436 rows).

## Test results
| Metric | Value |
|---|---|
| Model MAE | 1.2334 |
| Baseline MAE (tomorrow = today) | 1.2705 |
| Improvement over baseline | 2.9% |
| Calibrated 80% interval coverage | 87.8% |
| Raw interval coverage | 73.6% |
| Average interval width (C) | 4.8 |

## Slices
| city | MAE | Baseline MAE | 80% coverage | Rows |
|---|---|---|---|---|
| Jacobabad | 1.1413 | 1.1149 | 91.7% | 109 |
| Karachi | 1.1261 | 1.1429 | 87.2% | 109 |
| Lahore | 1.4106 | 1.5613 | 82.6% | 109 |
| Multan | 1.2555 | 1.263 | 89.9% | 109 |

| season | MAE | Baseline MAE | 80% coverage | Rows |
|---|---|---|---|---|
| Autumn | 1.1507 | 1.2156 | 87.8% | 196 |
| Summer | 1.3009 | 1.3154 | 87.9% | 240 |

## Limitations
- The gain over the persistence baseline is small. Treat the median forecast as a modest improvement, not a large one.
- The test window covers only some seasons (see the season table). It does not represent a full year.
- Coverage is above the nominal 80%, so intervals are on the wide side.
- Risk levels are placeholders based on US NWS heat index bands, not PMD/NDMA thresholds.
- Values are gridded model data, not thermometer readings.
- The data is historical, so the forecast is not live for tomorrow.
