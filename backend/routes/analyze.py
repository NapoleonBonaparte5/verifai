"""
Ruta /api/analyze — Análisis principal de deepfakes
"""

import os
import uuid
import json
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from loguru import logger

from utils.file_handler import save_upload, get_file_type, format_size
from utils.analyzer import analyze_media
from utils.cleanup import schedule_deletion

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/verifai/uploads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/tmp/verifai/outputs")
MAX_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "200"))

ALLOWED_TYPES = {
    "image": ["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"],
    "video": ["video/mp4", "video/avi", "video/quicktime", "video/x-msvideo",
              "video/webm", "video/x-matroska"],
    "audio": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/flac",
              "audio/mp4", "audio/x-wav"],
}

ALL_ALLOWED = [mt for types in ALLOWED_TYPES.values() for mt in types]

@router.post("/analyze")
@limiter.limit("20/minute")
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    compare_file: Optional[UploadFile] = File(None),
):
    """
    Analiza un archivo multimedia y devuelve el reporte de autenticidad.
    """
    # ── Validación básica ───────────────────────────────────────
    if not file.filename:
        raise HTTPException(400, "No se recibió ningún archivo")

    content_type = file.content_type or ""
    if content_type not in ALL_ALLOWED:
        raise HTTPException(400, f"Tipo de archivo no soportado: {content_type}")

    # ── Leer y validar tamaño ───────────────────────────────────
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > MAX_SIZE_MB:
        raise HTTPException(413, f"Archivo demasiado grande. Máximo {MAX_SIZE_MB}MB")

    # ── Guardar archivo ─────────────────────────────────────────
    analysis_id = str(uuid.uuid4())
    file_path = await save_upload(content, file.filename, analysis_id, UPLOAD_DIR)

    logger.info(f"Análisis iniciado: {file.filename} ({format_size(len(content))})")

    # ── Archivo de comparación opcional ─────────────────────────
    compare_path = None
    if compare_file and compare_file.filename:
        compare_content = await compare_file.read()
        compare_path = await save_upload(
            compare_content, compare_file.filename,
            f"{analysis_id}_compare", UPLOAD_DIR
        )

    # ── Ejecutar análisis ────────────────────────────────────────
    try:
        file_type = get_file_type(content_type)
        result = await analyze_media(
            file_path=file_path,
            file_type=file_type,
            original_name=file.filename,
            analysis_id=analysis_id,
            compare_path=compare_path,
            output_dir=OUTPUT_DIR,
        )

        # Guardar resultado JSON
        result_path = Path(OUTPUT_DIR) / f"{analysis_id}.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

        # Programar borrado en 30 minutos
        schedule_deletion(str(file_path), delay_minutes=30)
        if compare_path:
            schedule_deletion(str(compare_path), delay_minutes=30)
        schedule_deletion(str(result_path), delay_minutes=60)

        logger.info(f"Análisis completado: {analysis_id} — Score: {result['overall_score']}%")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error en análisis {analysis_id}: {e}")
        # Limpiar archivos en caso de error
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(500, f"Error al analizar el archivo: {str(e)}")


@router.get("/results/{analysis_id}")
async def get_result(analysis_id: str):
    """Recupera un resultado de análisis guardado."""
    if not analysis_id.replace("-", "").isalnum():
        raise HTTPException(400, "ID de análisis inválido")

    result_path = Path(OUTPUT_DIR) / f"{analysis_id}.json"

    if not result_path.exists():
        raise HTTPException(404, "Resultado no encontrado o expirado")

    return JSONResponse(content=json.loads(result_path.read_text()))
