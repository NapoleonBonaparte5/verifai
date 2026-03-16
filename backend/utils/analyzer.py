"""
VerifAI — Motor de análisis principal
Combina múltiples técnicas de detección para máxima precisión
"""

import os
import asyncio
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

import httpx
import numpy as np
from PIL import Image, ImageFilter, ImageChops
from loguru import logger

from utils.image_analysis import (
    analyze_ela,
    analyze_noise,
    analyze_frequency,
    analyze_metadata,
    analyze_color_consistency,
    detect_ai_signatures,
    compare_images,
    generate_heatmap_data,
)
from utils.audio_analysis import analyze_audio
from utils.video_analysis import analyze_video

HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "")
HF_API_URL = "https://api-inference.huggingface.co/models"

# Modelos de Hugging Face para detección de deepfakes
HF_MODELS = {
    "image_deepfake": "Wvolf/ViT-Deepfake-Detection",
    "image_ai_gen":   "umm-maybe/AI-image-detector",
}


async def call_huggingface_api(model_id: str, file_path: Path) -> dict:
    """Llama a la API de Hugging Face Inference."""
    if not HF_TOKEN:
        logger.warning("HF token no configurado, usando solo análisis local")
        return {}

    url = f"{HF_API_URL}/{model_id}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(file_path, "rb") as f:
                data = f.read()
            response = await client.post(url, headers=headers, content=data)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                logger.warning(f"Modelo {model_id} cargando, usando fallback local")
                return {}
            else:
                logger.warning(f"HF API error {response.status_code} para {model_id}")
                return {}
    except Exception as e:
        logger.warning(f"Error llamando HF API: {e}")
        return {}


def parse_hf_deepfake_result(hf_result: list) -> float:
    """
    Parsea resultado de HF y devuelve probabilidad de deepfake (0-100).
    """
    if not hf_result or not isinstance(hf_result, list):
        return -1.0  # -1 indica que no hay resultado de HF

    try:
        for item in hf_result:
            label = item.get("label", "").lower()
            score = float(item.get("score", 0))
            if "fake" in label or "deepfake" in label or "manipulated" in label:
                return round(score * 100, 1)
            if "real" in label or "authentic" in label or "genuine" in label:
                return round((1 - score) * 100, 1)
        return -1.0
    except Exception:
        return -1.0


async def analyze_media(
    file_path: Path,
    file_type: str,
    original_name: str,
    analysis_id: str,
    compare_path: Optional[Path],
    output_dir: str,
) -> dict:
    """
    Motor principal de análisis multimodal.
    Combina análisis local + Hugging Face API.
    """
    start_time = time.time()

    if file_type == "image":
        result = await analyze_image(file_path, original_name, compare_path)
    elif file_type == "audio":
        result = await analyze_audio_file(file_path, original_name)
    elif file_type == "video":
        result = await analyze_video_file(file_path, original_name, output_dir)
    else:
        raise ValueError(f"Tipo de archivo no soportado: {file_type}")

    elapsed = round(time.time() - start_time, 2)

    return {
        "analysis_id":    analysis_id,
        "filename":       original_name,
        "file_type":      file_type,
        "analyzed_at":    datetime.utcnow().isoformat(),
        "analysis_time":  elapsed,
        **result,
    }


