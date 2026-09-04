from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import RazorAgentException
from app.db.database import init_db
from app.api.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} in {settings.ENVIRONMENT} mode...")
    await init_db()
    logger.info("Database initialized. RazorAgent V7 ready.")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title="RazorAgent V7 API",
    description="Autonomous LLM-driven multi-agent payment operations platform with LangGraph and Groq",
    version="7.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RazorAgentException)
async def razoragent_exception_handler(request: Request, exc: RazorAgentException):
    logger.error(f"Domain exception on {request.url.path}: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.message, "details": exc.details}
    )


# Include API routers
app.include_router(api_router, prefix="/api/v1")
# Root health route
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "service": "RazorAgent V7",
        "status": "OPERATIONAL",
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
