"""
stats_utils.py

A small statistics toolkit used to practice testing and CI with GitHub Actions.
Replaces the calculator example from the original lab with functions that are
closer to what an ML pipeline actually needs (summary stats, scaling, loading data).
"""

import csv
import math


def _validate(values):
    """Make sure we got a non-empty list of numbers."""
    if not isinstance(values, (list, tuple)):
        raise TypeError("Input must be a list or tuple of numbers.")
    if len(values) == 0:
        raise ValueError("Input must not be empty.")
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise TypeError(f"All values must be numbers, got {v!r}.")


def mean(values):
    """Average of the values."""
    _validate(values)
    return sum(values) / len(values)


def median(values):
    """Middle value (average of the two middle values for even-length input)."""
    _validate(values)
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def variance(values):
    """Population variance."""
    _validate(values)
    m = mean(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def std_dev(values):
    """Population standard deviation."""
    return math.sqrt(variance(values))


def min_max_normalize(values):
    """Scale values to the range [0, 1]. A constant list becomes all zeros."""
    _validate(values)
    lo, hi = min(values), max(values)
    if lo == hi:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def z_score(values):
    """Standardize values to mean 0 and std 1. A constant list becomes all zeros."""
    _validate(values)
    m = mean(values)
    sd = std_dev(values)
    if sd == 0:
        return [0.0 for _ in values]
    return [(v - m) / sd for v in values]


def describe(values):
    """Summary of the values, similar to pandas' describe()."""
    _validate(values)
    return {
        "count": len(values),
        "mean": mean(values),
        "median": median(values),
        "std": std_dev(values),
        "min": min(values),
        "max": max(values),
    }


def load_column(path, column):
    """Read one numeric column from a CSV file into a list of floats."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if column not in (reader.fieldnames or []):
            raise KeyError(f"Column '{column}' not found in {path}.")
        return [float(row[column]) for row in reader]
