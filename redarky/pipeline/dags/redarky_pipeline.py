"""
redarky_pipeline.py  —  MYM-28 through MYM-41
=================================================
Main Airflow DAG for the RedArky data pipeline.

Task flow (Stage 1 + Stage 2):
  extract_sources
      → validate_schema
          → clean_deduplicate
              → load_postgresql
                  → convert_to_parquet
                      → generate_embeddings   (Stage 3)
                          → log_batch_metadata

Retry policy: 3 retries, 5-minute delay (scraper tasks).
Structured JSON logging via structlog throughout.
"""

import os
import sys
from datetime import datetime

PIPELINE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Inject it into Python's search paths so 'tasks' and 'utils' become direct modules
if PIPELINE_ROOT not in sys.path:
    sys.path.insert(0, PIPELINE_ROOT)

from datetime import timedelta, datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
# from pipeline.utils.dates import days_ago
from pipeline.utils.retry import DEFAULT_RETRY_POLICY

from pipeline.tasks.extract import extract_sources
from pipeline.tasks.validate import validate_schema
from pipeline.tasks.deduplicate import clean_deduplicate
from pipeline.tasks.parquet import convert_to_parquet
from pipeline.tasks.load_postgres import load_postgresql
from pipeline.tasks.embeddings import generate_embeddings


default_args = {
    "owner": "redarky",
    "depends_on_past": False,
    **DEFAULT_RETRY_POLICY,
    # 'start_date': datetime(2026, 1, 1),
}

with DAG(
    dag_id="redarky_pipeline",
    default_args=default_args,
    description="Redarky pipeline",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    schedule="@daily",
    max_active_runs=1,
    tags=["redarky"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_sources",
        python_callable=extract_sources,
    )

    validate_task = PythonOperator(
        task_id="validate_schema",
        python_callable=validate_schema,
    )

    deduplicate_task = PythonOperator(
        task_id="clean_deduplicate",
        python_callable=clean_deduplicate,
    )

    load_postgres_task = PythonOperator(
        task_id="load_postgresql",
        python_callable=load_postgresql,
    )

    parquet_task = PythonOperator(
        task_id="convert_to_parquet",
        python_callable=convert_to_parquet,
    )

    embeddings_task = PythonOperator(
        task_id="generate_embeddings",
        python_callable=generate_embeddings,
    )

    (
        extract_task
        >> validate_task
        >> deduplicate_task
        >> [load_postgres_task, parquet_task]
    )
    
    load_postgres_task >> embeddings_task

    # (
    #     extract_task
    #     >> validate_task
    #     >> deduplicate_task
    #     >> parquet_task
    # )