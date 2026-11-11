
import pandas as pd
import pytest

from src.insurance_pipeline.validation import validate_claims


@pytest.fixture
def valid_claim():
    return {
        "claim_id": "CLM-000001",
        "policy_id": "POL-000001",
        "claim_date": "2025-01-10",
        "declaration_date": "2025-01-12",
        "region": "Normandie",
        "vehicle_type": "SUV",
        "claim_type": "Collision",
        "claim_status": "Closed",
        "claim_amount": "4250.50",
        "reimbursement_amount": "3500.00",
        "deductible_amount": "500.00",
    }


def test_negative_claim_amount_is_rejected():
    # Arrange: prepare a synthetic claim
    df = pd.DataFrame([{
        "claim_id": "CLM-000001",
        "policy_id": "POL-000001",
        "claim_date": "2025-01-10",
        "declaration_date": "2025-01-12",
        "region": "Normandie",
        "vehicle_type": "SUV",
        "claim_type": "Collision",
        "claim_status": "Closed",
        "claim_amount": "-1500",
        "reimbursement_amount": "0",
        "deductible_amount": "300",
    }])

    # Act: execute the validation function
    valid_df, rejected_df = validate_claims(df)

    # Assert: verify expected behavior
    assert len(valid_df) == 0
    assert len(rejected_df) == 1

    assert (
        "INVALID_CLAIM_AMOUNT"
        in rejected_df.iloc[0]["rejection_reasons"]
    )


def test_missing_region_is_rejected(valid_claim):
    claim = valid_claim.copy()
    claim["region"] = None

    valid_df, rejected_df = validate_claims(
        pd.DataFrame([claim])
    )

    assert len(valid_df) == 0
    assert len(rejected_df) == 1
    assert "INVALID_REGION" in (
        rejected_df.iloc[0]["rejection_reasons"]
    )


def test_duplicate_claim_ids_are_rejected(valid_claim):
    first_claim = valid_claim.copy()
    second_claim = valid_claim.copy()

    second_claim["policy_id"] = "POL-000002"

    valid_df, rejected_df = validate_claims(
        pd.DataFrame([first_claim, second_claim])
    )

    assert len(valid_df) == 0
    assert len(rejected_df) == 2

    assert all(
        rejected_df["rejection_reasons"]
        .str.contains("DUPLICATE_ID")
    )


def test_declaration_before_claim_is_rejected(valid_claim):
    claim = valid_claim.copy()
    claim["declaration_date"] = "2025-01-05"

    valid_df, rejected_df = validate_claims(
        pd.DataFrame([claim])
    )

    assert len(valid_df) == 0
    assert "DECLARATION_BEFORE_CLAIM" in (
        rejected_df.iloc[0]["rejection_reasons"]
    )


def test_excessive_reimbursement_is_rejected(valid_claim):
    claim = valid_claim.copy()
    claim["reimbursement_amount"] = "5000.00"

    valid_df, rejected_df = validate_claims(
        pd.DataFrame([claim])
    )

    assert len(valid_df) == 0
    assert "REIMBURSEMENT_EXCEEDS_CLAIM" in (
        rejected_df.iloc[0]["rejection_reasons"]
    )


def test_valid_claim_is_accepted(valid_claim):
    valid_df, rejected_df = validate_claims(
        pd.DataFrame([valid_claim])
    )

    assert len(valid_df) == 1
    assert len(rejected_df) == 0


def test_missing_required_column_raises_error(valid_claim):
    claim = valid_claim.copy()
    del claim["claim_amount"]

    with pytest.raises(ValueError, match="Missing required columns\\: \\['claim_amount'\\]"):
        validate_claims(pd.DataFrame([claim]))

def test_multiple_rejection_reasons(valid_claim):
    claim = valid_claim.copy()
    claim["region"] = None
    claim["claim_amount"] = "-100"

    valid_df, rejected_df = validate_claims(
        pd.DataFrame([claim])
    )

    assert len(valid_df) == 0
    assert len(rejected_df) == 1

    reasons = rejected_df.iloc[0]["rejection_reasons"]

    assert "INVALID_REGION" in reasons
    assert "INVALID_CLAIM_AMOUNT" in reasons