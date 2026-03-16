"""
VerifAI — Algoritmos de análisis de imagen
ELA, Ruido, Frecuencia, Metadata, Color, Firmas AI
"""

import io
import struct
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageEnhance
from loguru import logger


# ══════════════════════════════════════════════════════════════
# ELA — Error Level Analysis
# ══════════════════════════════════════════════════════════════
def analyze_ela(file_path: Path, quality: int = 95) -> dict:
    """
    Analiza niveles de error de compresión JPEG.
    Regiones manipuladas muestran niveles ELA distintos al resto.
    """
    try:
        img = Image.open(file_path).convert("RGB")

        # Re-comprimir y calcular diferencia
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        recompressed = Image.open(buffer).convert("RGB")

        ela_img = ImageChops.difference(img, recompressed)
        ela_array = np.array(ela_img).astype(float)

        # Métricas estadísticas
        mean_ela = float(np.mean(ela_array))
        std_ela  = float(np.std(ela_array))
        max_ela  = float(np.max(ela_array))

        # Detectar regiones sospechosas (alta diferencia)
        threshold      = mean_ela + 2 * std_ela
        suspicious_pct = float(np.sum(ela_array > threshold) / ela_array.size * 100)

        # Score de manipulación (0-100)
        score = min(100, round(
            (mean_ela / 10) * 20 +
            (std_ela / 15) * 30 +
            (suspicious_pct / 5) * 50,
            1
        ))

        return {
            "manipulation_score": score,
            "details": f"ELA media: {mean_ela:.2f}, Zonas sospechosas: {suspicious_pct:.1f}%",
            "mean_ela": round(mean_ela, 3),
            "std_ela":  round(std_ela, 3),
            "max_ela":  round(max_ela, 3),
            "suspicious_pct": round(suspicious_pct, 2),
        }
    except Exception as e:
        logger.warning(f"Error en ELA: {e}")
        return {"manipulation_score": 0, "details": "No se pudo aplicar ELA", "error": str(e)}


