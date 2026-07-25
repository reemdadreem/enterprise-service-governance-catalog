import pandas as pd
from scripts.governance_rules import evaluate_governance_status


def test_missing_architecture_approval_is_not_ready():
    df = pd.DataFrame([{
        "approval_status": "Approved",
        "ea_approval": "Missing",
        "cada_approval": "Approved",
        "next_review_date": "2099-01-01",
        "risk_level": "Low",
    }])
    result = evaluate_governance_status(df)
    assert result.loc[0, "governance_readiness"] == "Architecture Review Required"
