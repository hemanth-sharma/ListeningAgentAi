from fastapi import FastAPI, Response, Depends
from app.missions.router import router as mission_router
import httpx
from contextlib import asynccontextmanager
from app.database import get_db, engine, Base
from sqlalchemy.ext.asyncio import AsyncSession
from app.scraper.models import ScrapedResult
from app.config import settings
from app.scraper.router import router as scraper_router


## Initialize Database 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On Start: Create tables 
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield 
    
    # On Shutdown: Clean up connections
    await engine.dispose()


app = FastAPI(title="RedArky AI", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return Response("Okay")


@app.get("/scrape")
async def call_scraper(db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        # Go Scraper
        res = await client.post(settings.SCRAPER_URL, json={"query": "ai"})
        data = res.json()

        # Save in database for now
        new_items = [
            ScrapedResult(
                title=item['title'],
                url=item['url'],
                query='ai'
            ) for item in data
        ]
        db.add_all(new_items)
        await db.commit()
        
        return {"message": f"Saved {len(new_items)} items to redarky.sqlite", "data": data}


# Register routes
app.include_router(mission_router, prefix="/missions", tags=["missions"])
app.include_router(scraper_router, prefix="/scraper", tags=["scraper"])