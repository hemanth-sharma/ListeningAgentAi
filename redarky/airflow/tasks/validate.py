from pathlib import Path

from airflow.pipeline_utils.logger import log
from airflow.pipeline_utils.files import load_json, save_json
from airflow.pipeline_utils.config import S3_BASE_PATH
import json


REQUIRED_FIELDS = {
    "source",
    "external_id",
    "title",
    "url",
    "scraped_at",
}


def validate_schema(**context):
    """
    Read the raw JSON written by extract_sources and re-validate
    each item against a lightweight inline schema.
    Rejects and quarantines bad records to dead_letter/.
    
    XCom output: validated_file_path, valid_count, rejected_count
    """

    ti = context["ti"]

    file_path = ti.xcom_pull(
        task_ids="extract_sources",
        key="file_path"
    )
    batch_id: str = ti.xcom_pull(task_ids="extract_sources", key="batch_id")
    mission_id: str = ti.xcom_pull(task_ids="extract_sources", key="mission_id")


    items = load_json(file_path)

    valid = []
    rejected = []

    for item in items:

        missing = REQUIRED_FIELDS - set(item.keys())

        if missing:
            rejected.append(item)
        else:
            valid.append(item)

    validated_path = str(
        Path(file_path).with_suffix(".validated.json")
    )

    save_json(validated_path, valid)
    if rejected:
        dead_letter_dir = Path(S3_BASE_PATH) / "dead_letter" / mission_id
        dead_letter_dir.mkdir(parents=True, exist_ok=True)
        dl_path = dead_letter_dir / f"{batch_id}_rejected.json"
        dl_path.write_text(json.dumps(rejected, ensure_ascii=True), encoding="utf-8")


    ti.xcom_push(
        key="validated_file_path",
        value=validated_path
    )

    ti.xcom_push(
        key="valid_count",
        value=len(valid)
    )

    ti.xcom_push(
        key="rejected_count",
        value=len(rejected)
    )

    log.info(
        "validate.done",
        valid=len(valid),
        rejected=len(rejected),
    )