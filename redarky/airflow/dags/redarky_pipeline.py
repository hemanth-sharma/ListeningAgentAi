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

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
import structlog
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# ──────────────────────────────────────────────────────────────
# Structlog configuration
# ──────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

log = structlog.get_logger("redarky_pipeline")

# ──────────────────────────────────────────────────────────────
# Runtime constants (from Airflow Variables)
# ──────────────────────────────────────────────────────────────
API_BASE_URL = Variable.get("API_BASE_URL", default_var="http://api:8000")
S3_BASE_PATH = Variable.get("S3_BASE_PATH", default_var="/opt/redarky_data_s3")
PG_CONN_STR = Variable.get(
    "PG_CONN_STR",
    default_var="postgresql+psycopg2://postgres:password@db:5432/redarky_db",
)
OPENAI_API_KEY = Variable.get("OPENAI_API_KEY", default_var="")

# Default mission_id used when DAG runs without config
DEFAULT_MISSION_ID = Variable.get("DEFAULT_MISSION_ID", default_var="00000000-0000-0000-0000-000000000001")
DEFAULT_QUERY = Variable.get("DEFAULT_QUERY", default_var="AI productivity tools")
DEFAULT_SUBREDDITS = Variable.get("DEFAULT_SUBREDDITS", default_var='["MachineLearning","artificial"]')

# ──────────────────────────────────────────────────────────────
# DAG default args
# ──────────────────────────────────────────────────────────────
default_args: dict[str, Any] = {
    "owner": "redarky",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    # Global retry policy (MYM-41) — applies to all tasks; can be overridden
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": False,
}

# ══════════════════════════════════════════════════════════════
# STAGE 1 — TASK 1: extract_sources  (MYM-28, 29)
# ══════════════════════════════════════════════════════════════

def extract_sources(**context: Any) -> None:
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
    mission_id = dag_run_conf.get("mission_id", DEFAULT_MISSION_ID)
    query = dag_run_conf.get("query", DEFAULT_QUERY)
    subreddits = dag_run_conf.get("subreddits", json.loads(DEFAULT_SUBREDDITS))

    batch_id = str(uuid.uuid4())
    log.info("extract_sources.start", batch_id=batch_id, mission_id=mission_id, query=query)

    url = f"{API_BASE_URL}/scraper/run/{mission_id}"
    payload = {"query": query, "subreddits": subreddits}

    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()

    file_path: str = result["file_path"]
    items_fetched: int = result["items_fetched"]

    log.info(
        "extract_sources.done",
        batch_id=batch_id,
        mission_id=mission_id,
        items_fetched=items_fetched,
        file_path=file_path,
    )

    # Push to XCom for downstream tasks
    task_instance = context["ti"]
    task_instance.xcom_push(key="batch_id", value=batch_id)
    task_instance.xcom_push(key="file_path", value=file_path)
    task_instance.xcom_push(key="mission_id", value=mission_id)
    task_instance.xcom_push(key="items_fetched", value=items_fetched)


# ══════════════════════════════════════════════════════════════
# STAGE 1 — TASK 2: validate_schema  (MYM-30)
# ══════════════════════════════════════════════════════════════

def validate_schema(**context: Any) -> None:
    """
    Read the raw JSON written by extract_sources and re-validate
    each item against a lightweight inline schema.
    Rejects and quarantines bad records to dead_letter/.
    
    XCom output: validated_file_path, valid_count, rejected_count
    """
    ti = context["ti"]
    file_path: str = ti.xcom_pull(task_ids="extract_sources", key="file_path")
    batch_id: str = ti.xcom_pull(task_ids="extract_sources", key="batch_id")
    mission_id: str = ti.xcom_pull(task_ids="extract_sources", key="mission_id")

    log.info("validate_schema.start", batch_id=batch_id, file_path=file_path)

    raw_data: list[dict] = json.loads(Path(file_path).read_text(encoding="utf-8"))

    valid_items: list[dict] = []
    rejected_items: list[dict] = []
    required_fields = {"source", "external_id", "title", "url", "scraped_at"}

    for item in raw_data:
        missing = required_fields - set(item.keys())
        if missing or not item.get("url") or not item.get("external_id"):
            rejected_items.append({"item": item, "reason": f"missing fields: {missing}"})
        else:
            valid_items.append(item)

    # Write validated JSON back (overwrite raw file with valid subset)
    validated_path = Path(file_path).with_suffix(".validated.json")
    validated_path.write_text(json.dumps(valid_items, ensure_ascii=True), encoding="utf-8")

    # Write rejected items to dead_letter/
    if rejected_items:
        dead_letter_dir = Path(S3_BASE_PATH) / "dead_letter" / mission_id
        dead_letter_dir.mkdir(parents=True, exist_ok=True)
        dl_path = dead_letter_dir / f"{batch_id}_rejected.json"
        dl_path.write_text(json.dumps(rejected_items, ensure_ascii=True), encoding="utf-8")

    log.info(
        "validate_schema.done",
        batch_id=batch_id,
        valid=len(valid_items),
        rejected=len(rejected_items),
    )

    ti.xcom_push(key="validated_file_path", value=str(validated_path))
    ti.xcom_push(key="valid_count", value=len(valid_items))
    ti.xcom_push(key="rejected_count", value=len(rejected_items))


