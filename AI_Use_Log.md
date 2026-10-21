# AI Use Log

## Tools used
- Claude
- ChatGPT
- GitHub Copilot

## Where AI was used

| Area | How AI helped |
|---|---|
| Pipeline | Helped build the data pipeline: fetching (Open-Meteo, NASA POWER), cleaning, daily and lag features, DuckDB warehouse, and the Prefect flow |
| Model and calibration | Helped with the LightGBM quantile model, conformal calibration and retraining logic |
| RAG and dashboard | Helped with the advice retrieval code and the dashboard |
| Code writing | Helped write and refactor code across `src/` |
| Debugging | Helped find and fix errors in the code |
| DQ agent design | Helped design the Data Quality Agent (checks, gates, quarantine) |
| Tests | Helped write unit tests in `tests/` |

## How the output was checked
- Ran the unit tests in `tests/` and reviewed the results.
- Ran the pipeline and checked the outputs (reports, DuckDB tables).
- Re-ran queries on the warehouse to confirm the dates and row counts used in the dataset proposal.
- Checked `git status` before pushing, so `.env` and `.venv` were not committed.

## Human responsibility
- The team reviewed, ran and is responsible for all submitted code and documents.
- Anything AI wrote that could not be verified was left out or marked for the team to confirm.

## Not done by AI
- Project idea, choice of the four cities and the focus on outdoor workers.
- Collecting the evidence PDFs in `data/evidence/`.
- Running the pipeline and tests on our own machine and checking the results.
- Final decisions on what to keep, flag or remove in the data.
- Creating the GitHub repository and pushing the code.