# ══════════════════════════════════════════════════════════════
# ANÁLISIS DE RUIDO
# ══════════════════════════════════════════════════════════════
def analyze_noise(file_path: Path) -> dict:
    """
    Analiza patrones de ruido para detectar inconsistencias.
    Imágenes manipuladas o generadas por IA tienen ruido uniforme anómalo.
    """
    try:
        img        = Image.open(file_path).convert("L")
        img_array  = np.array(img).astype(float)

        # Filtrado para aislar el ruido
        blurred    = np.array(Image.fromarray(img_array.astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=2))).astype(float)
        noise      = img_array - blurred

        # Estadísticas del ruido
        noise_std  = float(np.std(noise))
        noise_mean = float(np.mean(np.abs(noise)))

        # Varianza local en bloques (inconsistencia espacial)
        h, w = noise.shape
        block_size = max(16, min(h, w) // 8)
        local_vars = []
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = noise[i:i+block_size, j:j+block_size]
                local_vars.append(float(np.var(block)))

        if local_vars:
            var_of_vars = float(np.var(local_vars))
            mean_var    = float(np.mean(local_vars))
            cv          = float(np.std(local_vars) / (mean_var + 1e-6))  # Coeficiente de variación
        else:
            var_of_vars = 0
            mean_var    = 0
            cv          = 0

        # Score: alta inconsistencia = más sospechoso
        score = min(100, round(
            min(cv * 30, 40) +
            min((noise_std / 10) * 20, 30) +
            min((var_of_vars / 1000), 30),
            1
        ))

        return {
            "manipulation_score": score,
            "details": f"Ruido std: {noise_std:.2f}, Inconsistencia espacial: {cv:.2f}",
            "noise_std":  round(noise_std, 3),
            "noise_mean": round(noise_mean, 3),
            "spatial_inconsistency": round(cv, 3),
        }
    except Exception as e:
        logger.warning(f"Error en noise analysis: {e}")
        return {"manipulation_score": 0, "details": "Error en análisis de ruido", "error": str(e)}


# ══════════════════════════════════════════════════════════════
# ANÁLISIS DE FRECUENCIA (FFT)
# ══════════════════════════════════════════════════════════════
def analyze_frequency(file_path: Path) -> dict:
    """
    Análisis en dominio de frecuencias (FFT).
    Imágenes AI generadas muestran patrones regulares anómalos.
    """
    try:
        img   = Image.open(file_path).convert("L")
        # Reducir para rapidez
        img   = img.resize((256, 256), Image.LANCZOS)
        arr   = np.array(img).astype(float)

        # FFT 2D
        fft      = np.fft.fft2(arr)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)
        log_mag   = np.log1p(magnitude)

        # Análisis del espectro
        center     = (128, 128)
        y_idx, x_idx = np.indices(log_mag.shape)
        distances  = np.sqrt((x_idx - center[1])**2 + (y_idx - center[0])**2)

        # Energía en alta frecuencia (anillos exteriores)
        high_freq_mask  = distances > 80
        low_freq_mask   = distances < 20
        high_freq_energy = float(np.mean(log_mag[high_freq_mask]))
        low_freq_energy  = float(np.mean(log_mag[low_freq_mask]))
        freq_ratio       = high_freq_energy / (low_freq_energy + 1e-6)

        # Periodicidad anómala (grids de AI)
        row_periodicity  = float(np.std(np.mean(log_mag, axis=1)))
        col_periodicity  = float(np.std(np.mean(log_mag, axis=0)))
        periodicity_score = (row_periodicity + col_periodicity) / 2

        # Score
        score = min(100, round(
            min(freq_ratio * 25, 40) +
            min(periodicity_score * 3, 35) +
            (25 if high_freq_energy > 3.5 else 0),
            1
        ))

        return {
            "manipulation_score": score,
            "details": f"Ratio frecuencias: {freq_ratio:.3f}, Periodicidad: {periodicity_score:.3f}",
            "freq_ratio":         round(freq_ratio, 4),
            "high_freq_energy":   round(high_freq_energy, 4),
            "periodicity_score":  round(periodicity_score, 4),
        }
    except Exception as e:
        logger.warning(f"Error en frequency analysis: {e}")
        return {"manipulation_score": 0, "details": "Error en análisis de frecuencia", "error": str(e)}


# ══════════════════════════════════════════════════════════════
# ANÁLISIS DE METADATA EXIF
# ══════════════════════════════════════════════════════════════
def analyze_metadata(file_path: Path) -> dict:
    """
    Extrae y analiza metadata EXIF para detectar inconsistencias.
    """
    try:
        img  = Image.open(file_path)
        exif = img._getexif() if hasattr(img, '_getexif') else None

        info = {
            "format":   img.format or "Desconocido",
            "mode":     img.mode,
            "size":     f"{img.width}x{img.height}",
            "has_exif": exif is not None,
        }

        suspicious_flags = []

        if exif:
            # Tag IDs relevantes
            TAG_MAKE       = 271
            TAG_SOFTWARE   = 305
            TAG_DATETIME   = 306
            TAG_GPS        = 34853

            software = exif.get(TAG_SOFTWARE, "")
            make     = exif.get(TAG_MAKE, "")
            datetime_tag = exif.get(TAG_DATETIME, "")

            info["software"] = str(software) if software else None
            info["camera"]   = str(make) if make else None
            info["datetime"] = str(datetime_tag) if datetime_tag else None
            info["has_gps"]  = TAG_GPS in exif

            # Detectar software de edición
            editing_software = ["photoshop", "gimp", "lightroom", "capture one",
                                 "affinity", "canva", "midjourney", "stable diffusion",
                                 "dall-e", "firefly", "runway", "ai"]
            sw_lower = str(software).lower()
            for sw in editing_software:
                if sw in sw_lower:
                    suspicious_flags.append(f"Software de edición detectado: {software}")
                    break
        else:
            # Sin EXIF puede indicar procesamiento/generación
            suspicious_flags.append("Sin metadata EXIF — posible procesamiento digital")

        info["suspicious_flags"] = suspicious_flags
        return info

    except Exception as e:
        logger.warning(f"Error en metadata: {e}")
        return {"format": "Error", "has_exif": False, "suspicious_flags": [], "error": str(e)}


