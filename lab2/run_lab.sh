#!/usr/bin/env bash
# Runs the whole lab in one go. From inside the lab2 folder:
#   bash run_lab.sh
set -e
cd "$(dirname "$0")"

echo "== 1. Environment =="
python3 -m venv lab_02
source lab_02/bin/activate
pip install -q -r requirements.txt

echo "== 2. Unit tests =="
python -m pytest -q tests

echo "== 3. Run the Beam pipeline =="
python src/pipeline.py --input data/claims.csv --output_dir outputs --threshold 1.0

echo "== 4. Results =="
cat outputs/summary.txt
echo
echo "High-risk clients:"
cat outputs/high_risk_clients.csv

echo "== 5. Push to GitHub =="
git add .
git commit -m "Lab 2: Apache Beam claims data pipeline"
git push origin main
echo "Done! Submit: https://github.com/bhavishyabondalapati/mlops/tree/main/lab2"
