from __future__ import annotations

import pandas as pd

RISK_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def evaluate_governance_status(df: pd.DataFrame) -> pd.DataFrame:
    """Apply governance readiness rules to the service inventory."""
    result = df.copy()
    today = pd.Timestamp.today().normalize()
    result["next_review_date"] = pd.to_datetime(result["next_review_date"], errors="coerce")
    result["review_expired"] = result["next_review_date"].lt(today)

    def determine_status(row: pd.Series) -> str:
        if row["approval_status"] == "Not Approved":
            return "Not Ready"
        if row["ea_approval"] in {"Missing", "Pending"}:
            return "Architecture Review Required"
        if row["cada_approval"] in {"Missing", "Pending"}:
            return "Cloud Architecture Approval Required"
        if bool(row["review_expired"]):
            return "Review Expired"
        if row["risk_level"] == "Critical":
            return "Executive Risk Review Required"
        if row["approval_status"] == "Conditional":
            return "Conditionally Ready"
        if row["approval_status"] == "Under Review":
            return "Under Review"
        return "Ready"

    result["governance_readiness"] = result.apply(determine_status, axis=1)
    result["risk_score"] = result["risk_level"].map(RISK_ORDER).fillna(0).astype(int)
    return result
