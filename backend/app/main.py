from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import initalrouter, debug
from app.api.routes import debug_stream, evaluation
from app.core.exception import register_exception_handlers
from app.core.logger import logger

from app.schemas.response import APIResponse
from app.db.session import  get_db,Base,engine
from sqlalchemy import text
import os
from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # Application Startup
    
    logger.info("Application starting...")
    logger.info("Configuration loading.")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connected.")

    except Exception as e:
        logger.exception(f"Database connection failed:{e}")
        raise
    logger.info("Application startup complete.")
    
    yield

    logger.info("Application shutting down...")

    
    # Application Shutdown
     
    logger.info("Application shutting down...")


app = FastAPI(
    title="AI Debugger API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # permissive for local dev
    allow_credentials=False,      # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(initalrouter.router)
app.include_router(debug.router)
app.include_router(debug_stream.router)
app.include_router(evaluation.router)

# Serve frontend (static files)
frontend_dir = Path(__file__).parent.parent.parent / "frontend"
if (frontend_dir / "dist").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir / "dist"), html=True), name="frontend")
elif frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
