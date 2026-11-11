
import pandas as pd
import pytest

from src.insurance_pipeline.transformation import transform_claims


def test_claim_transformation():
    df = pd.DataFrame([{
        "claim_id": "CLM-000001",
        "claim_date": pd.Timestamp("2025-03-10"),
        "declaration_date": pd.Timestamp("2025-03-13"),
        "claim_amount": 5000.00,
        "reimbursement_amount": 4200.00,
    }])

    result = transform_claims(df)

    assert result.iloc[0]["claim_year"] == 2025
    assert result.iloc[0]["claim_month"] == 3
    assert result.iloc[0]["declaration_delay_days"] == 3

    assert result.iloc[0]["unreimbursed_amount"] == pytest.approx(
        800.00
    )
