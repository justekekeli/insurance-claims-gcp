
import json
import logging
from decimal import Decimal

import pandas as pd
from google.cloud import bigquery


REQUIRED_COLUMNS = []
AMOUNT_COLUMNS = []
DATE_COLUMNS = []


with open("data/business_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    REQUIRED_COLUMNS = config["validation"]["required_columns"]
    AMOUNT_COLUMNS = config["validation"]["amount_columns"] + ["unreimbursed_amount"]
    DATE_COLUMNS = config["validation"]["date_columns"]


logger = logging.getLogger(__name__)

CLEAN_SCHEMA = [
    bigquery.SchemaField("claim_id", "STRING"),
    bigquery.SchemaField("policy_id", "STRING"),
    bigquery.SchemaField("claim_date", "DATE"),
    bigquery.SchemaField("declaration_date", "DATE"),
    bigquery.SchemaField("region", "STRING"),
    bigquery.SchemaField("vehicle_type", "STRING"),
    bigquery.SchemaField("claim_type", "STRING"),
    bigquery.SchemaField("claim_status", "STRING"),
    bigquery.SchemaField("claim_amount", "NUMERIC"),
    bigquery.SchemaField("reimbursement_amount", "NUMERIC"),
    bigquery.SchemaField("deductible_amount", "NUMERIC"),
    bigquery.SchemaField("source_row_number", "INTEGER"),
    bigquery.SchemaField("claim_year", "INTEGER"),
    bigquery.SchemaField("claim_month", "INTEGER"),
    bigquery.SchemaField("declaration_delay_days", "INTEGER"),
    bigquery.SchemaField("unreimbursed_amount", "NUMERIC"),
]

REJECTED_SCHEMA = [
    bigquery.SchemaField(column, "STRING")
    for column in REQUIRED_COLUMNS
] + [
    bigquery.SchemaField("source_row_number", "INTEGER"),
    bigquery.SchemaField("rejection_reasons", "STRING"),
]


def load_dataframe(client: bigquery.Client,dataframe: pd.DataFrame,table_id: str,schema: list[bigquery.SchemaField],location: str) -> None:
    """Charge a BigQuery table with the provided DataFrame."""

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
    )

    load_job = client.load_table_from_dataframe(
        dataframe,
        table_id,
        job_config=job_config,
        location=location,
    )

    load_job.result()

    table = client.get_table(table_id)

    logger.info(
        "Loaded %s rows into %s",
        table.num_rows,
        table_id,
    )


def load_curated_claims(client: bigquery.Client,valid_df: pd.DataFrame,rejected_df: pd.DataFrame,project_id: str,location: str) -> None:
    """Load clean and rejected claims into BigQuery."""

    clean_df = valid_df.copy()
    rejected_output = rejected_df.copy()

    # BigQuery DATE expects Python date values.
    for column in DATE_COLUMNS:
        clean_df[column] = clean_df[column].dt.date

    # BigQuery NUMERIC expects decimal-compatible values.
    
    # Convert financial amounts to Decimal objects.
    for column in AMOUNT_COLUMNS:
        clean_df[column] = pd.Series(
            [
                Decimal(str(value))
                if pd.notna(value)
                else None
                for value in clean_df[column]
            ],
            index=clean_df.index,
            dtype=object,
        )

    # Rejected records retain original source strings.
    for column in REQUIRED_COLUMNS:
        rejected_output[column] = (
            rejected_output[column].astype("string")
        )

    clean_table_id = (
        f"{project_id}.analytics_dt.claims_clean"
    )

    rejected_table_id = (
        f"{project_id}.analytics_dt.claims_rejected"
    )


    load_dataframe(
            client,
            clean_df,
            clean_table_id,
            CLEAN_SCHEMA,
            location,
        )

    load_dataframe(
        client,
        rejected_output,
        rejected_table_id,
        REJECTED_SCHEMA,
        location,
    )
