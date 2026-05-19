import hashlib
from pathlib import Path

from pipeline.utils.files import load_json, save_json
from pipeline.utils.logger import log


def clean_deduplicate(**context):
    """
    Read validated JSON, compute SHA-256 dedup_hash per item,
    drop in-batch duplicates (cross-batch dedup handled by DB UPSERT).
    Normalise text fields (strip whitespace, truncate content).

    XCom output: cleaned_file_path, unique_count
    """

    ti = context["ti"]

    path = ti.xcom_pull(
        task_ids="validate_schema",
        key="validated_file_path"
    )
    ti = context["ti"]
    # validated_path: str = ti.xcom_pull(task_ids="validate_schema", key="validated_file_path")
    # batch_id: str = ti.xcom_pull(task_ids="extract_sources", key="batch_id")
    # mission_id: str = ti.xcom_pull(task_ids="extract_sources", key="mission_id")


    items = load_json(path)

    seen = set()
    cleaned = []

    for item in items:

        dedup_hash = hashlib.sha256(
            f"{item['source']}:{item['external_id']}".encode()
        ).hexdigest()

        item["dedup_hash"] = dedup_hash

        if dedup_hash not in seen:
            seen.add(dedup_hash)
            cleaned.append(item)

    cleaned_path = str(
        Path(path).with_suffix(".cleaned.json")
    )

    save_json(cleaned_path, cleaned)

    ti.xcom_push(
        key="cleaned_file_path",
        value=cleaned_path
    )

    ti.xcom_push(
        key="unique_count",
        value=len(cleaned)
    )

    log.info(
        "deduplicate.done",
        unique=len(cleaned)
    )