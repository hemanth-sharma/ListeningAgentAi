from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.missions.schemas import MissionCreate
from app.missions.service import create_mission

router = APIRouter()

@router.post("/")
async def create(data: MissionCreate, db: AsyncSession = Depends(get_db)):
    return await create_mission(db, data)