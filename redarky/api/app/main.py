from fastapi import FastAPI, Request, Response, status
from app.scraper.router import router as scraper_router
from app.auth.router import router as auth_router
from app.projects.router import router as project_router
from app.keywords.router import router as keyword_router
from app.posts.router import router as post_router
from app.leads.router import router as lead_router


from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.utils.exceptions import NotFoundException, UnauthorizedException, DomainException

## Marketing listening parts # For now not using
# from app.missions.router import router as mission_router
# from app.rag.router import router as rag_router
# from app.agents.router import router as agents_router



app = FastAPI(
    title="Redarky API",
    description="Social Listening Lead Generation Platform Backend — Phase 1 Core CRUD",
    version="1.0.0"
)

# Standardized Error Response Helper
def create_error_response(status_code: int, error_type: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "type": error_type,
                "message": message
            }
        }
    )

# 1. Catch all Custom 'Not Found' Resources
@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException):
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_type="RESOURCE_NOT_FOUND",
        message=exc.message
    )

# 2. Catch Request/Pydantic Input Type Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Grab the first validation failure reason cleanly
    errors = exc.errors()
    msg = f"Validation failed: {errors[0]['loc'][-1]} - {errors[0]['msg']}" if errors else "Invalid request payload."
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="VALIDATION_ERROR",
        message=msg
    )

# 3. Catch-all fallback for completely unhandled system crashes (500)
@app.exception_handler(Exception)
async def universal_fallback_handler(request: Request, exc: Exception):
    # Log the actual stack trace here using system logger (e.g., logging.error(exc))
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please try again later."
    )



@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
def root():
    return Response("Okay")


# Register routes
app.include_router(auth_router)
app.include_router(scraper_router)
app.include_router(project_router)
app.include_router(keyword_router)
app.include_router(post_router)
app.include_router(lead_router)

# app.include_router(mission_router, prefix="/missions", tags=["missions"])
# app.include_router(rag_router, prefix="/rag", tags=["rag"])
# app.include_router(agents_router, prefix="/agents", tags=["agents"])

