import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from main import app  # noqa: E402

HIGH_RISK = {"avg_age": 58, "pct_female": 0.6, "members": 300, "chronic_rate": 0.3,
             "plan": "gold", "region": "northeast"}
LOW_RISK = {"avg_age": 28, "pct_female": 0.3, "members": 300, "chronic_rate": 0.05,
            "plan": "bronze", "region": "midwest"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # "with" runs the startup code that loads the model
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy", "model_loaded": True}


def test_model_info(client):
    body = client.get("/model-info").json()
    assert body["version"] == "1.0"
    assert "accuracy" in body["test_metrics"]


def test_predict_high_and_low(client):
    high = client.post("/predict", json=HIGH_RISK).json()
    low = client.post("/predict", json=LOW_RISK).json()
    assert high["risk_tier"] == "high"
    assert low["risk_tier"] == "low"
    assert abs(sum(high["probabilities"].values()) - 1) < 0.01


@pytest.mark.parametrize("field, bad_value", [
    ("avg_age", 150),          # out of range
    ("pct_female", 1.5),       # not a share
    ("members", 0),            # must be at least 1
    ("plan", "platinum"),      # not a known plan
])
def test_predict_rejects_bad_input(client, field, bad_value):
    r = client.post("/predict", json={**HIGH_RISK, field: bad_value})
    assert r.status_code == 422


def test_predict_missing_field(client):
    body = {k: v for k, v in HIGH_RISK.items() if k != "region"}
    assert client.post("/predict", json=body).status_code == 422


def test_batch(client):
    r = client.post("/predict/batch", json={"groups": [HIGH_RISK, LOW_RISK]})
    assert r.status_code == 200
    tiers = [p["risk_tier"] for p in r.json()["predictions"]]
    assert tiers == ["high", "low"]


def test_batch_empty_rejected(client):
    assert client.post("/predict/batch", json={"groups": []}).status_code == 422
