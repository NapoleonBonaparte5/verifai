"""
Analizador de Imágenes
Técnicas: ELA, Análisis de Ruido, EXIF Metadata, Frecuencias, IA vía Hugging Face
"""

import os
import io
import math
import json
import struct
import asyncio
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ExifTags
import httpx
from loguru import logger

HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_MODEL = "Organika/sdxl-detector"  # Modelo gratuito en HF para detectar AI


# ============================
# ANÁLISIS ELA (Error Level Analysis)
# ============================
def ela_analysis(image_path: str, quality: int = 90) -> dict:
    """
    ELA detecta manipulaciones comparando la imagen original
    con una versión recomprimida. Zonas alteradas aparecen con
    niveles de error diferentes.
    """
    try:
        img = Image.open(image_path).convert("RGB")

        # Recomprimir a calidad menor
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        recompressed = Image.open(buffer).convert("RGB")

        # Calcular diferencia
        orig_array = np.array(img, dtype=np.float32)
        recomp_array = np.array(recompressed, dtype=np.float32)
        diff = np.abs(orig_array - recomp_array)

        # Métricas
        mean_diff = float(np.mean(diff))
        max_diff = float(np.max(diff))
        std_diff = float(np.std(diff))

        # Score: alta varianza en ELA = más sospechoso
        # Valores normales: mean_diff < 8, std_diff < 10
        suspicion = 0.0
        if mean_diff > 15:
            suspicion += 35
        elif mean_diff > 8:
            suspicion += 15

        if std_diff > 15:
            suspicion += 25
        elif std_diff > 10:
            suspicion += 10

        # Detectar zonas con alta diferencia (posibles manipulaciones)
        high_diff_mask = diff.mean(axis=2) > (mean_diff + 2 * std_diff)
        suspicious_area_pct = float(high_diff_mask.mean() * 100)

        if suspicious_area_pct > 5:
            suspicion += 20
        elif suspicious_area_pct > 2:
            suspicion += 10

        return {
            "suspicionScore": min(suspicion, 100),
            "meanError": round(mean_diff, 2),
            "maxError": round(max_diff, 2),
            "stdError": round(std_diff, 2),
            "suspiciousAreaPercent": round(suspicious_area_pct, 2),
            "details": _ela_details(mean_diff, std_diff, suspicious_area_pct),
        }
    except Exception as e:
        logger.warning(f"ELA fallback: {e}")
        return {"suspicionScore": 0, "error": str(e)}


def _ela_details(mean_diff, std_diff, area_pct) -> str:
    if mean_diff < 5 and std_diff < 8:
        return "Niveles de error uniformes — imagen probablemente auténtica"
    elif mean_diff > 15:
        return "Niveles de error elevados — posibles modificaciones detectadas"
    elif area_pct > 5:
        return f"{area_pct:.1f}% del área muestra anomalías — revisar zonas marcadas"
    return "Niveles de error moderados — análisis adicional recomendado"