# ══════════════════════════════════════════════════════════════
# STAGE 1 — TASK 3: clean_deduplicate  (MYM-31)
# ══════════════════════════════════════════════════════════════

def clean_deduplicate(**context: Any) -> None:
    """
    Read validated JSON, compute SHA-256 dedup_hash per item,
    drop in-batch duplicates (cross-batch dedup handled by DB UPSERT).
    Normalise text fields (strip whitespace, truncate content).

    XCom output: cleaned_file_path, unique_count
    """
    ti = context["ti"]
    validated_path: str = ti.xcom_pull(task_ids="validate_schema", key="validated_file_path")
    batch_id: str = ti.xcom_pull(task_ids="extract_sources", key="batch_id")
    mission_id: str = ti.xcom_pull(task_ids="extract_sources", key="mission_id")

    log.info("clean_deduplicate.start", batch_id=batch_id)

    items: list[dict] = json.loads(Path(validated_path).read_text(encoding="utf-8"))

    seen_hashes: set[str] = set()
    cleaned: list[dict] = []

    for item in items:
        # Normalise
        item["title"] = (item.get("title") or "").strip()[:500]
        item["content"] = (item.get("content") or "").strip()[:10_000]
        item["author"] = (item.get("author") or "").strip()[:255]

        # Compute dedup hash
        raw = f"{mission_id}:{item.get('source', '')}:{item.get('external_id', '')}"
        dedup_hash = hashlib.sha256(raw.encode()).hexdigest()
        item["dedup_hash"] = dedup_hash

        if dedup_hash not in seen_hashes:
            seen_hashes.add(dedup_hash)
            cleaned.append(item)

    cleaned_path = Path(validated_path).with_suffix(".cleaned.json")
    cleaned_path.write_text(json.dumps(cleaned, ensure_ascii=True), encoding="utf-8")

    log.info("clean_deduplicate.done", batch_id=batch_id, unique=len(cleaned))

    ti.xcom_push(key="cleaned_file_path", value=str(cleaned_path))
    ti.xcom_push(key="unique_count", value=len(cleaned))


# ══════════════════════════════════════════════════════════════
# STAGE 1 — TASK 4: load_postgresql  (MYM-32, 33)
# Bulk insert using executemany / INSERT … ON CONFLICT DO NOTHING
# ══════════════════════════════════════════════════════════════

def load_postgresql(**context: Any) -> None:
    """
    Bulk-insert cleaned items into data_items table using a single
    executemany statement with ON CONFLICT DO NOTHING (dedup by mission+hash).

    XCom output: inserted_count, skipped_count, inserted_ids
    """
    import psycopg2
    from psycopg2.extras import execute_values

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
    conn_str = PG_CONN_STR.replace("postgresql+psycopg2://", "postgresql://")
    conn = psycopg2.connect(conn_str)
    conn.autocommit = False

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


# ══════════════════════════════════════════════════════════════
# STAGE 2 — TASK 5: convert_to_parquet  (MYM-35, 36)
# ══════════════════════════════════════════════════════════════

def convert_to_parquet(**context: Any) -> None:
    """
    Read cleaned JSON, write to Parquet under processed/ layer.
    Layout: processed/{mission_id}/{date}/{batch_id}.parquet
    """
    import pandas as pd

    ti = context["ti"]
    cleaned_path: str = ti.xcom_pull(task_ids="clean_deduplicate", key="cleaned_file_path")
    batch_id: str = ti.xcom_pull(task_ids="extract_sources", key="batch_id")
    mission_id: str = ti.xcom_pull(task_ids="extract_sources", key="mission_id")

    log.info("convert_to_parquet.start", batch_id=batch_id)

    items: list[dict] = json.loads(Path(cleaned_path).read_text(encoding="utf-8"))
    if not items:
        log.warning("convert_to_parquet.empty", batch_id=batch_id)
        ti.xcom_push(key="parquet_path", value="")
        return

    df = pd.DataFrame(items)

    # Coerce scraped_at to datetime
    if "scraped_at" in df.columns:
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True, errors="coerce")

    date_partition = datetime.now(UTC).strftime("%Y-%m-%d")
    parquet_dir = Path(S3_BASE_PATH) / "processed" / mission_id / date_partition
    parquet_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = parquet_dir / f"{batch_id}.parquet"

    df.to_parquet(parquet_path, index=False, engine="pyarrow")

    log.info("convert_to_parquet.done", batch_id=batch_id, path=str(parquet_path), rows=len(df))

    ti.xcom_push(key="parquet_path", value=str(parquet_path))


