import json

import pandas as pd

REGIONS = []
CLAIM_TYPES = []
REQUIRED_COLUMNS = []
AMOUNT_COLUMNS = []
DATE_COLUMNS = []


with open("data/business_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    REGIONS = config["regions"]
    CLAIM_TYPES = config["claim_types"]
    REQUIRED_COLUMNS = config["validation"]["required_columns"]
    AMOUNT_COLUMNS = config["validation"]["amount_columns"]
    DATE_COLUMNS = config["validation"]["date_columns"]

def validate_claims(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate claims data.

    Args:
        df (pd.DataFrame): DataFrame containing claims data.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: Tuple containing valid and invalid DataFrames.
    """
    # Check for missing required columns
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    data = df.copy()

    # Preserve original row order for traceability.
    data["source_row_number"] = range(1, len(data) + 1)

    # One row may contain several errors.
    data["rejection_reasons"] = [
        [] for _ in range(len(data))
    ]

    def add_reason(mask: pd.Series, reason: str) -> None:
        positions = mask.fillna(False).to_numpy(dtype=bool)

        for i, invalid in enumerate(positions):
            if invalid:
                data["rejection_reasons"].iat[i].append(reason)

    # Mandatory identifiers.
    missing_id = (
        data["claim_id"].isna()
        | data["claim_id"].astype("string").str.strip().eq("")
    )
    add_reason(missing_id, "MISSING_ID")

    # Reject every occurrence of a duplicate identifier.
    duplicate_id = (
        data["claim_id"].notna()
        & data["claim_id"].duplicated(keep=False)
    )
    add_reason(duplicate_id, "DUPLICATE_ID")

    # Mandatory policy identifier.
    invalid_policy = (
        data["policy_id"].isna()
        | data["policy_id"].astype("string").str.strip().eq("")
    )
    add_reason(invalid_policy, "INVALID_POLICY_ID")

    # Categorical validation.
    add_reason(
        ~data["region"].isin(REGIONS),
        "INVALID_REGION",
    )
    add_reason(
        ~data["claim_type"].isin(CLAIM_TYPES),
        "INVALID_CLAIM_TYPE",
    )

    # Convert amounts while detecting malformed values.
    for column in AMOUNT_COLUMNS:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        add_reason(
            data[column].isna() | (data[column] < 0),
            f"INVALID_{column.upper()}",
        )

    # Convert ISO dates.
    for column in DATE_COLUMNS:
        data[column] = pd.to_datetime(
            data[column],
            format="%Y-%m-%d",
            errors="coerce",
        )

        add_reason(
            data[column].isna(),
            f"INVALID_{column.upper()}",
        )

    # Business consistency checks.
    add_reason(
        data["declaration_date"] < data["claim_date"],
        "DECLARATION_BEFORE_CLAIM",
    )

    add_reason(
        data["reimbursement_amount"] > data["claim_amount"],
        "REIMBURSEMENT_EXCEEDS_CLAIM",
    )

    
    # Split valid and rejected records.
    rejected_mask = data["rejection_reasons"].map(bool)

    valid_df = data.loc[~rejected_mask].copy()

    # Preserve original source values for rejected records.
    rejected_df = df.loc[rejected_mask].copy()

    rejected_df["source_row_number"] = (
        data.loc[rejected_mask, "source_row_number"]
    )

    rejected_df["rejection_reasons"] = (
        data.loc[rejected_mask, "rejection_reasons"]
        .map(lambda reasons: "|".join(reasons))
    )

    valid_df = valid_df.drop(columns=["rejection_reasons"])



    return valid_df, rejected_df
