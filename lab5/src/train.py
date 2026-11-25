"""Train the risk-tier classifier and save it, with its metadata, to model/."""
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from data import FEATURES, add_tiers, make_dataset

MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "claims_risk_model.joblib"
MODEL_VERSION = "1.0"


def build_model():
    # The pipeline does its own one-hot encoding, so the API can pass in
    # plan/region as plain strings exactly as the user sends them.
    encode = ColumnTransformer(
        [("categories", OneHotEncoder(handle_unknown="ignore"), ["plan", "region"])],
        remainder="passthrough",
    )
    forest = RandomForestClassifier(n_estimators=200, max_depth=10,
                                    class_weight="balanced", random_state=42)
    return Pipeline([("encode", encode), ("forest", forest)])


def main():
    df = make_dataset()
    train_df, test_df = train_test_split(df, test_size=0.25, random_state=42)

    # Tier cut-offs come from the training data only (33rd and 67th percentile)
    low_cut, high_cut = train_df["claims_pmpm"].quantile([1 / 3, 2 / 3])
    y_train = add_tiers(train_df, low_cut, high_cut)
    y_test = add_tiers(test_df, low_cut, high_cut)

    model = build_model()
    model.fit(train_df[FEATURES], y_train)
    pred = model.predict(test_df[FEATURES])

    metrics = {
        "accuracy": round(accuracy_score(y_test, pred), 4),
        "macro_f1": round(f1_score(y_test, pred, average="macro"), 4),
    }
    print(classification_report(y_test, pred, digits=3))
    print(metrics)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({
        "model": model,
        "version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "features": FEATURES,
        "tier_cutoffs_pmpm": {"low_below": round(low_cut, 2), "high_above": round(high_cut, 2)},
        "test_metrics": metrics,
        "train_rows": len(train_df),
    }, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
