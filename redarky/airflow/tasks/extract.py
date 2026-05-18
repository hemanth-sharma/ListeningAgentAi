import uuid
import requests

from airflow.pipeline_utils.logger import log
from airflow.pipeline_utils.config import (
    API_BASE_URL,
    DEFAULT_MISSION_ID,
    DEFAULT_QUERY,
)


def extract_sources(**context):
    """
    Call POST /scraper/run/{mission_id} on the FastAPI service.
    The FastAPI endpoint:
      1. Calls the Go scraper
      2. Validates items against ScrapedItem schema
      3. Writes raw JSON to local-S3 (raw/ layer)
      4. Returns { status, items_fetched, file_path }

    XCom output:
        batch_id  — unique batch UUID
        file_path — absolute path inside the container
        mission_id
        items_fetched
    """

    dag_run_conf = context["dag_run"].conf or {}

    mission_id = dag_run_conf.get(
        "mission_id",
        DEFAULT_MISSION_ID
    )

    query = dag_run_conf.get(
        "query",
        DEFAULT_QUERY
    )
    # subreddits = dag_run_conf.get("subreddits", json.loads(DEFAULT_SUBREDDITS))


    batch_id = str(uuid.uuid4())

    log.info(
        "extract.start",
        batch_id=batch_id,
        mission_id=mission_id,
    )

    response = requests.post(
        f"{API_BASE_URL}/scraper/run/{mission_id}",
        json={
            "query": query,
            # "subreddits": subreddits
        },
        timeout=120
    )

    response.raise_for_status()

    result = response.json()
    
    # Push to XCom for downstream tasks
    ti = context["ti"]
    ti.xcom_push(key="batch_id", value=batch_id)
    ti.xcom_push(key="mission_id", value=mission_id)
    ti.xcom_push(key="file_path", value=result["file_path"])
    ti.xcom_push(key="items_fetched", value=result["items_fetched"])

    log.info(
        "extract.done",
        batch_id=batch_id,
        items=result["items_fetched"]
    )