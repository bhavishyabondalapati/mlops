"""Plain Python helpers used by the Beam pipeline (easy to unit test)."""
import csv
import math

HEADER = "client_id,month,members,premium,claims_paid"


def parse_row(line: str) -> dict:
    """Turn one CSV line into a dict. Raises ValueError if the row is bad."""
    parts = next(csv.reader([line]))
    if len(parts) != 5:
        raise ValueError(f"expected 5 columns but got {len(parts)}")
    client_id, month, members, premium, claims = (p.strip() for p in parts)
    if not client_id or not month:
        raise ValueError("missing client_id or month")
    # Missing claims are treated as invalid, not as zero: a blank usually means
    # the data hasn't arrived yet, and counting it as 0 would make MLR look too good.
    if not claims:
        raise ValueError("missing claims_paid")

    row = {
        "client_id": client_id,
        "month": month,
        "members": int(members),
        "premium": float(premium),
        "claims_paid": float(claims),
    }
    if not (math.isfinite(row["premium"]) and math.isfinite(row["claims_paid"])):
        raise ValueError("premium and claims must be real numbers")
    if row["members"] <= 0:
        raise ValueError("members must be > 0")
    if row["premium"] <= 0 or row["claims_paid"] < 0:
        raise ValueError("premium must be > 0 and claims must be >= 0")
    return row


def mlr(premium: float, claims: float) -> float:
    """Medical Loss Ratio (claims / premium). Not rounded, so threshold checks are exact."""
    return claims / premium if premium else 0.0


def format_client(client_id: str, totals: tuple) -> str:
    premium, claims, months = totals
    return f"{client_id},{months},{premium:.2f},{claims:.2f},{round(mlr(premium, claims), 4)}"
