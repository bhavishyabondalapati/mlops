"""Load the 'champion' model from the MLflow Model Registry and score new groups."""
import os

import mlflow
import pandas as pd

from data import TARGET, make_dataset

mlflow.set_tracking_uri("sqlite:///mlflow.db")


def main():
    model = mlflow.pyfunc.load_model("models:/ClaimsCostModel@champion")

    new_groups = make_dataset(n=5, seed=7)  # 5 groups the model has never seen
    X = new_groups.drop(columns=[TARGET])
    out = pd.DataFrame({
        "avg_age": X["avg_age"].round(1),
        "chronic_rate": X["chronic_rate"].round(3),
        "actual_pmpm": new_groups[TARGET].round(2),
        "predicted_pmpm": pd.Series(model.predict(X)).round(2).values,
    })
    print(out.to_string(index=False))
    os.makedirs("results", exist_ok=True)
    out.to_csv("results/sample_predictions.csv", index=False)


if __name__ == "__main__":
    main()
