"""Synthetic employer-group data, labelled with a claims-cost risk tier.

Made-up data (no real people). Each row is an employer group. The label is
low / medium / high depending on its claims cost per member per month (PMPM).
"""
import numpy as np
import pandas as pd

FEATURES = ["avg_age", "pct_female", "members", "chronic_rate", "plan", "region"]
PLANS = {"bronze": 0.8, "silver": 1.0, "gold": 1.25}
REGIONS = {"northeast": 1.15, "south": 0.95, "midwest": 0.9, "west": 1.05}


def make_dataset(n: int = 3000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "avg_age": rng.uniform(25, 60, n),
        "pct_female": rng.uniform(0.2, 0.8, n),
        "members": rng.integers(10, 1000, n),
        "chronic_rate": rng.beta(2, 10, n),
        "plan": rng.choice(list(PLANS), n),
        "region": rng.choice(list(REGIONS), n),
    })
    base = (150 + 0.25 * (df["avg_age"] - 25) ** 2
            + 900 * df["chronic_rate"] + 60 * df["pct_female"])
    cost = base * df["plan"].map(PLANS) * df["region"].map(REGIONS)
    noise = rng.normal(0, 40 + 400 / np.sqrt(df["members"]))  # small groups are noisier
    df["claims_pmpm"] = np.clip(cost + noise, 20, None)
    return df


def add_tiers(df: pd.DataFrame, low_cut: float, high_cut: float) -> pd.Series:
    """Label each group: below low_cut = low, above high_cut = high, else medium."""
    return pd.cut(df["claims_pmpm"], [-np.inf, low_cut, high_cut, np.inf],
                  labels=["low", "medium", "high"]).astype(str)
