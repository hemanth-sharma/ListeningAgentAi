import uuid
from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from app.posts.models import Post
from app.posts.schemas import PostCreate, PostUpdate

async def get_posts(
    db: AsyncSession, 
    project_id: Optional[uuid.UUID] = None,
    platform: Optional[str] = None,
    search: Optional[str] = None
) -> Sequence[Post]:
    stmt = select(Post)
    
    if project_id:
        stmt = stmt.where(Post.project_id == project_id)
    if platform:
        # Case-insensitive comparison matching your platform query string
        stmt = stmt.where(Post.platform.ilike(platform))
    if search:
        # Searches across title OR content
        stmt = stmt.where(
            or_(
                Post.title.ilike(f"%{search}%"),
                Post.content.ilike(f"%{search}%")
            )
        )
        
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_post(db: AsyncSession, post_id: uuid.UUID) -> Post | None:
    result = await db.execute(select(Post).where(Post.id == post_id))
    return result.scalar_one_or_none()

async def create_post(db: AsyncSession, post_in: PostCreate) -> Post:
    db_post = Post(**post_in.model_dump())
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    return db_post

async def update_post(db: AsyncSession, db_post: Post, post_in: PostUpdate) -> Post:
    for field, value in post_in.model_dump().items():
        setattr(db_post, field, value)
    await db.commit()
    await db.refresh(db_post)
    return db_post

async def delete_post(db: AsyncSession, db_post: Post) -> None:
    await db.delete(db_post)
    await db.commit()