async def analyze_image(
    file_path: Path,
    filename: str,
    compare_path: Optional[Path] = None,
) -> dict:
    """Análisis completo de imagen."""

    logger.info(f"Analizando imagen: {filename}")

    # Ejecutar análisis locales en paralelo
    (ela_result, noise_result, freq_result, meta_result,
     color_result, ai_sig_result) = await asyncio.gather(
        asyncio.to_thread(analyze_ela,              file_path),
        asyncio.to_thread(analyze_noise,            file_path),
        asyncio.to_thread(analyze_frequency,        file_path),
        asyncio.to_thread(analyze_metadata,         file_path),
        asyncio.to_thread(analyze_color_consistency,file_path),
        asyncio.to_thread(detect_ai_signatures,     file_path),
    )

    # Llamar a Hugging Face en paralelo
    hf_deepfake_raw, hf_ai_gen_raw = await asyncio.gather(
        call_huggingface_api(HF_MODELS["image_deepfake"], file_path),
        call_huggingface_api(HF_MODELS["image_ai_gen"],   file_path),
    )

    hf_deepfake_score = parse_hf_deepfake_result(
        hf_deepfake_raw if isinstance(hf_deepfake_raw, list) else []
    )
    hf_ai_score = parse_hf_deepfake_result(
        hf_ai_gen_raw if isinstance(hf_ai_gen_raw, list) else []
    )

    # Análisis de comparación si se subió archivo original
    comparison_result = None
    if compare_path:
        comparison_result = await asyncio.to_thread(compare_images, file_path, compare_path)

    # Calcular puntuación general (ensemble)
    scores = []
    weights = []

    # Análisis locales (siempre disponibles)
    scores.append(ela_result["manipulation_score"])
    weights.append(0.20)

    scores.append(noise_result["manipulation_score"])
    weights.append(0.15)

    scores.append(freq_result["manipulation_score"])
    weights.append(0.15)

    scores.append(color_result["manipulation_score"])
    weights.append(0.10)

    scores.append(ai_sig_result["manipulation_score"])
    weights.append(0.10)

    # HF modelos (mayor peso si disponibles)
    if hf_deepfake_score >= 0:
        scores.append(hf_deepfake_score)
        weights.append(0.20)

    if hf_ai_score >= 0:
        scores.append(hf_ai_score)
        weights.append(0.10)

    # Normalizar pesos
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]
    overall_score = round(sum(s * w for s, w in zip(scores, normalized_weights)), 1)

    # Determinación del veredicto
    verdict, verdict_color, confidence_label = get_verdict(overall_score)

    # Generar heatmap data
    heatmap = await asyncio.to_thread(generate_heatmap_data, file_path, ela_result, noise_result)

    return {
        "overall_score":    overall_score,
        "verdict":          verdict,
        "verdict_color":    verdict_color,
        "confidence_label": confidence_label,
        "hf_available":     hf_deepfake_score >= 0,
        "breakdown": {
            "ela": {
                "label":       "Error Level Analysis",
                "description": "Detecta regiones con niveles de compresión inconsistentes",
                "score":       ela_result["manipulation_score"],
                "details":     ela_result["details"],
                "icon":        "layers",
            },
            "noise": {
                "label":       "Análisis de Ruido",
                "description": "Identifica patrones de ruido artificiales o inconsistentes",
                "score":       noise_result["manipulation_score"],
                "details":     noise_result["details"],
                "icon":        "activity",
            },
            "frequency": {
                "label":       "Análisis de Frecuencia",
                "description": "Detecta artefactos de generación AI en dominio de frecuencias",
                "score":       freq_result["manipulation_score"],
                "details":     freq_result["details"],
                "icon":        "radio",
            },
            "color": {
                "label":       "Consistencia de Color",
                "description": "Analiza coherencia de iluminación y color en toda la imagen",
                "score":       color_result["manipulation_score"],
                "details":     color_result["details"],
                "icon":        "eye",
            },
            "ai_signatures": {
                "label":       "Firmas de IA Generativa",
                "description": "Detecta patrones característicos de DALL-E, Midjourney, Stable Diffusion",
                "score":       ai_sig_result["manipulation_score"],
                "details":     ai_sig_result["details"],
                "icon":        "cpu",
                "detected_tool": ai_sig_result.get("detected_tool"),
            },
            "ai_model": {
                "label":       "Modelo de IA (HuggingFace)",
                "description": "Clasificador neuronal entrenado en datasets de deepfakes",
                "score":       hf_deepfake_score if hf_deepfake_score >= 0 else None,
                "details":     "Análisis con modelo ViT entrenado en DFDC dataset" if hf_deepfake_score >= 0 else "No disponible — configura HF_TOKEN",
                "icon":        "brain",
                "available":   hf_deepfake_score >= 0,
            },
        },
        "metadata":    meta_result,
        "heatmap":     heatmap,
        "comparison":  comparison_result,
        "flags":       generate_flags(ela_result, noise_result, freq_result, ai_sig_result, overall_score),
        "recommendations": generate_recommendations(overall_score, ai_sig_result),
    }


