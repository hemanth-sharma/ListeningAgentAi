from typing import List, Dict
from pgvector.psycopg2 import register_vector

from agents.services.embedding_service import generate_embedding
from api.app.database import SessionLocal


def semantic_search(
    query: str,
    mission_id: str,
    limit: int = 10,
) -> List[Dict]:

    embedding = generate_embedding(query)

    db = SessionLocal()

    conn = db.connection().connection

    register_vector(conn)

    cursor = conn.cursor()

    sql = """
    SELECT
        d.id,
        d.title,
        d.content,
        d.url,
        1 - (e.vector <=> %s::vector) as similarity
    FROM embeddings e
    JOIN data_items d
        ON d.id = e.data_item_id
    WHERE d.mission_id = %s
    ORDER BY e.vector <=> %s::vector
    LIMIT %s
    """

    cursor.execute(
        sql,
        (embedding, mission_id, embedding, limit),
    )

    rows = cursor.fetchall()

    results = []

    for row in rows:
        results.append({
            "id": str(row[0]),
            "title": row[1],
            "content": row[2],
            "url": row[3],
            "similarity": float(row[4]),
        })

    cursor.close()
    db.close()

    return results