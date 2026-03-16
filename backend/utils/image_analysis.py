"""
VerifAI — Algoritmos de análisis de imagen
ELA, Ruido, Frecuencia, Metadata, Color, Firmas AI
Sin scipy — numpy puro para minimizar uso de memoria
"""

import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageFilter
from loguru import logger


# ── Helpers internos (reemplazan scipy) ────────────────────────

def _gaussian_blur_np(img_array, sigma=2):
    """Gaussian blur con numpy puro."""
    size = int(6 * sigma + 1) | 1
    x = np.arange(-(size // 2), size // 2 + 1).astype(float)
    k1d = np.exp(-x**2 / (2 * sigma**2))
    k1d /= k1d.sum()
    out = np.apply_along_axis(lambda r: np.convolve(r, k1d, mode='same'), 1, img_array)
    out = np.apply_along_axis(lambda c: np.convolve(c, k1d, mode='same'), 0, out)
    return out

def _convolve2d_np(img, kernel):
    """Convolución 2D con numpy puro."""
    ki, kj = kernel.shape
    pi, pj = ki // 2, kj // 2
    padded = np.pad(img, ((pi, pi), (pj, pj)), mode='edge')
    result = np.zeros_like(img, dtype=float)
    for i in range(ki):
        for j in range(kj):
            result += kernel[i, j] * padded[i:i+img.shape[0], j:j+img.shape[1]]
    return result


# ══════════════════════════════════════════════════════════════
# ELA — Error Level Analysis
# ══════════════════════════════════════════════════════════════
def analyze_ela(file_path: Path, quality: int = 95) -> dict:
    try:
        img = Image.open(file_path).convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        recompressed = Image.open(buffer).convert("RGB")
        ela_img = ImageChops.difference(img, recompressed)
        ela_array = np.array(ela_img).astype(float)

        mean_ela = float(np.mean(ela_array))
        std_ela  = float(np.std(ela_array))
        max_ela  = float(np.max(ela_array))

        threshold      = mean_ela + 2 * std_ela
        suspicious_pct = float(np.sum(ela_array > threshold) / ela_array.size * 100)

        score = min(100, round(
            (mean_ela / 10) * 20 +
            (std_ela / 15) * 30 +
            (suspicious_pct / 5) * 50, 1
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
    try:
        img       = Image.open(file_path).convert("L")
        img_array = np.array(img).astype(float)

        blurred   = _gaussian_blur_np(img_array, sigma=2)
        noise     = img_array - blurred

        noise_std  = float(np.std(noise))
        noise_mean = float(np.mean(np.abs(noise)))

        h, w       = noise.shape
        block_size = max(16, min(h, w) // 8)
        local_vars = []
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                local_vars.append(float(np.var(noise[i:i+block_size, j:j+block_size])))

        if local_vars:
            mean_var = float(np.mean(local_vars))
            cv       = float(np.std(local_vars) / (mean_var + 1e-6))
            var_of_vars = float(np.var(local_vars))
        else:
            mean_var = cv = var_of_vars = 0

        score = min(100, round(
            min(cv * 30, 40) +
            min((noise_std / 10) * 20, 30) +
            min((var_of_vars / 1000), 30), 1
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
    try:
        img  = Image.open(file_path).convert("L").resize((256, 256), Image.LANCZOS)
        arr  = np.array(img).astype(float)

        fft       = np.fft.fft2(arr)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)
        log_mag   = np.log1p(magnitude)

        center    = (128, 128)
        y_idx, x_idx = np.indices(log_mag.shape)
        distances = np.sqrt((x_idx - center[1])**2 + (y_idx - center[0])**2)

        high_freq_energy = float(np.mean(log_mag[distances > 80]))
        low_freq_energy  = float(np.mean(log_mag[distances < 20]))
        freq_ratio       = high_freq_energy / (low_freq_energy + 1e-6)

        row_periodicity  = float(np.std(np.mean(log_mag, axis=1)))
        col_periodicity  = float(np.std(np.mean(log_mag, axis=0)))
        periodicity_score = (row_periodicity + col_periodicity) / 2

        score = min(100, round(
            min(freq_ratio * 25, 40) +
            min(periodicity_score * 3, 35) +
            (25 if high_freq_energy > 3.5 else 0), 1
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
            TAG_SOFTWARE = 305
            TAG_MAKE     = 271
            TAG_DATETIME = 306
            TAG_GPS      = 34853

            software     = exif.get(TAG_SOFTWARE, "")
            make         = exif.get(TAG_MAKE, "")
            datetime_tag = exif.get(TAG_DATETIME, "")

            info["software"] = str(software) if software else None
            info["camera"]   = str(make) if make else None
            info["datetime"] = str(datetime_tag) if datetime_tag else None
            info["has_gps"]  = TAG_GPS in exif

            editing_sw = ["photoshop", "gimp", "lightroom", "midjourney",
                          "stable diffusion", "dall-e", "firefly", "runway", "ai"]
            sw_lower = str(software).lower()
            for sw in editing_sw:
                if sw in sw_lower:
                    suspicious_flags.append(f"Software de edición detectado: {software}")
                    break
        else:
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
    try:
        img = Image.open(file_path).convert("RGB").resize((256, 256), Image.LANCZOS)
        arr = np.array(img).astype(float)

        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

        r_mean, g_mean, b_mean = np.mean(r), np.mean(g), np.mean(b)

        rg_corr  = float(np.corrcoef(r.flatten(), g.flatten())[0, 1])
        rb_corr  = float(np.corrcoef(r.flatten(), b.flatten())[0, 1])
        gb_corr  = float(np.corrcoef(g.flatten(), b.flatten())[0, 1])
        avg_corr = (rg_corr + rb_corr + gb_corr) / 3

        h, w     = arr.shape[:2]
        quads    = [arr[:h//2, :w//2], arr[:h//2, w//2:],
                    arr[h//2:, :w//2], arr[h//2:, w//2:]]
        quad_means    = [float(np.mean(q)) for q in quads]
        lighting_var  = float(np.std(quad_means))

        score = min(100, round(
            max(0, (1 - avg_corr) * 40) +
            min(lighting_var / 5, 40) +
            (20 if abs(r_mean - g_mean) > 30 or abs(r_mean - b_mean) > 30 else 0), 1
        ))

        return {
            "manipulation_score": score,
            "details": f"Correlación canales: {avg_corr:.2f}, Variación iluminación: {lighting_var:.1f}",
            "channel_correlation": round(avg_corr, 3),
            "lighting_variation":  round(lighting_var, 3),
            "rgb_means": [round(r_mean, 1), round(float(np.mean(g)), 1), round(float(np.mean(b)), 1)],
        }
    except Exception as e:
        logger.warning(f"Error en color consistency: {e}")
        return {"manipulation_score": 0, "details": "Error en análisis de color", "error": str(e)}


# ══════════════════════════════════════════════════════════════
# DETECCIÓN DE FIRMAS DE IA GENERATIVA
# ══════════════════════════════════════════════════════════════
def detect_ai_signatures(file_path: Path) -> dict:
    try:
        img  = Image.open(file_path).convert("RGB")
        arr  = np.array(img).astype(float)

        score         = 0
        detected_tool = None
        indicators    = []

        gray = np.mean(arr, axis=2)

        # Laplaciano para detección de bordes
        laplacian = np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]], dtype=float)
        edges     = _convolve2d_np(gray, laplacian)
        edge_std  = float(np.std(edges))

        if edge_std < 15:
            score += 25
            indicators.append("Texturas excesivamente suaves (típico de AI)")

        # Uniformidad de ruido
        blurred      = _gaussian_blur_np(gray, sigma=2)
        noise_map    = gray - blurred
        h, w         = gray.shape
        block_stds   = []
        for i in range(0, h - 32, 32):
            for j in range(0, w - 32, 32):
                block_stds.append(float(np.std(noise_map[i:i+32, j:j+32])))

        if block_stds:
            mean_bs = float(np.mean(block_stds)) + 1e-6
            noise_uniformity = 1.0 - float(np.std(block_stds) / mean_bs)
        else:
            noise_uniformity = 0

        if noise_uniformity > 0.8:
            score += 20
            indicators.append("Ruido excesivamente uniforme")

        # Dimensiones características de AI
        ai_sizes = {512, 768, 1024, 1536, 2048, 640, 576}
        h_orig, w_orig = arr.shape[:2]
        if w_orig in ai_sizes or h_orig in ai_sizes:
            score += 15
            if w_orig == h_orig:
                score += 10
                indicators.append(f"Dimensiones cuadradas características de AI ({w_orig}x{h_orig})")
            else:
                indicators.append(f"Dimensión característica de AI ({w_orig}x{h_orig})")

        if score >= 35:
            if w_orig == h_orig and w_orig in {512, 768, 1024}:
                detected_tool = "Stable Diffusion / Midjourney"
            elif w_orig in {1024, 1792} or h_orig in {1024, 1792}:
                detected_tool = "DALL-E 3"
            else:
                detected_tool = "Herramienta AI Generativa"

        return {
            "manipulation_score": min(100, score),
            "details": "; ".join(indicators) if indicators else "Sin firmas AI detectadas",
            "indicators":       indicators,
            "detected_tool":    detected_tool,
            "edge_std":         round(edge_std, 3),
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
    try:
        img1 = Image.open(file_path).convert("RGB")
        img2 = Image.open(original_path).convert("RGB")

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
            "similarity_pct":      similarity,
            "mean_difference":     round(mean_diff, 2),
            "max_difference":      round(max_diff, 2),
            "modified_area_pct":   round(pct_diff, 2),
            "verdict": "Muy similar al original" if similarity > 85 else
                       "Diferencias notables"    if similarity > 60 else
                       "Archivos muy diferentes",
        }
    except Exception as e:
        return {"error": str(e), "similarity_pct": None}


# ══════════════════════════════════════════════════════════════
# GENERAR DATOS DE HEATMAP
# ══════════════════════════════════════════════════════════════
def generate_heatmap_data(file_path: Path, ela_result: dict, noise_result: dict) -> dict:
    try:
        img  = Image.open(file_path).convert("RGB").resize((64, 64), Image.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)
        recompressed = Image.open(buffer)

        diff  = ImageChops.difference(img, recompressed)
        arr   = np.array(diff).astype(float)
        gray  = np.mean(arr, axis=2)

        norm  = (gray - gray.min()) / (gray.max() - gray.min() + 1e-6)

        return {
            "width":     64,
            "height":    64,
            "data":      norm.flatten().tolist(),
            "max_value": float(gray.max()),
        }
    except Exception as e:
        return {"error": str(e), "data": [], "width": 0, "height": 0}
