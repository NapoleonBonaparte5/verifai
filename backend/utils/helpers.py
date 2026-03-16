"""
VerifAI — Utilidades: File Handler, Cleanup, Report Generator
"""

# ────────────────────────────────────────────────────────────
# FILE HANDLER
# ────────────────────────────────────────────────────────────

import os
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger


async def save_upload(content: bytes, filename: str, prefix: str, upload_dir: str) -> Path:
    """Guarda un archivo subido de forma segura."""
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")[:64]
    ext       = Path(safe_name).suffix.lower()
    file_path = Path(upload_dir) / f"{prefix}{ext}"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, file_path.write_bytes, content)
    return file_path


def get_file_type(content_type: str) -> str:
    if content_type.startswith("image/"): return "image"
    if content_type.startswith("video/"): return "video"
    if content_type.startswith("audio/"): return "audio"
    return "unknown"


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:       return f"{size_bytes} B"
    if size_bytes < 1024**2:    return f"{size_bytes/1024:.1f} KB"
    return f"{size_bytes/1024**2:.2f} MB"


# ────────────────────────────────────────────────────────────
# CLEANUP
# ────────────────────────────────────────────────────────────

import threading
import time


def schedule_deletion(file_path: str, delay_minutes: int = 30):
    """Programa el borrado de un archivo después de N minutos."""
    def delete_later():
        time.sleep(delay_minutes * 60)
        try:
            Path(file_path).unlink(missing_ok=True)
            logger.debug(f"Archivo eliminado: {file_path}")
        except Exception as e:
            logger.warning(f"No se pudo eliminar {file_path}: {e}")

    t = threading.Thread(target=delete_later, daemon=True)
    t.start()


def cleanup_expired_files(upload_dir: str, output_dir: str, max_age_minutes: int = 60) -> int:
    """Limpia archivos más antiguos que max_age_minutes."""
    deleted = 0
    now     = time.time()
    cutoff  = now - (max_age_minutes * 60)

    for directory in [upload_dir, output_dir]:
        try:
            for f in Path(directory).iterdir():
                if f.is_file() and f.stat().st_mtime < cutoff:
                    f.unlink()
                    deleted += 1
        except Exception as e:
            logger.warning(f"Error en cleanup de {directory}: {e}")

    return deleted


# ────────────────────────────────────────────────────────────
# REPORT GENERATOR (PDF básico con reportlab)
# ────────────────────────────────────────────────────────────

async def generate_pdf_report(result: dict, analysis_id: str, output_dir: str) -> Path:
    """Genera un reporte PDF del análisis."""
    pdf_path = Path(output_dir) / f"{analysis_id}_report.pdf"

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _build_pdf, result, str(pdf_path))
    return pdf_path


