"""FastAPI service that predicts an employer group's claims-cost risk tier."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "claims_risk_model.joblib"
state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once when the server starts, not on every request
    if MODEL_PATH.exists():
        state["bundle"] = joblib.load(MODEL_PATH)
    yield
    state.clear()


app = FastAPI(
    title="Claims Risk API",
    description="Predicts whether an employer group's claims cost will be low, medium or high.",
    version="1.0",
    lifespan=lifespan,
)


class GroupFeatures(BaseModel):
    avg_age: float = Field(..., ge=18, le=80, description="Average member age", examples=[42.5])
    pct_female: float = Field(..., ge=0, le=1, description="Share of female members (0-1)",
                              examples=[0.5])
    members: int = Field(..., ge=1, le=100_000, description="Number of members", examples=[120])
    chronic_rate: float = Field(..., ge=0, le=1,
                                description="Share of members with a chronic condition (0-1)",
                                examples=[0.15])
    plan: Literal["bronze", "silver", "gold"] = Field(..., examples=["silver"])
    region: Literal["northeast", "south", "midwest", "west"] = Field(..., examples=["south"])


class Prediction(BaseModel):
    risk_tier: Literal["low", "medium", "high"]
    probabilities: dict[str, float]


class PredictionResponse(Prediction):
    model_version: str


class BatchRequest(BaseModel):
    groups: list[GroupFeatures] = Field(..., min_length=1, max_length=100)


class BatchResponse(BaseModel):
    model_version: str
    predictions: list[Prediction]


def get_bundle() -> dict:
    bundle = state.get("bundle")
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Run `python src/train.py` and restart the server.",
        )
    return bundle


def predict_groups(groups: list[GroupFeatures]) -> list[Prediction]:
    bundle = get_bundle()
    model = bundle["model"]
    X = pd.DataFrame([g.model_dump() for g in groups])[bundle["features"]]
    probs = model.predict_proba(X)
    classes = [str(c) for c in model.classes_]
    results = []
    for row in probs:
        results.append(Prediction(
            risk_tier=classes[int(row.argmax())],
            probabilities={c: round(float(p), 4) for c, p in zip(classes, row)},
        ))
    return results


@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": "bundle" in state}


@app.get("/model-info")
async def model_info():
    bundle = get_bundle()
    return {k: v for k, v in bundle.items() if k != "model"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(group: GroupFeatures):
    result = predict_groups([group])[0]
    return PredictionResponse(**result.model_dump(), model_version=get_bundle()["version"])


@app.post("/predict/batch", response_model=BatchResponse)
async def predict_batch(request: BatchRequest):
    return BatchResponse(model_version=get_bundle()["version"],
                         predictions=predict_groups(request.groups))
