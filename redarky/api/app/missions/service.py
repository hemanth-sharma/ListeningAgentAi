from sqlalchemy.ext.asyncio import AsyncSession
from app.missions.models import Mission

async def create_mission(db: AsyncSession, data):
    mission = Mission(**data.dict())
    db.add(mission)
    await db.commit()
    await db.refresh(mission)
    return mission