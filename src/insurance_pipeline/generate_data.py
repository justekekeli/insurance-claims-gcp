
import json
from pathlib import Path
from datetime import date, timedelta
import random

import numpy as np
import pandas as pd
from faker import Faker


SEED = 42
NB_CLAIMS = 5000
OUTPUT_PATH = Path("data/sample/claims.csv")
CONFIG_PATH = Path("data/business_config.json")
REGIONS = []
CLAIM_TYPES = []
CLAIM_STATUSES = []
AMOUNT_RANGES = {}
VEHICLE_TYPES = []

CLAIM_PROBABILITIES = [0.40, 0.25, 0.12, 0.08, 0.15]

def initialize_variables():
    global REGIONS, CLAIM_TYPES, CLAIM_STATUSES, AMOUNT_RANGES, VEHICLE_TYPES

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
        REGIONS = config["regions"]
        CLAIM_TYPES = config["claim_types"]
        CLAIM_STATUSES = config["claim_statuses"]

        for k,v in config["claim_amount_ranges"].items():
            AMOUNT_RANGES[k] = tuple(v)

        VEHICLE_TYPES = config["vehicle_types"]

def generate_claims(n: int = NB_CLAIMS) -> pd.DataFrame:
    """Generate reproducible synthetic automobile claims."""

    if n <= 0:
        raise ValueError("n must be a positive integer")

    Faker.seed(SEED)
    fake = Faker("fr_FR")
    rng = np.random.default_rng(SEED)
    random.seed(SEED)

    claims = []
    start_date = date(2023, 1, 1)
    end_date = date(2025, 12, 31)
    days_range = (end_date - start_date).days

    for i in range(1, n + 1):
        claim_type = rng.choice(
            CLAIM_TYPES,
            p=CLAIM_PROBABILITIES,
        )

        min_amount, max_amount = AMOUNT_RANGES[claim_type]

        claim_amount = round(
            float(rng.uniform(min_amount, max_amount)), 2
        )

        deductible = float(
            rng.choice([0, 150, 300, 500, 750])
        )

        reimbursement = round(
            max(0, claim_amount - deductible)
            * float(rng.uniform(0.7, 1.0)),
            2,
        )

        claim_date = start_date + timedelta(
            days=int(rng.integers(0, days_range + 1))
        )

        declaration_date = claim_date + timedelta(
            days=int(rng.integers(0, 16))
        )

        claim_status = rng.choice(
            CLAIM_STATUSES,
            p=[0.15, 0.25, 0.50, 0.10],
        )

        claims.append({
            "claim_id": f"CLM-{i:06d}",
            "policy_id": f"POL-{int(rng.integers(1, 3001)):06d}",
            "claim_date": claim_date.isoformat(),
            "declaration_date": declaration_date.isoformat(),
            "region": fake.random_element(REGIONS),
            "vehicle_type": rng.choice(
                VEHICLE_TYPES,
            ),
            "claim_type": claim_type,
            "claim_status": claim_status,
            "claim_amount": claim_amount,
            "reimbursement_amount": reimbursement,
            "deductible_amount": deductible,
        })

    return pd.DataFrame(claims)


def inject_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Inject deterministic data quality anomalies."""

    df = df.copy()

    # Missing mandatory region
    df.loc[0, "region"] = None

    # Negative claim amount
    df.loc[1, "claim_amount"] = -1500.0

    # Invalid declaration date
    df.loc[2, "declaration_date"] = "2020-01-01"

    # Reimbursement greater than claim amount
    df.loc[3, "reimbursement_amount"] = float(df.loc[3, "claim_amount"]) + 1000.0

    # Duplicate claim identifier
    df.loc[4, "claim_id"] = df.loc[5, "claim_id"]

    return df



if __name__ == "__main__":

    initialize_variables() 

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    df = generate_claims()
    df = inject_anomalies(df)

    df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8",
    )

    print(f"Generated {len(df)} claims")
    print(f"Output: {OUTPUT_PATH}")
    #print(df.head())
