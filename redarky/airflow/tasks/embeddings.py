
import json
from airflow.pipeline_utils.logger import log
from airflow.pipeline_utils.config import (OPENAI_API_KEY, PG_CONN_STR)
from typing import Any
import uuid
from datetime import UTC, datetime, timedelta


# Pending 
def generate_embeddings(**context: Any) -> None:
    """
    For each newly inserted data_item, fetch its title/content/summary,
    call OpenAI embeddings API (text-embedding-3-small, 1536-dim),
    and bulk-insert into the embeddings table via pgvector.

    Skips if OPENAI_API_KEY is not set (allows testing without the key).
    """
    import openai
    import psycopg2
    from psycopg2.extras import execute_values

    ti = context["ti"]
    batch_id: str = ti.xcom_pull(task_ids="extract_sources", key="batch_id")
    inserted_ids: list[str] = ti.xcom_pull(task_ids="load_postgresql", key="inserted_ids") or []

    if not inserted_ids:
        log.info("generate_embeddings.skip_empty", batch_id=batch_id)
        return

    if not OPENAI_API_KEY:
        log.warning("generate_embeddings.no_api_key", batch_id=batch_id)
        return

    log.info("generate_embeddings.start", batch_id=batch_id, count=len(inserted_ids))

    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    conn_str = PG_CONN_STR.replace("postgresql+psycopg2://", "postgresql://")
    conn = psycopg2.connect(conn_str)

    try:
        # Fetch items to embed
        with conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(inserted_ids))
            cur.execute(
                f"SELECT id, title, content FROM data_items WHERE id IN ({placeholders})",
                inserted_ids,
            )
            rows = cur.fetchall()

        embedding_rows = []
        for (item_id, title, content) in rows:
            # Embed only semantic text — not raw metadata
            text_to_embed = " ".join(filter(None, [title, content]))[:8000]
            if not text_to_embed.strip():
                continue

            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text_to_embed,
            )
            vector = response.data[0].embedding  # list[float], len=1536

            embedding_rows.append((
                str(uuid.uuid4()),          # id
                str(item_id),              # data_item_id
                "text-embedding-3-small",  # model_name
                json.dumps(vector),        # vector (stored as JSON for now)
                datetime.now(UTC).isoformat(),  # created_at
            ))

        if embedding_rows:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO embeddings (id, data_item_id, model_name, vector, created_at)
                    VALUES %s
                    ON CONFLICT (data_item_id) DO NOTHING
                    """,
                    embedding_rows,
                )
            conn.commit()

        log.info("generate_embeddings.done", batch_id=batch_id, embedded=len(embedding_rows))

    except Exception:
        conn.rollback()
        log.exception("generate_embeddings.failed", batch_id=batch_id)
        raise
    finally:
        conn.close()