def _build_pdf(result: dict, pdf_path: str):
    """Construye el PDF con reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER

        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)

        C_DARK  = colors.HexColor("#0D1117")
        C_BLUE  = colors.HexColor("#0D47A1")
        C_GREEN = colors.HexColor("#2E7D32")
        C_RED   = colors.HexColor("#C62828")
        C_YELL  = colors.HexColor("#F57F17")
        C_GRAY  = colors.HexColor("#555555")
        C_LGRAY = colors.HexColor("#F5F5F5")

        score   = result.get("overall_score", 0)
        verdict = result.get("verdict", "DESCONOCIDO")
        vcolor  = C_GREEN if score < 40 else (C_YELL if score < 60 else C_RED)

        S_TITLE  = ParagraphStyle("t",  fontName="Helvetica-Bold", fontSize=22, textColor=C_BLUE, alignment=TA_CENTER, spaceAfter=4)
        S_SUB    = ParagraphStyle("s",  fontName="Helvetica",      fontSize=10, textColor=C_GRAY, alignment=TA_CENTER, spaceAfter=12)
        S_H2     = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, textColor=C_DARK, spaceBefore=10, spaceAfter=4)
        S_BODY   = ParagraphStyle("b",  fontName="Helvetica",      fontSize=9,  textColor=C_GRAY, leading=14, spaceAfter=3)
        S_VERD   = ParagraphStyle("v",  fontName="Helvetica-Bold", fontSize=18, textColor=vcolor, alignment=TA_CENTER)

        story = []
        story.append(Paragraph("VerifAI", S_TITLE))
        story.append(Paragraph("Reporte de Análisis de Autenticidad de Medios", S_SUB))
        story.append(HRFlowable(width="100%", thickness=1, color=C_BLUE, spaceAfter=10))

        # Info general
        info_data = [
            ["Archivo",        result.get("filename", "—")],
            ["Tipo",           result.get("file_type", "—").upper()],
            ["Analizado",      result.get("analyzed_at", "—")[:19].replace("T", " ")],
            ["ID de análisis", analysis_id[:16] + "..."],
            ["Tiempo",         f"{result.get('analysis_time', 0)}s"],
        ]
        info_tbl = Table(info_data, colWidths=[40*mm, 120*mm])
        info_tbl.setStyle(TableStyle([
            ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE",  (0,0), (-1,-1), 9),
            ("FONTNAME",  (0,0), (0,-1),  "Helvetica-Bold"),
            ("TEXTCOLOR", (0,0), (0,-1),  C_DARK),
            ("TEXTCOLOR", (1,0), (1,-1),  C_GRAY),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_LGRAY, colors.white]),
            ("GRID",      (0,0), (-1,-1), 0.3, colors.HexColor("#DDDDDD")),
            ("TOPPADDING",(0,0), (-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("LEFTPADDING",(0,0),(-1,-1), 8),
        ]))
        story.append(info_tbl)
        story.append(Spacer(1, 12))

        # Veredicto
        story.append(Paragraph("VEREDICTO FINAL", S_H2))
        story.append(Paragraph(f"{verdict} — {score}%", S_VERD))
        story.append(Paragraph(result.get("confidence_label", ""), S_BODY))
        story.append(Spacer(1, 10))

        # Breakdown
        breakdown = result.get("breakdown", {})
        if breakdown:
            story.append(Paragraph("DESGLOSE DEL ANÁLISIS", S_H2))
            bd_data = [["Técnica", "Score", "Detalles"]]
            for key, val in breakdown.items():
                s = val.get("score")
                score_str = f"{s:.1f}%" if s is not None else "N/A"
                bd_data.append([
                    val.get("label", key),
                    score_str,
                    str(val.get("details", ""))[:80],
                ])
            bd_tbl = Table(bd_data, colWidths=[45*mm, 20*mm, 95*mm])
            bd_tbl.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0),  C_BLUE),
                ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 8),
                ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_LGRAY, colors.white]),
                ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("LEFTPADDING", (0,0), (-1,-1), 6),
            ]))
            story.append(bd_tbl)
            story.append(Spacer(1, 10))

        # Recomendaciones
        recs = result.get("recommendations", [])
        if recs:
            story.append(Paragraph("RECOMENDACIONES", S_H2))
            for rec in recs:
                story.append(Paragraph(f"• {rec}", S_BODY))

        # Disclaimer
        story.append(Spacer(1, 15))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_GRAY, spaceAfter=6))
        story.append(Paragraph(
            "DISCLAIMER: Este análisis es orientativo y no garantiza 100% de precisión. "
            "Úsalo como herramienta auxiliar y complementa con verificación humana experta. "
            "VerifAI no se responsabiliza de decisiones tomadas basadas en este reporte.",
            ParagraphStyle("disc", fontName="Helvetica", fontSize=7, textColor=C_GRAY, leading=10)
        ))

        doc.build(story)
        logger.info(f"PDF generado: {pdf_path}")

    except ImportError:
        # Si reportlab no está, crear PDF mínimo
        _create_minimal_pdf(result, pdf_path)


def _create_minimal_pdf(result: dict, pdf_path: str):
    """Crea un PDF mínimo sin reportlab."""
    content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 200>>stream
BT /F1 12 Tf 50 750 Td (VerifAI Report) Tj
0 -20 Td (File: {result.get('filename','?')}) Tj
0 -20 Td (Score: {result.get('overall_score',0)}%) Tj
0 -20 Td (Verdict: {result.get('verdict','?')}) Tj
ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
trailer<</Size 6/Root 1 0 R>>
startxref 0
%%EOF"""
    Path(pdf_path).write_text(content)