async def analyze_audio_file(file_path: Path, filename: str) -> dict:
    """Análisis de audio para detección de voz sintética."""
    logger.info(f"Analizando audio: {filename}")
    audio_result = await asyncio.to_thread(analyze_audio, file_path)

    overall_score = audio_result["manipulation_score"]
    verdict, verdict_color, confidence_label = get_verdict(overall_score)

    return {
        "overall_score":    overall_score,
        "verdict":          verdict,
        "verdict_color":    verdict_color,
        "confidence_label": confidence_label,
        "hf_available":     False,
        "breakdown":        audio_result["breakdown"],
        "metadata":         audio_result.get("metadata", {}),
        "heatmap":          None,
        "comparison":       None,
        "flags":            audio_result.get("flags", []),
        "recommendations":  generate_recommendations(overall_score, {}),
    }


async def analyze_video_file(file_path: Path, filename: str, output_dir: str) -> dict:
    """Análisis de video frame-by-frame."""
    logger.info(f"Analizando video: {filename}")
    video_result = await asyncio.to_thread(analyze_video, file_path, output_dir)

    overall_score = video_result["manipulation_score"]
    verdict, verdict_color, confidence_label = get_verdict(overall_score)

    return {
        "overall_score":    overall_score,
        "verdict":          verdict,
        "verdict_color":    verdict_color,
        "confidence_label": confidence_label,
        "hf_available":     False,
        "breakdown":        video_result["breakdown"],
        "metadata":         video_result.get("metadata", {}),
        "heatmap":          video_result.get("heatmap"),
        "comparison":       None,
        "flags":            video_result.get("flags", []),
        "recommendations":  generate_recommendations(overall_score, {}),
        "frame_analysis":   video_result.get("frame_analysis", []),
    }


def get_verdict(score: float) -> tuple:
    if score < 20:
        return "AUTÉNTICO", "green", "Alta confianza — Sin manipulación detectada"
    elif score < 40:
        return "PROBABLEMENTE AUTÉNTICO", "green", "Baja probabilidad de manipulación"
    elif score < 60:
        return "INCIERTO", "yellow", "Resultados mixtos — Verificar manualmente"
    elif score < 80:
        return "PROBABLEMENTE FALSO", "red", "Alta probabilidad de manipulación"
    else:
        return "DEEPFAKE DETECTADO", "red", "Muy alta probabilidad de contenido sintético"


def generate_flags(ela, noise, freq, ai_sig, overall_score) -> list:
    flags = []
    if ela["manipulation_score"] > 60:
        flags.append({"type": "warning", "message": "Inconsistencias de compresión detectadas en zonas específicas"})
    if noise["manipulation_score"] > 65:
        flags.append({"type": "warning", "message": "Patrones de ruido anómalos — posible retoque digital"})
    if freq["manipulation_score"] > 70:
        flags.append({"type": "danger", "message": "Artefactos de frecuencia típicos de imágenes generadas por IA"})
    if ai_sig.get("detected_tool"):
        flags.append({"type": "danger", "message": f"Posibles firmas de {ai_sig['detected_tool']} detectadas"})
    if overall_score > 75:
        flags.append({"type": "danger", "message": "Múltiples indicadores apuntan a contenido sintético"})
    if not flags:
        flags.append({"type": "success", "message": "No se encontraron indicadores de manipulación significativos"})
    return flags


def generate_recommendations(score: float, ai_sig: dict) -> list:
    recs = [
        "Verifica el origen de este medio en fuentes primarias",
        "Busca la imagen/video en Google Images o TinEye para encontrar el original",
    ]
    if score > 50:
        recs += [
            "No compartas este contenido sin verificación adicional",
            "Consulta plataformas especializadas como Sensity AI o Reality Defender para confirmación",
        ]
    if score > 70:
        recs += [
            "Reporta este contenido a la plataforma donde lo encontraste",
            "Considera consultar a un experto en medios forenses",
        ]
    if ai_sig.get("detected_tool"):
        recs.append(f"Busca imágenes similares en comunidades de {ai_sig['detected_tool']}")
    return recs
