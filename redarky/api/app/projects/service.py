import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.projects.models import Project
from app.projects.schemas import ProjectCreate, ProjectUpdate


async def get_projects(db: AsyncSession, owner_id: uuid.UUID) -> Sequence[Project]:
    result = await db.execute(select(Project).where(Project.owner_id == owner_id))
    return result.scalars().all()

async def get_project(db: AsyncSession, project_id: uuid.UUID, owner_id: uuid.UUID) -> Project | None:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
    )
    return result.scalar_one_or_none()

async def create_project(db: AsyncSession, project_in: ProjectCreate, owner_id: uuid.UUID) -> Project:
    # Injecting the owner_id extracted from your Auth token validation step
    db_project = Project(**project_in.model_dump(), owner_id=owner_id)
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project

async def update_project(db: AsyncSession, db_project: Project, project_in: ProjectUpdate) -> Project:
    for field, value in project_in.model_dump().items():
        setattr(db_project, field, value)
    await db.commit()
    await db.refresh(db_project)
    return db_project

async def delete_project(db: AsyncSession, db_project: Project) -> None:
    await db.delete(db_project)
    await db.commit()