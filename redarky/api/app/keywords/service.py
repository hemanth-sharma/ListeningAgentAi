import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.keywords.models import Keyword
from app.keywords.schemas import KeywordCreate, KeywordUpdate

async def get_keywords(db: AsyncSession, project_id: uuid.UUID | None = None) -> Sequence[Keyword]:
    stmt = select(Keyword)
    if project_id:
        stmt = stmt.where(Keyword.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_keyword(db: AsyncSession, keyword_id: uuid.UUID) -> Keyword | None:
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    return result.scalar_one_or_none()

async def create_keyword(db: AsyncSession, keyword_in: KeywordCreate) -> Keyword:
    db_keyword = Keyword(**keyword_in.model_dump())
    db.add(db_keyword)
    await db.commit()
    await db.refresh(db_keyword)
    return db_keyword

async def update_keyword(db: AsyncSession, db_keyword: Keyword, keyword_in: KeywordUpdate) -> Keyword:
    for field, value in keyword_in.model_dump().items():
        setattr(db_keyword, field, value)
    await db.commit()
    await db.refresh(db_keyword)
    return db_keyword

async def delete_keyword(db: AsyncSession, db_keyword: Keyword) -> None:
    await db.delete(db_keyword)
    await db.commit()