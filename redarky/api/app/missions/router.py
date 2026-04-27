from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.missions.schemas import MissionCreate, MissionOut, MissionUpdate
from app.missions.service import create_mission, delete_mission, get_mission, list_missions, update_mission
from app.models import User

router = APIRouter()


@router.post("/", response_model=MissionOut, status_code=status.HTTP_201_CREATED)
async def create(
    data: MissionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await create_mission(db, str(user.id), data)


@router.get("/", response_model=list[MissionOut])
async def list_all(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await list_missions(db, str(user.id))


@router.get("/{mission_id}", response_model=MissionOut)
async def get_one(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    mission = await get_mission(db, str(user.id), mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return mission


@router.patch("/{mission_id}", response_model=MissionOut)
async def update_one(
    mission_id: str,
    payload: MissionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    mission = await get_mission(db, str(user.id), mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return await update_mission(db, mission, payload)


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_one(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deleted = await delete_mission(db, str(user.id), mission_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")