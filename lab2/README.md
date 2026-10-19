# Lab 2: Apache Beam claims pipeline

For this lab I built an Apache Beam pipeline that runs locally. I used a synthetic health insurance claims file instead of the original lab's data, because our final project (an MLR calculator for an insurance company) works with this kind of data, so I wanted to practice on something similar.

Each row in `data/claims.csv` is one client (an employer group) in one month: number of members, premium paid, and claims paid. The pipeline cleans the file and calculates each client's MLR (Medical Loss Ratio = claims ÷ premium). An MLR above 1.0 means the client cost more in claims than they paid in premium.

The data is made up, with some problems added on purpose: 5 duplicate rows and 7 rows with no claims value.

## How the pipeline works

```
claims.csv
   │
Distinct ──────────── drop exact duplicate rows
   │
ParseRow ──────────── bad rows ──► invalid_rows.csv (with reason)
   │ valid rows
   ├──► total per client ──► client_mlr.csv
   │          └──► MLR > threshold ──► high_risk_clients.csv
   ├──► total per month ───► monthly_claims.csv
   └──► counts and totals ─► summary.txt
```

Bad rows aren't dropped silently. They go to `invalid_rows.csv` with the reason they failed, so you can see what was thrown out. A row with a missing claims value counts as invalid rather than as zero claims, because a blank usually means the data isn't in yet, and treating it as 0 would make the client look cheaper than they are.

For the per-client totals I wrote a small combiner (`SumPremiumAndClaims`) that adds up premium and claims together and counts the months. MLR is then calculated from the totals for the whole period, not by averaging each month's ratio, since a small month would otherwise count as much as a big one.

Two decisions worth noting:

- `Distinct` only removes rows that are exactly the same. If a client had two different rows for the same month, both would be kept. For this lab I left it that way, but for real data you'd want a rule for which row wins.
- The MLR threshold for "high risk" is a command-line option (`--threshold`, default 1.0). The comparison uses the exact ratio; values are only rounded when written to the output files.

## Files

```
lab2/
├── data/claims.csv          # input data
├── src/
│   ├── pipeline.py          # the Beam pipeline
│   └── transforms.py        # parsing and MLR helpers
├── tests/test_transforms.py # pytest tests for the helpers
├── outputs/                 # written by the pipeline
├── run_lab.sh               # setup + tests + pipeline
└── requirements.txt
```

## How to run

```bash
cd lab2
bash run_lab.sh
```

This creates a virtual environment, installs Beam, runs the tests, and runs the pipeline. Or step by step:

```bash
python3 -m venv lab_02
source lab_02/bin/activate
pip install -r requirements.txt
python -m pytest -q tests
python src/pipeline.py --input data/claims.csv --output_dir outputs --threshold 1.0
```

## Results

From my run (threshold 1.0):

| | |
|---|---|
| Rows in the file | 245 |
| After removing duplicates | 240 |
| Valid rows | 233 |
| Invalid rows (missing claims) | 7 |
| Clients | 20 |
| Clients with MLR above 1.0 | 11 |
| Overall MLR | 0.952 |
