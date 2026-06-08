import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from psycopg2.extras import execute_values

from pipeline.monitoring.batch_tracker import track_pipeline_event
from pipeline.metrics.ingestion_metrics import record_ingestion_metrics
from pipeline.utils.database import get_postgres_connection
from pipeline.utils.logger import log


BATCH_SIZE = 500


def load_postgresql(**context: Any) -> None:
    """
    PostgreSQL bulk loader.

    Features:
    - Batch inserts
    - ON CONFLICT deduplication
    - Structured logging
    - Metrics tracking
    - Failure observability
    - Retry-safe transactions
    """

    start_time = time.time()

    ti = context["ti"]

    cleaned_path: str = ti.xcom_pull(
        task_ids="clean_deduplicate",
        key="cleaned_file_path",
    )

    batch_id: str = ti.xcom_pull(
        task_ids="extract_sources",
        key="batch_id",
    )

    mission_id: str = ti.xcom_pull(
        task_ids="extract_sources",
        key="mission_id",
    )

    log.info(
        "load_postgresql.start",
        batch_id=batch_id,
        mission_id=mission_id,
        cleaned_path=cleaned_path,
    )

    items: list[dict] = json.loads(
        Path(cleaned_path).read_text(encoding="utf-8")
    )

    if not items:
        log.warning(
            "load_postgresql.empty",
            batch_id=batch_id,
        )

        ti.xcom_push(key="inserted_count", value=0)
        ti.xcom_push(key="skipped_count", value=0)
        ti.xcom_push(key="inserted_ids", value=[])

        return

    conn = get_postgres_connection()

    inserted_ids = []

    try:
        with conn.cursor() as cur:

            rows = []

            for item in items:
                rows.append(
                    (
                        str(uuid.uuid4()),
                        mission_id,
                        item.get("source", ""),
                        item.get("external_id", ""),
                        item.get("dedup_hash", ""),
                        item.get("title"),
                        item.get("content"),
                        item.get("url", ""),
                        item.get("author"),
                        item.get("score", 0),
                        None,
                        None,
                        item.get("scraped_at"),
                        datetime.now(UTC),
                    )
                )

            insert_sql = """
                INSERT INTO data_items
                (
                    id,
                    mission_id,
                    source,
                    external_id,
                    dedup_hash,
                    title,
                    content,
                    url,
                    author,
                    score,
                    classification,
                    sentiment_score,
                    scraped_at,
                    created_at
                )
                VALUES %s
                ON CONFLICT (mission_id, dedup_hash)
                DO NOTHING
                RETURNING id
            """

            execute_values(
                cur,
                insert_sql,
                rows,
                page_size=BATCH_SIZE,
            )

            returned = cur.fetchall()

            inserted_ids = [str(r[0]) for r in returned]

            conn.commit()

        inserted_count = len(inserted_ids)
        skipped_count = len(items) - inserted_count

        duration = round(time.time() - start_time, 2)

        log.info(
            "load_postgresql.done",
            batch_id=batch_id,
            inserted_count=inserted_count,
            skipped_count=skipped_count,
            duration_seconds=duration,
        )

        record_ingestion_metrics(
            batch_id=batch_id,
            mission_id=mission_id,
            inserted=inserted_count,
            skipped=skipped_count,
            duration_seconds=duration,
        )

        track_pipeline_event(
            batch_id=batch_id,
            stage="load_postgresql",
            status="success",
            metadata={
                "inserted": inserted_count,
                "skipped": skipped_count,
                "duration_seconds": duration,
            },
        )

        ti.xcom_push(key="inserted_count", value=inserted_count)
        ti.xcom_push(key="skipped_count", value=skipped_count)
        ti.xcom_push(key="inserted_ids", value=inserted_ids)

    except Exception as e:

        conn.rollback()

        log.exception(
            "load_postgresql.failed",
            batch_id=batch_id,
            error=str(e),
        )

        track_pipeline_event(
            batch_id=batch_id,
            stage="load_postgresql",
            status="failed",
            metadata={"error": str(e)},
        )

        raise

    finally:
        conn.close()