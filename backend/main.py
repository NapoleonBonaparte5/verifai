"""
VerifAI Backend — FastAPI
Verificador de Deepfakes y Autenticidad de Medios
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
import uvicorn

from dotenv import load_dotenv
load_dotenv()

# ── Importar rutas ──────────────────────────────────────────────
from routes.analyze import router as analyze_router
from routes.download import router as download_router
from utils.cleanup import cleanup_expired_files

# ── Configurar logger ───────────────────────────────────────────
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}",
    level="INFO"
)
logger.add("logs/verifai.log", rotation="10 MB", retention="7 days", level="WARNING")

# ── Crear directorios necesarios ────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/verifai/uploads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/tmp/verifai/outputs")
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# ── Rate limiter ────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── Lifespan ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 VerifAI Backend arrancando...")
    logger.info(f"📁 Uploads: {UPLOAD_DIR}")
    logger.info(f"📂 Outputs: {OUTPUT_DIR}")
    yield
    logger.info("🛑 VerifAI Backend cerrando...")

# ── App ─────────────────────────────────────────────────────────
app = FastAPI(
    title="VerifAI API",
    description="Verificador de Deepfakes y Autenticidad de Medios",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

# ── Middleware ──────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ─────────────────────────────────────────────────────
app.include_router(analyze_router, prefix="/api")
app.include_router(download_router, prefix="/api")

# ── Health check ────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "VerifAI",
        "version": "1.0.0",
        "hf_configured": bool(os.getenv("HUGGINGFACE_API_TOKEN")),
    }

# ── Error handlers ──────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor"}
    )

# ── Start ────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info",
    )