# ============================
# ANÁLISIS DE RUIDO
# ============================
def noise_analysis(image_path: str) -> dict:
    """
    Las imágenes generadas por IA tienen patrones de ruido
    diferentes a las fotografías reales (más uniformes/sintéticos).
    """
    try:
        img = Image.open(image_path).convert("L")  # Escala de grises
        arr = np.array(img, dtype=np.float32)

        # Calcular ruido local (diferencia con media local)
        from PIL import ImageFilter
        blurred = Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=2))
        blur_arr = np.array(blurred, dtype=np.float32)
        noise = arr - blur_arr

        # Métricas de ruido
        noise_mean = float(np.mean(np.abs(noise)))
        noise_std = float(np.std(noise))

        # Uniformidad del ruido (AI tiende a ser muy uniforme)
        # Dividir en bloques y comparar varianza
        h, w = arr.shape
        block_size = max(h // 8, 16)
        block_stds = []
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = noise[i:i+block_size, j:j+block_size]
                block_stds.append(float(np.std(block)))

        if block_stds:
            noise_uniformity = float(np.std(block_stds) / (np.mean(block_stds) + 1e-6))
        else:
            noise_uniformity = 0

        # Score: ruido muy uniforme → más sintético
        suspicion = 0.0
        if noise_uniformity < 0.3:
            suspicion += 30  # Ruido muy uniforme = AI
        elif noise_uniformity < 0.5:
            suspicion += 15

        if noise_mean < 1.5:
            suspicion += 20  # Muy poco ruido = posiblemente sintético
        elif noise_mean < 3:
            suspicion += 10

        return {
            "suspicionScore": min(suspicion, 100),
            "noiseMean": round(noise_mean, 3),
            "noiseStd": round(noise_std, 3),
            "noiseUniformity": round(noise_uniformity, 3),
            "details": _noise_details(noise_uniformity, noise_mean),
        }
    except Exception as e:
        logger.warning(f"Noise analysis error: {e}")
        return {"suspicionScore": 0, "error": str(e)}


def _noise_details(uniformity, mean) -> str:
    if uniformity < 0.3:
        return "Ruido excepcionalmente uniforme — patrón típico de imágenes generadas por IA"
    elif mean < 2:
        return "Nivel de ruido muy bajo — posible imagen sintética o procesada digitalmente"
    elif uniformity > 0.8:
        return "Distribución de ruido natural — característica de fotografías reales"
    return "Patrón de ruido mixto — análisis no concluyente"


# ============================
# ANÁLISIS DE METADATA EXIF
# ============================
def exif_analysis(image_path: str) -> dict:
    """
    Analiza metadatos EXIF para detectar inconsistencias
    o ausencia sospechosa de datos de cámara.
    """
    try:
        img = Image.open(image_path)
        exif_data = img._getexif() if hasattr(img, "_getexif") and img._getexif() else {}

        if not exif_data:
            return {
                "suspicionScore": 25,
                "hasExif": False,
                "details": "Sin metadatos EXIF — común en imágenes generadas por IA o editadas",
                "flags": ["NO_EXIF"],
            }

        flags = []
        suspicion = 0

        # Mapear tags
        exif = {}
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, str(tag_id))
            exif[tag] = str(value)[:100]

        # Verificar campos clave
        has_camera = "Make" in exif or "Model" in exif
        has_software = "Software" in exif
        has_datetime = "DateTime" in exif or "DateTimeOriginal" in exif

        if not has_camera:
            suspicion += 20
            flags.append("NO_CAMERA_INFO")

        if has_software:
            software = exif.get("Software", "").lower()
            ai_tools = ["stable diffusion", "midjourney", "dall-e", "firefly", "photoshop", "gimp"]
            for tool in ai_tools:
                if tool in software:
                    suspicion += 40
                    flags.append(f"AI_TOOL_{tool.upper().replace(' ', '_')}")
                    break

        if not has_datetime:
            suspicion += 10
            flags.append("NO_DATETIME")

        return {
            "suspicionScore": min(suspicion, 100),
            "hasExif": True,
            "camera": exif.get("Make", "") + " " + exif.get("Model", ""),
            "software": exif.get("Software", "Desconocido"),
            "dateTime": exif.get("DateTimeOriginal", exif.get("DateTime", "No disponible")),
            "flags": flags,
            "details": _exif_details(flags, has_camera),
        }
    except Exception as e:
        return {"suspicionScore": 15, "hasExif": False, "details": f"Error al leer EXIF: {str(e)}", "flags": []}


def _exif_details(flags, has_camera) -> str:
    if "AI_TOOL_STABLE_DIFFUSION" in flags:
        return "Metadata indica generación con Stable Diffusion"
    if "AI_TOOL_DALL-E" in flags:
        return "Metadata indica generación con DALL-E"
    if "NO_CAMERA_INFO" in flags and "NO_EXIF" not in flags:
        return "Sin información de cámara — posible imagen sintética o editada"
    if has_camera:
        return "Información de cámara presente — consistente con fotografía real"
    return "Metadata limitada — análisis no concluyente"