# ══════════════════════════════════════════════════════════════
# STAGE 3 — TASK 6: generate_embeddings  (MYM-44, 45)
# ══════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════
# STAGE 2 — TASK 7: log_batch_metadata  (MYM-37 to 40)
# Writes a row to pipeline_batches for observability
# ══════════════════════════════════════════════════════════════

def log_batch_metadata(**context: Any) -> None:
    """
    Record pipeline run metadata in the pipeline_batches table.
    Captures timings, counts, and status for the full batch.
    """
    import psycopg2

    ti = context["ti"]
    batch_id: str = ti.xcom_pull(task_ids="extract_sources", key="batch_id")
    mission_id: str = ti.xcom_pull(task_ids="extract_sources", key="mission_id")
    items_scraped: int = ti.xcom_pull(task_ids="extract_sources", key="items_fetched") or 0
    valid_count: int = ti.xcom_pull(task_ids="validate_schema", key="valid_count") or 0
    rejected_count: int = ti.xcom_pull(task_ids="validate_schema", key="rejected_count") or 0
    unique_count: int = ti.xcom_pull(task_ids="clean_deduplicate", key="unique_count") or 0
    inserted_count: int = ti.xcom_pull(task_ids="load_postgresql", key="inserted_count") or 0
    skipped_count: int = ti.xcom_pull(task_ids="load_postgresql", key="skipped_count") or 0
    parquet_path: str = ti.xcom_pull(task_ids="convert_to_parquet", key="parquet_path") or ""

    dag_run = context["dag_run"]
    started_at = dag_run.start_date
    ended_at = datetime.now(UTC)
    duration_seconds = (ended_at - started_at).total_seconds() if started_at else None

    log.info(
        "log_batch_metadata",
        batch_id=batch_id,
        mission_id=mission_id,
        items_scraped=items_scraped,
        inserted=inserted_count,
        skipped=skipped_count,
        duration_s=duration_seconds,
    )

    conn_str = PG_CONN_STR.replace("postgresql+psycopg2://", "postgresql://")
    conn = psycopg2.connect(conn_str)

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pipeline_batches
                  (batch_id, mission_id, items_scraped, valid_count, rejected_count,
                   unique_count, success_count, skipped_count, parquet_path,
                   started_at, ended_at, duration_seconds, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (batch_id) DO NOTHING
                """,
                (
                    batch_id,
                    mission_id,
                    items_scraped,
                    valid_count,
                    rejected_count,
                    unique_count,
                    inserted_count,
                    skipped_count,
                    parquet_path,
                    started_at,
                    ended_at,
                    duration_seconds,
                    "completed",
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        log.exception("log_batch_metadata.failed", batch_id=batch_id)
        raise
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
# DAG DEFINITION
# ══════════════════════════════════════════════════════════════

with DAG(
    dag_id="redarky_pipeline",
    description="End-to-end RedArky data pipeline: scrape → validate → clean → load → embed",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["redarky", "pipeline", "phase2"],
    doc_md="""
## RedArky Pipeline DAG

**Stages covered:**
- Stage 1 (MYM-28→33): extract → validate → deduplicate → bulk insert
- Stage 2 (MYM-35→41): parquet conversion + batch metadata logging
- Stage 3 (MYM-44→45): OpenAI embedding generation

**Trigger:** Can be triggered manually with config:
```json
{
  "mission_id": "<uuid>",
  "query": "AI SaaS tools",
  "subreddits": ["MachineLearning", "SaaS"]
}
```
    """,
) as dag:

    t_extract = PythonOperator(
        task_id="extract_sources",
        python_callable=extract_sources,
        # Scraper tasks get the full retry policy (MYM-41)
        retries=3,
        retry_delay=timedelta(minutes=5),
    )

    t_validate = PythonOperator(
        task_id="validate_schema",
        python_callable=validate_schema,
        retries=2,
        retry_delay=timedelta(minutes=2),
    )

    t_clean = PythonOperator(
        task_id="clean_deduplicate",
        python_callable=clean_deduplicate,
        retries=2,
        retry_delay=timedelta(minutes=2),
    )

    t_load = PythonOperator(
        task_id="load_postgresql",
        python_callable=load_postgresql,
        retries=3,
        retry_delay=timedelta(minutes=5),
    )

    t_parquet = PythonOperator(
        task_id="convert_to_parquet",
        python_callable=convert_to_parquet,
        retries=2,
        retry_delay=timedelta(minutes=2),
    )

    t_embed = PythonOperator(
        task_id="generate_embeddings",
        python_callable=generate_embeddings,
        retries=3,
        retry_delay=timedelta(minutes=5),
    )

    t_log = PythonOperator(
        task_id="log_batch_metadata",
        python_callable=log_batch_metadata,
        # Metadata logging must not block; set trigger_rule to allow partial failures
        trigger_rule="all_done",
        retries=1,
        retry_delay=timedelta(minutes=1),
    )

    # ── Task dependency chain ─────────────────────────────────
    t_extract >> t_validate >> t_clean >> t_load >> t_parquet >> t_embed >> t_log
