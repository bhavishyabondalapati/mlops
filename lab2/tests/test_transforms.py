import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from transforms import format_client, mlr, parse_row  # noqa: E402


def test_parse_valid_row():
    row = parse_row("C001,2025-01,100,50000.0,40000.0")
    assert row["client_id"] == "C001"
    assert row["members"] == 100
    assert row["claims_paid"] == 40000.0


def test_parse_quoted_field():
    row = parse_row('"C001",2025-01,100,50000.0,40000.0')
    assert row["client_id"] == "C001"


@pytest.mark.parametrize("line", [
    "C001,2025-01,100,50000.0,",          # missing claims
    "C001,2025-01,100",                   # too few columns
    ",2025-01,100,50000.0,40000.0",       # missing client
    "C001,2025-01,0,50000.0,40000.0",     # zero members
    "C001,2025-01,100,0,40000.0",         # zero premium
    "C001,2025-01,100,50000.0,-5",        # negative claims
    "C001,2025-01,100,50000.0,nan",       # not a real number
])
def test_parse_bad_rows(line):
    with pytest.raises(ValueError):
        parse_row(line)


def test_mlr_is_not_rounded():
    # 1.00004 must count as above a threshold of 1.0
    assert mlr(100000.0, 100004.0) > 1.0


def test_format_client():
    assert format_client("C001", (100.0, 50.0, 12)) == "C001,12,100.00,50.00,0.5"
