"""Synthetic employer-group data for predicting claims cost per member per month.

Made-up data (no real people). Cost depends on age (non-linearly), chronic
conditions, plan type and region, so a straight-line model won't capture all of it.
"""
import numpy as np
import pandas as pd

TARGET = "claims_pmpm"
PLANS = {"bronze": 0.8, "silver": 1.0, "gold": 1.25}
REGIONS = {"northeast": 1.15, "south": 0.95, "midwest": 0.9, "west": 1.05}


def make_dataset(n: int = 2000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    avg_age = rng.uniform(25, 60, n)
    pct_female = rng.uniform(0.2, 0.8, n)
    members = rng.integers(10, 1000, n)
    chronic_rate = rng.beta(2, 10, n)  # share of members with a chronic condition
    plan = rng.choice(list(PLANS), n)
    region = rng.choice(list(REGIONS), n)

    base = 150 + 0.25 * (avg_age - 25) ** 2 + 900 * chronic_rate + 60 * pct_female
    cost = base * np.array([PLANS[p] for p in plan]) * np.array([REGIONS[r] for r in region])
    noise = rng.normal(0, 40 + 400 / np.sqrt(members))  # small groups are noisier
    cost = np.clip(cost + noise, 20, None)

    df = pd.DataFrame({
        "avg_age": avg_age,
        "pct_female": pct_female,
        "members": members.astype(float),
        "chronic_rate": chronic_rate,
        "plan": pd.Categorical(plan, categories=list(PLANS)),
        "region": pd.Categorical(region, categories=list(REGIONS)),
        TARGET: cost,
    })
    # Fixed categories, so even a 5-row sample gets the same columns as training
    return pd.get_dummies(df, columns=["plan", "region"], dtype=float)
