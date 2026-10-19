"""Plain Python helpers used by the Beam pipeline (easy to unit test)."""

HEADER = "client_id,month,members,premium,claims_paid"


def parse_row(line: str) -> dict:
    """Turn one CSV line into a dict. Raises ValueError if the row is bad."""
    parts = line.strip().split(",")
    if len(parts) != 5:
        raise ValueError(f"expected 5 columns but got {len(parts)}")
    client_id, month, members, premium, claims = parts
    if not client_id or not month:
        raise ValueError("missing client_id or month")
    if not claims:
        raise ValueError("missing claims_paid")
    row = {
        "client_id": client_id,
        "month": month,
        "members": int(members),
        "premium": float(premium),
        "claims_paid": float(claims),
    }
    if row["premium"] <= 0 or row["claims_paid"] < 0:
        raise ValueError("premium must be > 0 and claims must be >= 0")
    return row


def mlr(premium: float, claims: float) -> float:
    """Medical Loss Ratio: share of premium spent on claims."""
    return round(claims / premium, 4) if premium else 0.0


def format_client(client_id: str, totals: tuple) -> str:
    premium, claims, months = totals
    return f"{client_id},{months},{premium:.2f},{claims:.2f},{mlr(premium, claims)}"
