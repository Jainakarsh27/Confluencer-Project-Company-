import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.base import Base
from app.db.session import engine, get_db
from app.exceptions import register_exception_handlers
from app.api.accounts import router as accounts_router
from app.api.transactions import router as transactions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup structured logging
    setup_logging()
    logger.info("Initializing %s application...", settings.APP_NAME)
    
    # Auto-create tables for development/sqlite convenience if not existing
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified.")
    except Exception as e:
        logger.warning("Could not auto-create tables on startup (using migrations): %s", e)
        
    yield
    logger.info("Shutting down %s application...", settings.APP_NAME)


app = FastAPI(
    title=f"{settings.APP_NAME} — Transaction Ledger API",
    version="1.0.0",
    description=(
        "Production-grade Transaction Ledger API implementing atomic double-entry-style balance management, "
        "concurrency protection, duplicate transaction prevention, and audit reconciliation."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
register_exception_handlers(app)

# Include API Routers
app.include_router(accounts_router, prefix=settings.API_V1_STR)
app.include_router(transactions_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"], summary="System health check")
def health_check(db: Session = Depends(get_db)):
    """Health check verifying API responsiveness and database connectivity."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Health check DB probe failed: %s", e)
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app": settings.APP_NAME,
        "environment": settings.ENV,
        "database": db_status,
    }


# Static frontend mounting (if built or static assets exist)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Welcome to LedgerFlow API. Explore documentation at /docs"}
else:
    @app.get("/", include_in_schema=False)
    def redirect_to_docs():
        return {"message": "LedgerFlow API is active. Visit /docs for Swagger UI documentation."}
