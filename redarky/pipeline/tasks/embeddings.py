import time
import uuid
from datetime import UTC, datetime
from typing import Any

import openai
from psycopg2.extras import execute_values

from pipeline.monitoring.batch_tracker import track_pipeline_event
from pipeline.utils.config import OPENAI_API_KEY
from pipeline.utils.database import get_postgres_connection
from pipeline.utils.logger import log

EMBEDDING_MODEL = "text-embedding-3-small"
MAX_EMBED_TEXT_LENGTH = 8000
EMBED_BATCH_SIZE = 100


def generate_embeddings(**context: Any) -> None:
    """
    Generate embeddings and store in pgvector.
    """

    start_time = time.time()

    ti = context["ti"]

    batch_id: str = ti.xcom_pull(
        task_ids="extract_sources",
        key="batch_id",
    )

    inserted_ids: list[str] = ti.xcom_pull(
        task_ids="load_postgresql",
        key="inserted_ids",
    ) or []

    if not inserted_ids:
        log.info(
            "generate_embeddings.skip_empty",
            batch_id=batch_id,
        )
        return

    if not OPENAI_API_KEY:
        log.warning(
            "generate_embeddings.no_api_key",
            batch_id=batch_id,
        )
        return

    log.info(
        "generate_embeddings.start",
        batch_id=batch_id,
        total_records=len(inserted_ids),
    )

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    conn = get_postgres_connection()

    try:
        with conn.cursor() as cur:

            placeholders = ",".join(["%s"] * len(inserted_ids))

            cur.execute(
                f"""
                SELECT id, title, content
                FROM data_items
                WHERE id IN ({placeholders})
                """,
                inserted_ids,
            )

            rows = cur.fetchall()

        valid_items = []
        texts = []

        for item_id, title, content in rows:

            text = " ".join(
                filter(None, [title, content])
            ).strip()

            text = text[:MAX_EMBED_TEXT_LENGTH]

            if text:
                valid_items.append(item_id)
                texts.append(text)

        if not texts:
            log.warning(
                "generate_embeddings.no_text",
                batch_id=batch_id,
            )
            return

        embedding_rows = []

        for i in range(0, len(texts), EMBED_BATCH_SIZE):

            batch_texts = texts[i:i + EMBED_BATCH_SIZE]
            batch_items = valid_items[i:i + EMBED_BATCH_SIZE]

            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch_texts,
            )

            for idx, item_id in enumerate(batch_items):

                vector = response.data[idx].embedding

                pgvector = f"[{','.join(map(str, vector))}]"

                embedding_rows.append(
                    (
                        str(uuid.uuid4()),
                        str(item_id),
                        EMBEDDING_MODEL,
                        pgvector,
                        datetime.now(UTC),
                    )
                )

        with conn.cursor() as cur:

            execute_values(
                cur,
                """
                INSERT INTO embeddings
                (
                    id,
                    data_item_id,
                    model_name,
                    vector,
                    created_at
                )
                VALUES %s
                ON CONFLICT (data_item_id)
                DO NOTHING
                """,
                embedding_rows,
                page_size=100,
            )

        conn.commit()

        duration = round(time.time() - start_time, 2)

        log.info(
            "generate_embeddings.done",
            batch_id=batch_id,
            embedded=len(embedding_rows),
            duration_seconds=duration,
        )

        track_pipeline_event(
            batch_id=batch_id,
            stage="generate_embeddings",
            status="success",
            metadata={
                "embedded": len(embedding_rows),
                "duration_seconds": duration,
            },
        )

    except Exception as e:

        conn.rollback()

        log.exception(
            "generate_embeddings.failed",
            batch_id=batch_id,
            error=str(e),
        )

        track_pipeline_event(
            batch_id=batch_id,
            stage="generate_embeddings",
            status="failed",
            metadata={"error": str(e)},
        )

        raise

    finally:
        conn.close()