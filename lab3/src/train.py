"""Train several models, track every run in MLflow, and register the best one.

Changes from the course lab (ElasticNet on wine data):
- tracking goes to a SQLite database, so the Model Registry works
- 8 runs: a grid of ElasticNet settings plus two random forests
- ElasticNet gets a StandardScaler first (it is sensitive to feature scale)
- each run also logs a predicted-vs-actual plot
- the lowest-RMSE model is registered and tagged with the alias "champion"
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mlflow  # noqa: E402
import mlflow.sklearn  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from mlflow import MlflowClient  # noqa: E402
from mlflow.models import infer_signature  # noqa: E402
from sklearn.ensemble import RandomForestRegressor  # noqa: E402
from sklearn.linear_model import ElasticNet  # noqa: E402
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from data import TARGET, make_dataset  # noqa: E402

TRACKING_URI = "sqlite:///mlflow.db"
EXPERIMENT = "claims-cost-prediction"
MODEL_NAME = "ClaimsCostModel"


def candidates():
    for alpha in [0.1, 0.5, 1.0]:
        for l1_ratio in [0.2, 0.8]:
            model = make_pipeline(
                StandardScaler(),
                ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42),
            )
            yield f"elasticnet_a{alpha}_l1{l1_ratio}", "elasticnet", \
                {"alpha": alpha, "l1_ratio": l1_ratio}, model
    for max_depth in [4, 8]:
        model = RandomForestRegressor(n_estimators=200, max_depth=max_depth, random_state=42)
        yield f"random_forest_depth{max_depth}", "random_forest", \
            {"n_estimators": 200, "max_depth": max_depth}, model


def eval_metrics(actual, pred):
    rmse = float(np.sqrt(mean_squared_error(actual, pred)))
    return rmse, float(mean_absolute_error(actual, pred)), float(r2_score(actual, pred))


def pred_vs_actual(actual, pred, title):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(actual, pred, s=8, alpha=0.5)
    lims = [min(actual.min(), pred.min()), max(actual.max(), pred.max())]
    ax.plot(lims, lims, "r--", linewidth=1)
    ax.set_xlabel("Actual claims PMPM ($)")
    ax.set_ylabel("Predicted claims PMPM ($)")
    ax.set_title(title)
    fig.tight_layout()
    return fig


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)

    df = make_dataset()
    X, y = df.drop(columns=[TARGET]), df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    results = []
    for run_name, family, params, model in candidates():
        with mlflow.start_run(run_name=run_name) as run:
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            rmse, mae, r2 = eval_metrics(y_test, pred)

            mlflow.set_tag("model_family", family)
            mlflow.log_params(params)
            mlflow.log_param("train_rows", len(X_train))
            mlflow.log_metrics({"rmse": rmse, "mae": mae, "r2": r2})

            fig = pred_vs_actual(y_test, pred, run_name)
            mlflow.log_figure(fig, "pred_vs_actual.png")
            plt.close(fig)

            # Newer MLflow saves sklearn models with skops, which refuses tree
            # objects unless you mark them as trusted. We trained this model ourselves.
            trusted = ["sklearn.tree._tree.Tree"] if family == "random_forest" else None
            info = mlflow.sklearn.log_model(
                model, name="model", signature=infer_signature(X_test, pred),
                skops_trusted_types=trusted,
            )
            results.append({
                "run_name": run_name, "model_family": family,
                "rmse": round(rmse, 2), "mae": round(mae, 2), "r2": round(r2, 4),
                "run_id": run.info.run_id, "model_uri": info.model_uri,
            })
            print(f"{run_name:28s} RMSE={rmse:7.2f}  MAE={mae:7.2f}  R2={r2:.4f}")

    table = pd.DataFrame(results).sort_values("rmse").reset_index(drop=True)
    os.makedirs("results", exist_ok=True)
    table.drop(columns=["model_uri"]).to_csv("results/experiment_results.csv", index=False)

    best = table.iloc[0]
    version = mlflow.register_model(best["model_uri"], MODEL_NAME)
    client = MlflowClient()
    client.set_registered_model_alias(MODEL_NAME, "champion", version.version)
    client.update_model_version(
        MODEL_NAME, version.version,
        description=f"Best of {len(table)} runs: {best['run_name']} (test RMSE {best['rmse']})",
    )
    print(f"\nBest: {best['run_name']} (RMSE {best['rmse']})")
    print(f"Registered as {MODEL_NAME} version {version.version}, alias 'champion'")


if __name__ == "__main__":
    main()
