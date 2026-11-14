
import logging
import os
import time

from dotenv import load_dotenv
from google.cloud import bigquery

from .validation import validate_claims
from .transformation import transform_claims

from .load_in_bq import load_curated_claims

from .quality_checks import run_quality_checks


logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":

    start_time = time.perf_counter()

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
    
    logger.info("Loading curated and rejected records")

    load_curated_claims(
        client=client,
        valid_df=transformed_df,
        rejected_df=rejected_df,
        project_id=project_id,
        location=region
    )

    logger.info("BigQuery curated loading completed")

    logger.info("Running BigQuery quality checks")

    run_quality_checks(
        client=client,
        project_id=project_id,
        location=region,
        expected_raw=len(raw_df),
        expected_clean=len(transformed_df),
        expected_rejected=len(rejected_df)
    )

    duration = time.perf_counter() - start_time

    logger.info(
        "Pipeline completed successfully | duration=%.2fs",
        duration
    )