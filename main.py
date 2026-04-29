import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.base import Base
from app.core.database import engine
from app.routers.users import router as auth_router, users_router
from app.routers.campaigns import router as campaigns_router, sessions_router
from app.routers.contributions import router as contributions_router
from app.routers.groups import router as groups_router
from app.routers.leaderboard import router as leaderboard_router
from app.routers.ws import router as ws_router

logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="TotalFit — Fitness campaign and health data API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        redirect_slashes=True,
    )

    # CORS - Must be added BEFORE routes
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8081",
            "http://localhost:8082",
            "http://localhost:19006",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["*"],  # Expose all headers
    )

    # Catch-all exception handler — ensures unhandled errors still return a
    # proper JSON response that passes through CORSMiddleware (which sits
    # below ServerErrorMiddleware in the stack).
    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    prefix = settings.API_V1_STR
    
    # Include routers
    app.include_router(auth_router, prefix=prefix)
    app.include_router(users_router, prefix=prefix)
    app.include_router(campaigns_router, prefix=prefix)
    app.include_router(sessions_router, prefix=prefix)
    app.include_router(contributions_router, prefix=prefix)
    app.include_router(groups_router, prefix=prefix)
    app.include_router(leaderboard_router, prefix=prefix)
    app.include_router(ws_router, prefix=prefix)

    # Health check endpoints (defined after routers to avoid conflicts)
    @app.get("/health", tags=["Health"])
    async def health_check_root():
        return {"status": "ok", "service": settings.PROJECT_NAME}
    
    @app.get("/healthz", tags=["Health"])
    async def health_check_k8s():
        return {"status": "ok", "service": settings.PROJECT_NAME}
    
    @app.get(f"{prefix}/health", tags=["Health"])
    async def health_check_v1():
        return {"status": "ok", "service": settings.PROJECT_NAME}

    return app


app = create_app()
