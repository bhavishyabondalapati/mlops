# Lab 2: Data Processing Pipeline with Apache Beam

Based on `Labs/Data_Labs/Apache_Beam_Labs` from the course repo. Apache Beam is a framework for writing data pipelines once and running them anywhere: locally with the DirectRunner (used here) or at scale on Google Cloud Dataflow.

## What this lab does

The pipeline reads a health insurance claims file (one row per client per month), cleans it, and computes each client's **Medical Loss Ratio (MLR)**, the share of premium spent on claims. Clients with MLR above 1.0 are losing money for the insurer and get flagged.

```
claims.csv
   │  ReadFromText
   ▼
Distinct ──────────── drop exact duplicate rows
   │
ParDo(ParseRow) ───── bad rows ──► invalid_rows.csv (with reason)
   │ valid rows
   ├──► CombinePerKey(SumPremiumAndClaims) per client ──► client_mlr.csv
   │                     └──► Filter(MLR > threshold) ──► high_risk_clients.csv
   ├──► CombinePerKey(sum) per month ──────────────────► monthly_claims.csv
   └──► Counts + overall totals as side inputs ────────► summary.txt
```

## What I changed from the original lab

1. **Different dataset.** A synthetic health claims dataset (`data/claims.csv`: 20 clients × 12 months) with deliberate problems: 5 duplicate rows and 7 rows with missing claims. No real personal data.
2. **Data quality handling.** Duplicates are removed with `Distinct`, and bad rows are routed to a separate output using `TaggedOutput`, with the reason each row failed, instead of crashing the pipeline or silently dropping them.
3. **Custom `CombineFn`.** `SumPremiumAndClaims` adds premium and claims together in one pass and counts months, so MLR is computed correctly from totals (not by averaging monthly ratios).
4. **Side inputs.** The run summary combines several single values (row counts, client counts, totals) using `AsSingleton` side inputs.
5. **Configurable threshold.** `--threshold` sets the MLR level for flagging high-risk clients.
6. **Unit tests.** `tests/test_transforms.py` tests the parsing and MLR logic with pytest, including five kinds of bad rows.
7. **One-command run.** `run_lab.sh` sets up the environment, runs the tests and the pipeline, and pushes to GitHub.

## Project structure

```
lab2/
├── data/claims.csv          # input data
├── src/
│   ├── pipeline.py          # the Beam pipeline
│   └── transforms.py        # plain helper functions (parsing, MLR)
├── tests/test_transforms.py
├── outputs/                 # created by the pipeline
├── run_lab.sh
└── requirements.txt
```

## How to run

```bash
cd lab2
bash run_lab.sh
```

Or step by step:

```bash
python3 -m venv lab_02
source lab_02/bin/activate          # Windows: lab_02\Scripts\activate
pip install -r requirements.txt
python -m pytest -q tests
python src/pipeline.py --input data/claims.csv --output_dir outputs --threshold 1.0
```

Try a different threshold, e.g. `--threshold 0.9`, and compare `outputs/high_risk_clients.csv`.

## Results

| Check | Value |
|---|---|
| Rows in file | 245 |
| After removing duplicates | 240 |
| Valid rows | 233 |
| Invalid rows (missing claims) | 7 |
| Clients | 20 |
| High-risk clients (MLR > 1.0) | 11 |
| Overall MLR | 0.952 |

## Outputs

| File | Contents |
|---|---|
| `client_mlr.csv` | Months, total premium, total claims and MLR for each client |
| `high_risk_clients.csv` | Clients with MLR above the threshold |
| `monthly_claims.csv` | Total claims per month |
| `invalid_rows.csv` | Rows that failed validation, with the reason |
| `summary.txt` | Row counts, client counts and overall MLR |
