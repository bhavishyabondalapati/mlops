# Lab 4: Serving a model with FastAPI

Based on `API_Labs/FastAPI_Labs`. The course lab trains a decision tree on the Iris dataset and serves it with a `/predict` endpoint. I kept the same idea (train a model, put it behind a FastAPI app) but changed the problem and most of how the API works.

## The problem

The API predicts whether an employer group's claims cost will be **low, medium or high**, from its average age, share of female members, group size, share of members with a chronic condition, plan type and region. This is the kind of question our final project's MLR calculator deals with. The data is synthetic (3,000 groups, generated in `src/data.py`), so there's no real or private data.

The tiers are set from the training data: the cheapest third of groups is "low", the most expensive third is "high". The cut-offs (in dollars per member per month) are saved with the model and shown at `/model-info`.

## What I changed from the course lab

**The model is loaded once, at startup.** The course lab's `predict_data` calls `joblib.load` on every request, which re-reads the file from disk each time. I load it in FastAPI's `lifespan` hook and keep it in memory. If the model file is missing, the API still starts, but prediction endpoints return a 503 with a message saying to run `train.py`, instead of a generic 500.

**Input validation with real limits.** The Iris model accepts any float. Here every field has a range (age 18–80, shares between 0 and 1, at least 1 member), and `plan` and `region` only accept known values. Bad input gets a 422 that says which field is wrong.

**Probabilities, not just a label.** `/predict` returns the tier plus the probability of each tier and the model version, so a caller can tell a confident "high" from a borderline one.

**Batch endpoint.** `/predict/batch` scores up to 100 groups in one request.

**`/model-info` endpoint.** Shows the model version, training time, test accuracy, features and tier cut-offs.

**The model handles its own encoding.** `plan` and `region` are text, so the model is a scikit-learn pipeline with a `OneHotEncoder` in front of a random forest. The API passes the request fields straight in.

**Paths don't depend on where you run it.** The course lab uses `../model/iris_model.pkl`, which only works if you `cd src` first. I build the path from the file's own location.

**Tests.** `tests/test_api.py` uses FastAPI's `TestClient` to check every endpoint, including that bad input is rejected and that clearly high-risk and low-risk groups are classified correctly.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Server status and whether the model is loaded |
| GET | `/model-info` | Version, training time, metrics, tier cut-offs |
| POST | `/predict` | Risk tier for one group |
| POST | `/predict/batch` | Risk tiers for up to 100 groups |

Example request to `/predict`:

```json
{"avg_age": 42.5, "pct_female": 0.5, "members": 120,
 "chronic_rate": 0.15, "plan": "silver", "region": "south"}
```

Example response:

```json
{"risk_tier": "medium",
 "probabilities": {"high": 0.064, "low": 0.346, "medium": 0.59},
 "model_version": "1.0"}
```

## How to run

```bash
cd lab4
bash run_lab.sh
```

This trains the model, runs the tests, then starts the API. Open http://127.0.0.1:8000/docs to try the endpoints in the browser (Try it out → Execute). Press Ctrl+C to stop.

Or step by step:

```bash
python3 -m venv lab_04
source lab_04/bin/activate
pip install -r requirements.txt
cd src && python train.py && cd ..
python -m pytest -q tests
uvicorn main:app --app-dir src --port 8000
```

## Files

```
lab4/
├── src/
│   ├── data.py      # generates the synthetic dataset and tiers
│   ├── train.py     # trains the pipeline, saves model + metadata
│   └── main.py      # the FastAPI app
├── tests/test_api.py
├── model/           # model file is created by train.py (not committed)
├── run_lab.sh
└── requirements.txt
```

## Results

On the test set (750 groups), accuracy was 0.756 and macro F1 was 0.758. High and low were predicted well (F1 around 0.84 and 0.79), but medium was much harder (F1 0.65). That makes sense, because a medium group sits between the other two, so small noise in its cost can push it over either cut-off. A medium prediction with probabilities spread across tiers (like the example above) is less trustworthy than a confident high or low.
