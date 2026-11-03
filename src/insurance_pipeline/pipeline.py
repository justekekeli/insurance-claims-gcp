
import logging
import os

from dotenv import load_dotenv
from google.cloud import bigquery

from .validation import validate_claims
from .transformation import transform_claims


logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)


def main() -> None:
    load_dotenv()

    project_id = os.environ["GCP_PROJECT_ID"]
    region = os.environ["GCP_REGION"]

    client = bigquery.Client(
        project=project_id,
        location=region,
    )

    query = f"""
        SELECT 
            claim_id,
            policy_id,
            claim_date,
            declaration_date,
            region,
            vehicle_type,
            claim_type,
            claim_status,
            claim_amount,
            reimbursement_amount,
            deductible_amount
        FROM `{project_id}.raw_dt.claims_raw`
        ORDER BY claim_id, policy_id
    """

    logger.info("Reading BigQuery Raw data from table: %s", 
        f"{project_id}.raw_dt.claims_raw"
    )

    raw_df = client.query(
        query,
        location=region,
    ).to_dataframe()

    logger.info("Raw records: %s", len(raw_df))

    valid_df, rejected_df = validate_claims(raw_df)
    transformed_df = transform_claims(valid_df)

    print(
    transformed_df[[ "claim_id","claim_year","claim_month","declaration_delay_days","unreimbursed_amount",]].head()
)

    logger.info("Valid records: %s", len(transformed_df))
    logger.info("Rejected records: %s", len(rejected_df))

    quality_rate = (
        len(transformed_df) / len(raw_df) * 100
        if len(raw_df) > 0 else 0
    )

    logger.info("Data quality rate: %.2f%%", quality_rate)

    if not rejected_df.empty:
        logger.info("Rejection reasons:")
        logger.info(
            "\n%s",
            rejected_df[
                ["claim_id", "rejection_reasons"]
            ].to_string(index=False),
        )

    logger.info("Transformation completed successfully")


if __name__ == "__main__":
    main()
