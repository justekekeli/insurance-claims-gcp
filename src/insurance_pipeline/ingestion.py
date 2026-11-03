import logging
import os 

from dotenv import load_dotenv
from google.cloud import bigquery


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

COLUMNS = [
    "claim_id",
    "policy_id",
    "claim_date",
    "declaration_date",
    "region",
    "vehicle_type",
    "claim_type",
    "claim_status",
    "claim_amount",
    "reimbursement_amount",
    "deductible_amount",
]

def load_raw_claims()-> None:
    """Load raw claims data into BigQuery."""

    load_dotenv()

    project_id = os.environ["GCP_PROJECT_ID"]
    region = os.environ["GCP_REGION"]
    bucket_name = os.environ["GCS_BUCKET_NAME"]
    blob_name = os.environ["GCS_SOURCE_BLOB"]
    

    client = bigquery.Client(project=project_id)

    source_uri = f"gs://{bucket_name}/{blob_name}"
    table_id = f"{project_id}.raw_dt.claims_raw"

    schema = [
        bigquery.SchemaField(column, "STRING")
        for column in COLUMNS
    ]

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=False,
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        max_bad_records=0,
        encoding="UTF-8",
    )

    logger.info(f"Loading data from {source_uri} into {table_id}...")

    load_job = client.load_table_from_uri(
            source_uri, 
            table_id, 
            job_config=job_config,
            location=region
    )

    load_job.result()  # Wait for the job to complete.

    table = client.get_table(table_id)  # Make an API request.

    logger.info(f"Loaded {table.num_rows} rows into {table_id}.")

    if table.num_rows != 5000:
        raise ValueError(f"Expected 5000 rows, but loaded {table.num_rows} rows into {table_id}.")

if __name__ == "__main__":
    load_raw_claims()
