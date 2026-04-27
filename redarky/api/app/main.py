from fastapi import FastAPI, Response
from app.missions.router import router as mission_router
from app.scraper.router import router as scraper_router
from app.auth.router import router as auth_router


app = FastAPI(title="RedArky AI")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return Response("Okay")


# Register routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(mission_router, prefix="/missions", tags=["missions"])
app.include_router(scraper_router, prefix="/scraper", tags=["scraper"])