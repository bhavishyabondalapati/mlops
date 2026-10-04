import math
import os

import pytest

from src import stats_utils as su

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sample_scores.csv")


@pytest.mark.parametrize(
    "values, expected",
    [
        ([1, 2, 3, 4], 2.5),
        ([10], 10),
        ([-5, 5], 0),
        ([1.5, 2.5], 2.0),
    ],
)
def test_mean(values, expected):
    assert su.mean(values) == pytest.approx(expected)


@pytest.mark.parametrize(
    "values, expected",
    [
        ([3, 1, 2], 2),          # odd length, unsorted
        ([4, 1, 3, 2], 2.5),     # even length
        ([7], 7),
    ],
)
def test_median(values, expected):
    assert su.median(values) == expected


def test_variance_and_std():
    values = [2, 4, 4, 4, 5, 5, 7, 9]
    assert su.variance(values) == pytest.approx(4.0)
    assert su.std_dev(values) == pytest.approx(2.0)


def test_min_max_normalize():
    assert su.min_max_normalize([0, 5, 10]) == [0.0, 0.5, 1.0]


def test_min_max_normalize_constant_list():
    assert su.min_max_normalize([3, 3, 3]) == [0.0, 0.0, 0.0]


def test_z_score_has_mean_zero_and_std_one():
    z = su.z_score([1, 2, 3, 4, 5])
    assert su.mean(z) == pytest.approx(0.0)
    assert su.std_dev(z) == pytest.approx(1.0)


def test_describe():
    d = su.describe([1, 2, 3])
    assert d["count"] == 3
    assert d["mean"] == 2
    assert d["min"] == 1 and d["max"] == 3
    assert d["std"] == pytest.approx(math.sqrt(2 / 3))


@pytest.mark.parametrize("func", [su.mean, su.median, su.variance, su.describe])
def test_empty_input_raises(func):
    with pytest.raises(ValueError):
        func([])


@pytest.mark.parametrize("bad", [[1, "two", 3], "123", [True, 2]])
def test_bad_input_raises(bad):
    with pytest.raises(TypeError):
        su.mean(bad)


def test_load_column_from_csv():
    scores = su.load_column(DATA_PATH, "exam_score")
    assert scores == [55.0, 62.0, 70.0, 74.0, 85.0, 92.0]


def test_load_missing_column_raises():
    with pytest.raises(KeyError):
        su.load_column(DATA_PATH, "not_a_column")
