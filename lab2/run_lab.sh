#!/usr/bin/env bash
# Sets up the environment, runs the tests, then runs the pipeline.
#   bash run_lab.sh
set -e
cd "$(dirname "$0")"

if [ ! -d lab_02 ]; then
  python3 -m venv lab_02
fi
source lab_02/bin/activate
pip install -q -r requirements.txt

echo "== Tests =="
python -m pytest -q tests

echo "== Pipeline =="
python src/pipeline.py --input data/claims.csv --output_dir outputs --threshold 1.0

echo "== Summary =="
cat outputs/summary.txt
echo
echo "== Done! Check the outputs/ folder. =="
