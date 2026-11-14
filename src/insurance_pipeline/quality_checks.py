
import logging

from google.cloud import bigquery


logger = logging.getLogger(__name__)


def run_quality_checks(
    client: bigquery.Client,
    project_id: str,
    location: str,
    expected_raw: int,
    expected_clean: int,
    expected_rejected: int,
) -> None:
    """Verify data integrity after BigQuery loading."""

    query = f"""
    SELECT
        (SELECT COUNT(*)
         FROM `{project_id}.raw_dt.claims_raw`)
            AS raw_count,

        (SELECT COUNT(*)
         FROM `{project_id}.analytics_dt.claims_clean`)
            AS clean_count,

        (SELECT COUNT(*)
         FROM `{project_id}.analytics_dt.claims_rejected`)
            AS rejected_count,

        (SELECT COUNT(*) - COUNT(DISTINCT claim_id)
         FROM `{project_id}.analytics_dt.claims_clean`)
            AS duplicate_clean_ids
    """

    result = list(
        client.query(query, location=location).result()
    )[0]

    raw_count = result.raw_count
    clean_count = result.clean_count
    rejected_count = result.rejected_count
    duplicate_clean_ids = result.duplicate_clean_ids

    logger.info("Quality check counts | raw=%s clean=%s rejected=%s", raw_count, clean_count,rejected_count)

    if raw_count != expected_raw:
        raise ValueError(f"Raw count mismatch: {raw_count} != {expected_raw}")

    if clean_count != expected_clean:
        raise ValueError(f"Clean count mismatch: {clean_count} != {expected_clean}")

    if rejected_count != expected_rejected:
        raise ValueError(f"Rejected count mismatch: {rejected_count} != {expected_rejected}")

    if raw_count != clean_count + rejected_count:
        raise ValueError(f"Row conservation failed: {raw_count} != {clean_count} + {rejected_count}")

    if duplicate_clean_ids != 0:
        raise ValueError(
            f"Duplicate claim IDs in clean table: "
            f"{duplicate_clean_ids}"
        )

    logger.info("All BigQuery quality checks passed")
