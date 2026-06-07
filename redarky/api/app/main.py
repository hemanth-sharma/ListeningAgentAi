from fastapi import FastAPI, Response
from app.missions.router import router as mission_router
from app.scraper.router import router as scraper_router
from app.auth.router import router as auth_router
from app.rag.router import router as rag_router
from app.agents.router import router as agents_router


app = FastAPI(title="RedArky AI", version="2.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
def root():
    return Response("Okay")


# Register routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(mission_router, prefix="/missions", tags=["missions"])
app.include_router(scraper_router, prefix="/scraper", tags=["scraper"])
app.include_router(rag_router, prefix="/rag", tags=["rag"])
app.include_router(agents_router, prefix="/agents", tags=["agents"])