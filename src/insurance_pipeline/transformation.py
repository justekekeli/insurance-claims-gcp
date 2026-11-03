
import pandas as pd


def transform_claims(df: pd.DataFrame) -> pd.DataFrame:
    """Add analytical features to validated claims."""

    data = df.copy()

    data["claim_year"] = data["claim_date"].dt.year
    data["claim_month"] = data["claim_date"].dt.month

    data["declaration_delay_days"] = (
        data["declaration_date"] - data["claim_date"]
    ).dt.days

    data["unreimbursed_amount"] = (
        data["claim_amount"]
        - data["reimbursement_amount"]
    ).round(2)

    return data