# ============================
# ANÁLISIS DE FRECUENCIAS
# ============================
def frequency_analysis(image_path: str) -> dict:
    """
    Las imágenes AI tienen patrones frecuenciales distintos
    a las fotografías. Analiza con FFT.
    """
    try:
        img = Image.open(image_path).convert("L")
        # Redimensionar para consistencia
        img = img.resize((256, 256), Image.LANCZOS)
        arr = np.array(img, dtype=np.float32)

        # FFT 2D
        fft = np.fft.fft2(arr)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.log(np.abs(fft_shift) + 1)

        # Dividir en zonas (low/mid/high frecuencias)
        h, w = magnitude.shape
        center_h, center_w = h // 2, w // 2

        # Radio para zonas
        r1, r2 = h // 8, h // 4

        y, x = np.ogrid[:h, :w]
        dist = np.sqrt((y - center_h)**2 + (x - center_w)**2)

        low_freq = float(magnitude[dist < r1].mean())
        mid_freq = float(magnitude[(dist >= r1) & (dist < r2)].mean())
        high_freq = float(magnitude[dist >= r2].mean())

        # Ratio low/high — AI tiende a tener más energía en bajas frecuencias
        ratio = low_freq / (high_freq + 1e-6)
        suspicion = 0.0

        if ratio > 4:
            suspicion += 30  # Dominancia exagerada de bajas frecuencias
        elif ratio > 2.5:
            suspicion += 15

        # Uniformidad radial (AI suele ser más uniforme)
        radial_std = float(np.std([low_freq, mid_freq, high_freq]))
        if radial_std < 0.5:
            suspicion += 20

        return {
            "suspicionScore": min(suspicion, 100),
            "lowFreqEnergy": round(low_freq, 3),
            "midFreqEnergy": round(mid_freq, 3),
            "highFreqEnergy": round(high_freq, 3),
            "lowHighRatio": round(ratio, 3),
            "details": _freq_details(ratio, suspicion),
        }
    except Exception as e:
        logger.warning(f"Frequency analysis error: {e}")
        return {"suspicionScore": 0, "error": str(e)}


def _freq_details(ratio, suspicion) -> str:
    if ratio > 4:
        return "Dominancia atípica de bajas frecuencias — patrón de generación AI"
    elif ratio > 2.5:
        return "Distribución frecuencial ligeramente anómala"
    return "Distribución frecuencial natural — consistente con fotografía"


# ============================
# DETECCIÓN IA via Hugging Face
# ============================
async def hf_ai_detection(image_path: str) -> dict:
    """
    Usa Hugging Face Inference API para detectar si la imagen
    fue generada por IA usando modelos pre-entrenados.
    """
    api_key = os.getenv("HF_API_KEY", "")
    if not api_key or api_key == "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        return {
            "suspicionScore": 0,
            "available": False,
            "details": "Hugging Face API no configurada — análisis local únicamente",
        }

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()

        headers = {"Authorization": f"Bearer {api_key}"}
        api_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(api_url, headers=headers, content=image_data)

        if response.status_code == 200:
            results = response.json()
            if isinstance(results, list) and results:
                # Buscar label de AI-generated
                ai_score = 0
                for item in results:
                    label = str(item.get("label", "")).lower()
                    score = float(item.get("score", 0))
                    if any(kw in label for kw in ["fake", "ai", "generated", "synthetic"]):
                        ai_score = max(ai_score, score * 100)

                return {
                    "suspicionScore": round(ai_score, 1),
                    "available": True,
                    "rawResults": results[:3],
                    "details": f"Modelo IA: {ai_score:.1f}% probabilidad de imagen sintética",
                }

        return {"suspicionScore": 0, "available": True, "details": "Modelo no disponible temporalmente"}

    except Exception as e:
        logger.warning(f"HF API error: {e}")
        return {"suspicionScore": 0, "available": False, "details": f"Error en API: {str(e)}"}


