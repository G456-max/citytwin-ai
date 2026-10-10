from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from loguru import logger
import sys

from app.config import settings
from app.database import init_db
from app.rag import ensure_index
from app.routes import (
    health,
    scan,
    risk,
    graph,
    cascade,
    priority,
    plan,
    explain,
    cbom,
    train,
    evaluate,
    explain_ml,
)

# ============ LOGGER ============
logger.remove()
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    colorize=True
)

# ============ APP ============
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Post-Quantum Cybersecurity for Safety-Critical Mining Infrastructure",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============ CORS ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ EXCEPTION HANDLERS ============
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "MG_VALIDATION_ERROR", "message": "Invalid request", "detail": exc.errors()}}
    )


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "MG_INTERNAL_ERROR", "message": "Internal server error"}}
    )

# ============ ROUTES ============
app.include_router(health.router, prefix="/api")
app.include_router(scan.router, prefix="/api")
app.include_router(risk.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(cascade.router, prefix="/api")
app.include_router(priority.router, prefix="/api")
app.include_router(plan.router, prefix="/api")
app.include_router(explain.router, prefix="/api")
app.include_router(cbom.router, prefix="/api")
app.include_router(train.router, prefix="/api")
app.include_router(evaluate.router, prefix="/api")
app.include_router(explain_ml.router, prefix="/api")


# ============ ROOT ============
@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "tagline": "Predict the risk. Trace the impact. Plan the migration."
    }


# ============ LIFECYCLE ============
@app.on_event("startup")
async def startup_event():
    logger.info("═══════════════════════════════════════════")
    logger.info(f"  Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"  Debug mode: {settings.DEBUG}")
    init_db()
    logger.info("  Database initialized.")
    try:
        retriever = ensure_index(
            data_dir="data",
            vector_db_path=settings.VECTOR_DB_PATH,
            embedder_model=settings.EMBEDDER_MODEL
        )
        logger.info(f"  RAG index ready: {retriever.vectorstore.size()} chunks indexed.")
    except Exception as e:
        logger.warning(f"  RAG index initialization note: {e}")

    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        logger.info("  RAG in MOCK mode (no API key configured).")
    logger.info("═══════════════════════════════════════════")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.APP_NAME}")
