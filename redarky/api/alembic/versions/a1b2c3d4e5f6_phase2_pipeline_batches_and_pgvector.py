"""phase2_pipeline_batches_and_pgvector

Revision ID: a1b2c3d4e5f6
Revises: e82a3bc86ac2
Create Date: 2026-05-11 04:00:00.000000

Phase 2 changes:
  1. Enable pgvector extension (CREATE EXTENSION IF NOT EXISTS vector)
  2. Add pipeline_batches table (MYM-37 to 40)
  3. Alter embeddings.vector from JSON → vector(1536) using pgvector
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e82a3bc86ac2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Phase 2 schema upgrades."""

    # ── 1. pgvector extension (MYM-42) ───────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # ── 2. pipeline_batches table (MYM-37 to 40) ─────────────
    op.create_table(
        "pipeline_batches",
        sa.Column("batch_id", sa.String(36), primary_key=True),
        sa.Column("mission_id", sa.String(36), nullable=False, index=True),
        sa.Column("items_scraped", sa.Integer(), nullable=False, default=0),
        sa.Column("valid_count", sa.Integer(), nullable=False, default=0),
        sa.Column("rejected_count", sa.Integer(), nullable=False, default=0),
        sa.Column("unique_count", sa.Integer(), nullable=False, default=0),
        sa.Column("success_count", sa.Integer(), nullable=False, default=0),
        sa.Column("skipped_count", sa.Integer(), nullable=False, default=0),
        sa.Column("parquet_path", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_pipeline_batches_mission_id", "pipeline_batches", ["mission_id"])
    op.create_index("ix_pipeline_batches_status", "pipeline_batches", ["status"])

    # ── 3. Upgrade embeddings.vector JSON → pgvector(1536) (MYM-43) ──
    # Step 1: rename old column
    op.alter_column("embeddings", "vector", new_column_name="vector_json_backup")

    # Step 2: add new pgvector column
    op.execute("ALTER TABLE embeddings ADD COLUMN vector vector(1536);")

    # Step 3: migrate existing JSON data → vector (best-effort cast)
    op.execute("""
        UPDATE embeddings
        SET vector = vector_json_backup::text::vector
        WHERE vector_json_backup IS NOT NULL;
    """)

    # Step 4: drop the backup column
    op.drop_column("embeddings", "vector_json_backup")

    # Step 5: add IVFFlat index for cosine similarity search (MYM-43)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_embeddings_vector_cosine
        ON embeddings
        USING ivfflat (vector vector_cosine_ops)
        WITH (lists = 100);
    """)


def downgrade() -> None:
    """Revert Phase 2 changes."""

    # Revert vector column
    op.execute("DROP INDEX IF EXISTS ix_embeddings_vector_cosine;")
    op.execute("ALTER TABLE embeddings ADD COLUMN vector_json_backup JSON;")
    op.execute("""
        UPDATE embeddings
        SET vector_json_backup = vector::text::json
        WHERE vector IS NOT NULL;
    """)
    op.execute("ALTER TABLE embeddings DROP COLUMN vector;")
    op.alter_column("embeddings", "vector_json_backup", new_column_name="vector")

    # Drop pipeline_batches
    op.drop_index("ix_pipeline_batches_status", "pipeline_batches")
    op.drop_index("ix_pipeline_batches_mission_id", "pipeline_batches")
    op.drop_table("pipeline_batches")

    # Note: We leave the pgvector extension in place on downgrade
    # to avoid breaking other potential usages.
