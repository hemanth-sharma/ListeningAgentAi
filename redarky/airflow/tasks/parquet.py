from pathlib import Path
from datetime import datetime, UTC

import pandas as pd

from airflow.pipeline_utils.files import load_json
from airflow.pipeline_utils.logger import log
from airflow.pipeline_utils.config import S3_BASE_PATH


def convert_to_parquet(**context):
    """
    Read cleaned JSON, write to Parquet under processed/ layer.
    Layout: processed/{mission_id}/{date}/{batch_id}.parquet
    """

    ti = context["ti"]

    cleaned_path = ti.xcom_pull(
        task_ids="clean_deduplicate",
        key="cleaned_file_path"
    )

    mission_id = ti.xcom_pull(
        task_ids="extract_sources",
        key="mission_id"
    )

    batch_id = ti.xcom_pull(
        task_ids="extract_sources",
        key="batch_id"
    )

    items = load_json(cleaned_path)

    df = pd.DataFrame(items)

    date_partition = datetime.now(
        UTC
    ).strftime("%Y-%m-%d")

    parquet_dir = (
        Path(S3_BASE_PATH)
        / "processed"
        / mission_id
        / date_partition
    )

    parquet_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    parquet_path = parquet_dir / f"{batch_id}.parquet"

    df.to_parquet(
        parquet_path,
        index=False,
        engine="pyarrow"
    )

    ti.xcom_push(
        key="parquet_path",
        value=str(parquet_path)
    )

    log.info(
        "parquet.done",
        path=str(parquet_path)
    )