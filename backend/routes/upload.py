"""
Ruta de subida de archivos con validación completa
"""

import os
import uuid
import json
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./tmp/uploads"))
MAX_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "200"))
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

# Extensiones permitidas por tipo
ALLOWED_EXTENSIONS = {
    "image": {"jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"},
    "video": {"mp4", "avi", "mov", "mkv", "webm", "flv"},
    "audio": {"mp3", "wav", "ogg", "flac", "aac", "m4a"},
}

ALL_ALLOWED = {ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts}

MIME_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "webp": "image/webp", "bmp": "image/bmp", "gif": "image/gif",
    "tiff": "image/tiff", "mp4": "video/mp4", "avi": "video/x-msvideo",
    "mov": "video/quicktime", "mkv": "video/x-matroska",
    "webm": "video/webm", "flv": "video/x-flv", "mp3": "audio/mpeg",
    "wav": "audio/wav", "ogg": "audio/ogg", "flac": "audio/flac",
    "aac": "audio/aac", "m4a": "audio/mp4",
}


def get_media_type(ext: str) -> str:
    for media_type, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return media_type
    return "unknown"


def format_size(bytes_size: int) -> str:
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    return f"{bytes_size / 1024 / 1024:.2f} MB"


@router.post("/upload")
@limiter.limit("20/minute")
async def upload_file(request: Request, file: UploadFile = File(...)):
    try:
        # Obtener extensión
        filename = file.filename or "unknown"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ALL_ALLOWED:
            raise HTTPException(
                status_code=400,
                detail=f"Formato .{ext} no permitido. Usa: JPG, PNG, MP4, MP3, WAV..."
            )

        # Leer y verificar tamaño
        content = await file.read()
        size = len(content)

        if size > MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo demasiado grande. Máximo {MAX_SIZE_MB}MB."
            )

        if size == 0:
            raise HTTPException(status_code=400, detail="El archivo está vacío")

        # Generar ID único
        file_id = str(uuid.uuid4())
        save_filename = f"{file_id}.{ext}"
        save_path = UPLOAD_DIR / save_filename

        # Guardar archivo
        with open(save_path, "wb") as f:
            f.write(content)

        # Guardar metadata
        media_type = get_media_type(ext)
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        meta = {
            "id": file_id,
            "originalName": filename,
            "filename": save_filename,
            "ext": ext,
            "mediaType": media_type,
            "size": size,
            "mimeType": MIME_TYPES.get(ext, "application/octet-stream"),
            "uploadedAt": datetime.utcnow().isoformat(),
            "expiresAt": expires_at.isoformat(),
        }

        with open(UPLOAD_DIR / f"{file_id}.meta.json", "w") as f:
            json.dump(meta, f, indent=2)

        logger.info(f"Archivo subido: {filename} ({format_size(size)}) → {media_type}")

        return {
            "success": True,
            "fileId": file_id,
            "filename": filename,
            "ext": ext,
            "mediaType": media_type,
            "size": size,
            "sizeFormatted": format_size(size),
            "expiresAt": expires_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error al subir: {str(e)}")
