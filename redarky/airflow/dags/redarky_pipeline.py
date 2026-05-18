from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from tasks.extract import extract_sources
from tasks.validate import validate_schema
from tasks.deduplicate import clean_deduplicate
from tasks.parquet import convert_to_parquet

default_args = {
    "owner": "redarky",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="redarky_pipeline",
    default_args=default_args,
    description="Redarky pipeline",
    start_date=days_ago(1),
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

    parquet_task = PythonOperator(
        task_id="convert_to_parquet",
        python_callable=convert_to_parquet,
    )

    (
        extract_task
        >> validate_task
        >> deduplicate_task
        >> parquet_task
    )