# ══════════════════════════════════════════════════════════════
# CONSISTENCIA DE COLOR
# ══════════════════════════════════════════════════════════════
def analyze_color_consistency(file_path: Path) -> dict:
    """
    Analiza consistencia de iluminación y distribución de color.
    Imágenes manipuladas suelen tener inconsistencias cromáticas.
    """
    try:
        img   = Image.open(file_path).convert("RGB")
        img   = img.resize((256, 256), Image.LANCZOS)
        arr   = np.array(img).astype(float)

        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

        # Estadísticas por canal
        r_mean, g_mean, b_mean = np.mean(r), np.mean(g), np.mean(b)
        r_std, g_std, b_std    = np.std(r), np.std(g), np.std(b)

        # Correlación entre canales (debería ser alta en fotos reales)
        rg_corr = float(np.corrcoef(r.flatten(), g.flatten())[0, 1])
        rb_corr = float(np.corrcoef(r.flatten(), b.flatten())[0, 1])
        gb_corr = float(np.corrcoef(g.flatten(), b.flatten())[0, 1])
        avg_corr = (rg_corr + rb_corr + gb_corr) / 3

        # Variación de iluminación en cuadrantes
        h, w = arr.shape[:2]
        quads = [
            arr[:h//2, :w//2],
            arr[:h//2, w//2:],
            arr[h//2:, :w//2],
            arr[h//2:, w//2:],
        ]
        quad_means = [float(np.mean(q)) for q in quads]
        lighting_var = float(np.std(quad_means))

        # Score
        score = min(100, round(
            max(0, (1 - avg_corr) * 40) +
            min(lighting_var / 5, 40) +
            (20 if abs(r_mean - g_mean) > 30 or abs(r_mean - b_mean) > 30 else 0),
            1
        ))

        return {
            "manipulation_score": score,
            "details": f"Correlación canales: {avg_corr:.2f}, Variación iluminación: {lighting_var:.1f}",
            "channel_correlation": round(avg_corr, 3),
            "lighting_variation":  round(lighting_var, 3),
            "rgb_means": [round(r_mean,1), round(g_mean,1), round(b_mean,1)],
        }
    except Exception as e:
        logger.warning(f"Error en color consistency: {e}")
        return {"manipulation_score": 0, "details": "Error en análisis de color", "error": str(e)}


# ══════════════════════════════════════════════════════════════
# DETECCIÓN DE FIRMAS DE IA GENERATIVA
# ══════════════════════════════════════════════════════════════
def detect_ai_signatures(file_path: Path) -> dict:
    """
    Detecta patrones característicos de herramientas AI generativas.
    Busca grids regulares, texturas perfectas y otras firmas.
    """
    try:
        img   = Image.open(file_path).convert("RGB")
        arr   = np.array(img).astype(float)

        score         = 0
        detected_tool = None
        indicators    = []

        # 1. Suavidad excesiva (AI genera piel/texturas perfectas)
        gray      = np.mean(arr, axis=2)
        laplacian = np.array([
            [-1,-1,-1],[-1,8,-1],[-1,-1,-1]
        ])
        from scipy import ndimage
        edges     = ndimage.convolve(gray, laplacian)
        edge_std  = float(np.std(edges))

        if edge_std < 15:
            score += 25
            indicators.append("Texturas excesivamente suaves (típico de AI)")

        # 2. Uniformidad de ruido (AI genera ruido muy uniforme)
        noise_map = gray - ndimage.gaussian_filter(gray, sigma=2)
        noise_uniformity = 1.0 - float(np.std([
            np.std(noise_map[i:i+32, j:j+32])
            for i in range(0, gray.shape[0]-32, 32)
            for j in range(0, gray.shape[1]-32, 32)
        ]) / (np.mean([
            np.std(noise_map[i:i+32, j:j+32])
            for i in range(0, gray.shape[0]-32, 32)
            for j in range(0, gray.shape[1]-32, 32)
        ]) + 1e-6))

        if noise_uniformity > 0.8:
            score += 20
            indicators.append("Ruido excesivamente uniforme")

        # 3. Dimensiones características de AI (512, 768, 1024, etc.)
        ai_sizes = {512, 768, 1024, 1536, 2048, 640, 576}
        h, w     = arr.shape[:2]
        if w in ai_sizes or h in ai_sizes:
            score += 15
            if w == h:
                score += 10
                indicators.append(f"Dimensiones cuadradas características de AI ({w}x{h})")
            else:
                indicators.append(f"Dimensión característica de AI ({w}x{h})")

        # 4. Detectar posible herramienta
        if score >= 35:
            if w == h and w in {512, 768, 1024}:
                detected_tool = "Stable Diffusion / Midjourney"
            elif w in {1024, 1792} or h in {1024, 1792}:
                detected_tool = "DALL-E 3"
            else:
                detected_tool = "Herramienta AI Generativa"

        return {
            "manipulation_score": min(100, score),
            "details": "; ".join(indicators) if indicators else "Sin firmas AI detectadas",
            "indicators":     indicators,
            "detected_tool":  detected_tool,
            "edge_std":       round(edge_std, 3),
            "noise_uniformity": round(noise_uniformity, 3),
        }
    except Exception as e:
        logger.warning(f"Error en AI signatures: {e}")
        return {
            "manipulation_score": 0,
            "details": "Error en detección de firmas AI",
            "detected_tool": None,
            "error": str(e),
        }


# ══════════════════════════════════════════════════════════════
# COMPARACIÓN CON ORIGINAL
# ══════════════════════════════════════════════════════════════
def compare_images(file_path: Path, original_path: Path) -> dict:
    """Compara pixel a pixel con la imagen original."""
    try:
        img1 = Image.open(file_path).convert("RGB")
        img2 = Image.open(original_path).convert("RGB")

        # Redimensionar al mismo tamaño
        size = (min(img1.width, img2.width), min(img1.height, img2.height))
        img1 = img1.resize(size, Image.LANCZOS)
        img2 = img2.resize(size, Image.LANCZOS)

        diff     = ImageChops.difference(img1, img2)
        diff_arr = np.array(diff).astype(float)

        mean_diff = float(np.mean(diff_arr))
        max_diff  = float(np.max(diff_arr))
        pct_diff  = float(np.sum(diff_arr > 10) / diff_arr.size * 100)

        similarity = max(0, round(100 - mean_diff / 2.55, 1))

        return {
            "similarity_pct": similarity,
            "mean_difference": round(mean_diff, 2),
            "max_difference":  round(max_diff, 2),
            "modified_area_pct": round(pct_diff, 2),
            "verdict": "Muy similar al original" if similarity > 85 else
                       "Diferencias notables" if similarity > 60 else
                       "Archivos muy diferentes",
        }
    except Exception as e:
        return {"error": str(e), "similarity_pct": None}


# ══════════════════════════════════════════════════════════════
# GENERAR DATOS DE HEATMAP
# ══════════════════════════════════════════════════════════════
def generate_heatmap_data(file_path: Path, ela_result: dict, noise_result: dict) -> dict:
    """
    Genera datos para visualizar las zonas más sospechosas.
    Devuelve una grilla normalizada para renderizar en frontend.
    """
    try:
        img   = Image.open(file_path).convert("RGB")
        img   = img.resize((64, 64), Image.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)
        recompressed = Image.open(buffer)

        diff  = ImageChops.difference(img, recompressed)
        arr   = np.array(diff).astype(float)
        gray  = np.mean(arr, axis=2)

        # Normalizar 0-1
        norm  = (gray - gray.min()) / (gray.max() - gray.min() + 1e-6)

        return {
            "width":  64,
            "height": 64,
            "data":   norm.flatten().tolist(),
            "max_value": float(gray.max()),
        }
    except Exception as e:
        return {"error": str(e), "data": [], "width": 0, "height": 0}
