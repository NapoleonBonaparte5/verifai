"""
Ruta /api/download — Descarga de reportes PDF
"""

import os
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger

from utils.report_generator import generate_pdf_report

router = APIRouter()
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/tmp/verifai/outputs")


@router.get("/download/report/{analysis_id}")
async def download_report(analysis_id: str):
    """Genera y descarga un reporte PDF del análisis."""

    if not analysis_id.replace("-", "").isalnum():
        raise HTTPException(400, "ID inválido")

    result_path = Path(OUTPUT_DIR) / f"{analysis_id}.json"

    if not result_path.exists():
        raise HTTPException(404, "Análisis no encontrado o expirado")

    try:
        result = json.loads(result_path.read_text())
        pdf_path = await generate_pdf_report(result, analysis_id, OUTPUT_DIR)

        return FileResponse(
            path=str(pdf_path),
            filename=f"verifai-report-{analysis_id[:8]}.pdf",
            media_type="application/pdf",
        )
    except Exception as e:
        logger.error(f"Error generando PDF {analysis_id}: {e}")
        raise HTTPException(500, "Error al generar el reporte")
