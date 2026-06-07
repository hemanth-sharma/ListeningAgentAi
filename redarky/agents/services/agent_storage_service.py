import uuid
from datetime import datetime, UTC

from sqlalchemy import text

from api.app.database import SessionLocal


def save_agent_report(
    mission_id: str,
    report: str,
):

    db = SessionLocal()

    query = text("""
        INSERT INTO ai_reports (
            id,
            mission_id,
            report,
            created_at
        )
        VALUES (
            :id,
            :mission_id,
            :report,
            :created_at
        )
    """)

    db.execute(
        query,
        {
            "id": str(uuid.uuid4()),
            "mission_id": mission_id,
            "report": report,
            "created_at": datetime.now(UTC),
        },
    )

    db.commit()

    db.close()