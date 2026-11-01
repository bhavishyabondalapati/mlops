#!/usr/bin/env bash
# Sets up the environment, runs all experiments, then loads the champion model.
#   bash run_lab.sh
set -e
cd "$(dirname "$0")"

if [ ! -d lab_03 ]; then
  python3 -m venv lab_03
fi
source lab_03/bin/activate
pip install -q -r requirements.txt

echo "== Training 8 models (each one is an MLflow run) =="
python src/train.py

echo "== Predicting with the registered champion model =="
python src/predict.py

echo
echo "== Done! To browse the runs in the MLflow UI: =="
echo "source lab_03/bin/activate && mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001"
echo "then open http://127.0.0.1:5001"