# ============================
# ANÁLISIS PRINCIPAL DE IMAGEN
# ============================
async def analyze_image(image_path: str, meta: dict) -> dict:
    """
    Análisis completo de imagen para detección de deepfakes/AI.
    Combina múltiples técnicas en un score final ponderado.
    """
    logger.info(f"Analizando imagen: {meta.get('originalName')}")

    # Ejecutar análisis en paralelo donde sea posible
    ela = ela_analysis(image_path)
    noise = noise_analysis(image_path)
    exif = exif_analysis(image_path)
    freq = frequency_analysis(image_path)
    hf = await hf_ai_detection(image_path)

    # Pesos de cada análisis
    weights = {
        "ela":   0.30,
        "noise": 0.20,
        "exif":  0.20,
        "freq":  0.15,
        "hf":    0.15,
    }

    # Score ponderado de sospecha
    ela_score   = ela.get("suspicionScore", 0)
    noise_score = noise.get("suspicionScore", 0)
    exif_score  = exif.get("suspicionScore", 0)
    freq_score  = freq.get("suspicionScore", 0)
    hf_score    = hf.get("suspicionScore", 0)

    total_suspicion = (
        ela_score   * weights["ela"]   +
        noise_score * weights["noise"] +
        exif_score  * weights["exif"]  +
        freq_score  * weights["freq"]  +
        hf_score    * weights["hf"]
    )

    # Autenticidad = inverso de sospecha
    authenticity_score = max(0, min(100, 100 - total_suspicion))

    # Veredicto
    verdict, verdict_color = _get_verdict(authenticity_score)

    # Información de la imagen
    try:
        img = Image.open(image_path)
        width, height = img.size
        img_mode = img.mode
        img_format = img.format or meta.get("ext", "").upper()
    except:
        width = height = 0
        img_mode = "N/A"
        img_format = meta.get("ext", "").upper()

    return {
        "authenticityScore": round(authenticity_score, 1),
        "suspicionScore": round(total_suspicion, 1),
        "verdict": verdict,
        "verdictColor": verdict_color,
        "breakdown": {
            "ela": {
                "name": "Análisis de Error (ELA)",
                "score": round(ela_score, 1),
                "details": ela.get("details", ""),
                "weight": weights["ela"],
            },
            "noise": {
                "name": "Patrones de Ruido",
                "score": round(noise_score, 1),
                "details": noise.get("details", ""),
                "weight": weights["noise"],
            },
            "exif": {
                "name": "Metadatos EXIF",
                "score": round(exif_score, 1),
                "details": exif.get("details", ""),
                "flags": exif.get("flags", []),
                "weight": weights["exif"],
            },
            "frequency": {
                "name": "Análisis de Frecuencias",
                "score": round(freq_score, 1),
                "details": freq.get("details", ""),
                "weight": weights["freq"],
            },
            "aiModel": {
                "name": "Modelo IA (Hugging Face)",
                "score": round(hf_score, 1),
                "details": hf.get("details", ""),
                "available": hf.get("available", False),
                "weight": weights["hf"],
            },
        },
        "imageInfo": {
            "width": width,
            "height": height,
            "format": img_format,
            "mode": img_mode,
            "hasExif": exif.get("hasExif", False),
            "camera": exif.get("camera", "Desconocido"),
            "software": exif.get("software", "Desconocido"),
        },
        "recommendations": _get_recommendations(authenticity_score, exif, ela, hf),
    }


def _get_verdict(score: float) -> tuple:
    if score >= 80:
        return "Probablemente Auténtico", "green"
    elif score >= 60:
        return "Incierto — Revisión Recomendada", "yellow"
    elif score >= 40:
        return "Sospechoso — Posible Manipulación", "orange"
    else:
        return "Alta Probabilidad de Deepfake/IA", "red"


def _get_recommendations(score: float, exif: dict, ela: dict, hf: dict) -> list:
    recs = []

    if score < 60:
        recs.append("Busca la imagen en Google Imágenes o TinEye para encontrar el original")
        recs.append("Verifica la fuente original del medio antes de compartirlo")

    if not exif.get("hasExif"):
        recs.append("La ausencia de metadatos EXIF es una señal de alerta en imágenes sospechosas")

    if ela.get("suspicionScore", 0) > 40:
        recs.append("El análisis ELA detectó posibles zonas editadas — revisa las áreas marcadas")

    if hf.get("available") and hf.get("suspicionScore", 0) > 50:
        recs.append("El modelo de IA indica alta probabilidad de imagen sintética")

    if score >= 80:
        recs.append("Esta imagen muestra características consistentes con fotografías reales")

    if not recs:
        recs.append("Resultado no concluyente — usa múltiples herramientas para mayor seguridad")

    return recs
