import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.models import Mission
from app.missions.schemas import MissionCreate, MissionUpdate


async def create_mission(db: AsyncSession, owner_id: str, data: MissionCreate) -> Mission:
    mission = Mission(owner_id=uuid.UUID(owner_id), **data.model_dump())
    db.add(mission)
    await db.commit()
    await db.refresh(mission)
    return mission


async def list_missions(db: AsyncSession, owner_id: str) -> list[Mission]:
    result = await db.execute(
        select(Mission).where(Mission.owner_id == uuid.UUID(owner_id)).order_by(Mission.created_at.desc())
    )
    return list(result.scalars().all())


async def get_mission(db: AsyncSession, owner_id: str, mission_id: str) -> Mission | None:
    result = await db.execute(
        select(Mission).where(Mission.id == uuid.UUID(mission_id), Mission.owner_id == uuid.UUID(owner_id))
    )
    return result.scalar_one_or_none()


async def update_mission(db: AsyncSession, mission: Mission, payload: MissionUpdate) -> Mission:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(mission, field, value)
    await db.commit()
    await db.refresh(mission)
    return mission


async def delete_mission(db: AsyncSession, owner_id: str, mission_id: str) -> bool:
    result = await db.execute(
        delete(Mission).where(Mission.id == uuid.UUID(mission_id), Mission.owner_id == uuid.UUID(owner_id))
    )
    await db.commit()
    return bool(result.rowcount)