#!/usr/bin/env bash
# Trains the model, runs the API tests, then starts the API.
#   bash run_lab.sh        (Ctrl+C stops the server)
set -e
cd "$(dirname "$0")"

if [ ! -d lab_04 ]; then
  python3 -m venv lab_04
fi
source lab_04/bin/activate
pip install -q -r requirements.txt

echo "== Training =="
(cd src && python train.py)

echo "== API tests =="
python -m pytest -q tests

echo "== Starting API: open http://127.0.0.1:8000/docs (Ctrl+C to stop) =="
uvicorn main:app --app-dir src --port 8000
