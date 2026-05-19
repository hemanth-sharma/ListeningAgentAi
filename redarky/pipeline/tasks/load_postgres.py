import json
from pipeline.utils.logger import log
from pipeline.utils.database import get_postgres_connection
from pathlib import Path
from typing import Any
from psycopg2.extras import execute_values
import uuid
from datetime import UTC, datetime, timedelta



def load_postgresql(**context: Any) -> None:
    """
    Bulk-insert cleaned items into data_items table using a single
    executemany statement with ON CONFLICT DO NOTHING (dedup by mission+hash).

    XCom output: inserted_count, skipped_count, inserted_ids
    """

    ti = context["ti"]
    cleaned_path: str = ti.xcom_pull(task_ids="clean_deduplicate", key="cleaned_file_path")
    batch_id: str = ti.xcom_pull(task_ids="extract_sources", key="batch_id")
    mission_id: str = ti.xcom_pull(task_ids="extract_sources", key="mission_id")

    log.info("load_postgresql.start", batch_id=batch_id, mission_id=mission_id)

    items: list[dict] = json.loads(Path(cleaned_path).read_text(encoding="utf-8"))
    if not items:
        log.warning("load_postgresql.empty", batch_id=batch_id)
        ti.xcom_push(key="inserted_count", value=0)
        ti.xcom_push(key="skipped_count", value=0)
        ti.xcom_push(key="inserted_ids", value=[])
        return

    # Build psycopg2 connection (sync — fine for Airflow tasks)
    conn = get_postgres_connection()

    try:
        with conn.cursor() as cur:
            rows = [
                (
                    str(uuid.uuid4()),        # id
                    mission_id,               # mission_id
                    item.get("source", ""),   # source
                    item.get("external_id", ""),  # external_id
                    item.get("dedup_hash", ""),   # dedup_hash
                    item.get("title"),        # title
                    item.get("content"),      # content
                    item.get("url", ""),      # url
                    item.get("author"),       # author
                    item.get("score", 0),     # score
                    None,                     # classification
                    None,                     # sentiment_score
                    item.get("scraped_at"),   # scraped_at
                    datetime.now(UTC).isoformat(),  # created_at
                )
                for item in items
            ]

            # Bulk upsert — ON CONFLICT DO NOTHING returns only actually inserted rows
            insert_sql = """
                INSERT INTO data_items
                  (id, mission_id, source, external_id, dedup_hash,
                   title, content, url, author, score,
                   classification, sentiment_score, scraped_at, created_at)
                VALUES %s
                ON CONFLICT (mission_id, dedup_hash) DO NOTHING
                RETURNING id
            """
            execute_values(cur, insert_sql, rows, page_size=500)
            inserted_ids = [str(row[0]) for row in cur.fetchall()]
            conn.commit()

        inserted_count = len(inserted_ids)
        skipped_count = len(items) - inserted_count

        log.info(
            "load_postgresql.done",
            batch_id=batch_id,
            inserted=inserted_count,
            skipped=skipped_count,
        )

        ti.xcom_push(key="inserted_count", value=inserted_count)
        ti.xcom_push(key="skipped_count", value=skipped_count)
        ti.xcom_push(key="inserted_ids", value=inserted_ids)

    except Exception:
        conn.rollback()
        log.exception("load_postgresql.failed", batch_id=batch_id)
        raise
    finally:
        conn.close()

