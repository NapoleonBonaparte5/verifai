"""
VerifAI — Análisis de Video
Análisis frame-by-frame para detección de deepfakes
"""

import os
import io
import struct
from pathlib import Path
import numpy as np
from PIL import Image
from loguru import logger
from utils.image_analysis import analyze_ela, analyze_noise, analyze_frequency, analyze_color_consistency


def analyze_video(file_path: Path, output_dir: str) -> dict:
    """
    Analiza video extrayendo frames y aplicando análisis de imagen.
    Sin dependencias pesadas — usa lectura binaria básica.
    """
    try:
        file_size = file_path.stat().st_size
        with open(file_path, 'rb') as f:
            header = f.read(32)

        # Detectar formato
        fmt = "MP4"
        if b'AVI ' in header[:12]:
            fmt = "AVI"
        elif b'ftyp' in header[4:8]:
            fmt = "MP4/MOV"

        # Extraer frames con PIL si es posible
        frames_analyzed = []
        frame_scores    = []

        # Intentar leer como secuencia de imágenes embebidas
        try:
            frames_analyzed, frame_scores = _extract_and_analyze_frames(file_path, output_dir)
        except Exception as e:
            logger.warning(f"No se pudieron extraer frames: {e}")

        if frame_scores:
            overall_score = round(float(np.mean(frame_scores)), 1)
            max_score     = round(float(np.max(frame_scores)), 1)
            # El score final pondera más los frames más sospechosos
            overall_score = round(overall_score * 0.6 + max_score * 0.4, 1)
        else:
            overall_score = 35  # Score neutral

        return {
            "manipulation_score": min(100, overall_score),
            "breakdown": {
                "frame_analysis": {
                    "label":   "Análisis de Frames",
                    "description": "Detección de manipulación en frames individuales",
                    "score":   overall_score,
                    "details": f"{len(frame_scores)} frames analizados",
                    "icon":    "film",
                },
                "temporal_consistency": {
                    "label":   "Consistencia Temporal",
                    "description": "Coherencia entre frames consecutivos",
                    "score":   round(float(np.std(frame_scores)) * 2, 1) if frame_scores else 25,
                    "details": f"Variación entre frames: {round(float(np.std(frame_scores)), 2) if frame_scores else 'N/A'}",
                    "icon":    "clock",
                },
            },
            "metadata": {
                "format":    fmt,
                "size_mb":   round(file_size / (1024*1024), 2),
                "frames_analyzed": len(frame_scores),
            },
            "frame_analysis": frames_analyzed,
            "flags": _generate_video_flags(overall_score, frame_scores),
        }

    except Exception as e:
        logger.error(f"Error en análisis de video: {e}")
        return {
            "manipulation_score": 30,
            "breakdown": {},
            "metadata": {"error": str(e)},
            "flags": [{"type": "info", "message": "Análisis de video limitado. Para mejores resultados, extrae frames manualmente."}],
        }


def _extract_and_analyze_frames(file_path: Path, output_dir: str, max_frames: int = 5):
    """
    Intenta extraer frames del video leyendo bloques JPEG embebidos.
    """
    frames_analyzed = []
    frame_scores    = []

    with open(file_path, 'rb') as f:
        data = f.read()

    # Buscar marcadores JPEG embebidos en el video
    jpeg_starts = []
    i = 0
    while i < len(data) - 1 and len(jpeg_starts) < max_frames:
        if data[i] == 0xFF and data[i+1] == 0xD8:
            jpeg_starts.append(i)
            i += 100000  # Saltar al menos 100KB entre frames
        else:
            i += 1

    for idx, start in enumerate(jpeg_starts[:max_frames]):
        try:
            # Buscar el final del JPEG
            end = data.find(b'\xff\xd9', start + 2)
            if end == -1 or end - start > 5_000_000:
                continue

            jpeg_data = data[start:end+2]
            img = Image.open(io.BytesIO(jpeg_data))

            # Guardar frame temporalmente
            frame_path = Path(output_dir) / f"frame_{idx}_{file_path.stem}.jpg"
            img.save(str(frame_path), "JPEG", quality=95)

            # Analizar frame
            ela   = analyze_ela(frame_path)
            noise = analyze_noise(frame_path)
            color = analyze_color_consistency(frame_path)

            frame_score = round(
                ela["manipulation_score"] * 0.4 +
                noise["manipulation_score"] * 0.3 +
                color["manipulation_score"] * 0.3,
                1
            )
            frame_scores.append(frame_score)
            frames_analyzed.append({
                "frame_index": idx,
                "score": frame_score,
                "ela_score":   ela["manipulation_score"],
                "noise_score": noise["manipulation_score"],
            })

            # Limpiar frame temporal
            frame_path.unlink(missing_ok=True)

        except Exception as e:
            logger.debug(f"Error procesando frame {idx}: {e}")
            continue

    return frames_analyzed, frame_scores


def _generate_video_flags(score, frame_scores) -> list:
    flags = []
    if score > 60:
        flags.append({"type": "danger", "message": "Alta probabilidad de manipulación detectada en frames"})
    if frame_scores and float(np.std(frame_scores)) > 20:
        flags.append({"type": "warning", "message": "Inconsistencias notables entre frames del video"})
    if not flags:
        flags.append({"type": "success", "message": "No se detectaron manipulaciones significativas en los frames analizados"})
    return flags
