"""
VerifAI — Análisis de Audio
Detección de voz sintética mediante análisis espectral
"""

import wave
import struct
from pathlib import Path

import numpy as np
from loguru import logger


def analyze_audio(file_path: Path) -> dict:
    """
    Analiza un archivo de audio para detectar voz sintética.
    Usa análisis espectral básico sin dependencias pesadas.
    """
    try:
        # Intentar leer con wave (solo WAV)
        if str(file_path).lower().endswith(".wav"):
            return _analyze_wav(file_path)
        else:
            # Para MP3 y otros, análisis de bytes básico
            return _analyze_binary(file_path)
    except Exception as e:
        logger.error(f"Error en análisis de audio: {e}")
        return _fallback_audio_result()


def _analyze_wav(file_path: Path) -> dict:
    """Análisis profundo de archivos WAV."""
    try:
        with wave.open(str(file_path), 'rb') as wav:
            n_channels  = wav.getnchannels()
            sample_rate = wav.getframerate()
            n_frames    = wav.getnframes()
            sampwidth   = wav.getsampwidth()

            # Leer samples (máximo 5 segundos para rapidez)
            max_frames = min(n_frames, sample_rate * 5)
            frames     = wav.readframes(max_frames)

        # Convertir a numpy
        if sampwidth == 2:
            samples = np.frombuffer(frames, dtype=np.int16).astype(float)
        elif sampwidth == 4:
            samples = np.frombuffer(frames, dtype=np.int32).astype(float)
        else:
            samples = np.frombuffer(frames, dtype=np.uint8).astype(float)

        if len(samples) == 0:
            return _fallback_audio_result()

        # Normalizar
        max_val  = np.max(np.abs(samples)) + 1e-6
        samples  = samples / max_val

        # ── Análisis espectral (FFT) ─────────────────────────
        fft_vals = np.abs(np.fft.rfft(samples[:min(len(samples), 8192)]))
        freqs    = np.fft.rfftfreq(min(len(samples), 8192), 1/sample_rate)

        # Energía en bandas de frecuencia
        def band_energy(f_low, f_high):
            mask = (freqs >= f_low) & (freqs < f_high)
            return float(np.mean(fft_vals[mask])) if np.any(mask) else 0.0

        sub_bass    = band_energy(20, 250)
        mid         = band_energy(250, 2000)
        presence    = band_energy(2000, 5000)
        brilliance  = band_energy(5000, 20000)

        total       = sub_bass + mid + presence + brilliance + 1e-6

        # Voz humana: más energía en mids y presence
        voice_ratio = (mid + presence) / total

        # ── Zero Crossing Rate ───────────────────────────────
        zcr = float(np.mean(np.abs(np.diff(np.sign(samples)))) / 2)

        # ── Análisis de silencios ────────────────────────────
        frame_size   = 1024
        rms_frames   = []
        for i in range(0, len(samples) - frame_size, frame_size):
            frame = samples[i:i+frame_size]
            rms_frames.append(float(np.sqrt(np.mean(frame**2))))

        silence_ratio = float(np.sum(np.array(rms_frames) < 0.01) / (len(rms_frames) + 1e-6))
        rms_std       = float(np.std(rms_frames))

        # ── Score de manipulación ────────────────────────────
        score = 0

        # Voz sintética tiende a tener voice_ratio muy alto y uniforme
        if voice_ratio > 0.90:
            score += 25

        # ZCR muy uniforme = sintético
        if zcr > 0.3:
            score += 20

        # Poca variación de energía = sintético
        if rms_std < 0.05:
            score += 20

        # Muchos silencios perfectos = sintético
        if silence_ratio > 0.4:
            score += 15

        # Baja frecuencia de sub-bass (síntesis artificial)
        if sub_bass / total < 0.02:
            score += 20

        score = min(100, score)
        verdict_label = get_audio_verdict(score)

        return {
            "manipulation_score": score,
            "breakdown": {
                "spectral": {
                    "label":   "Análisis Espectral",
                    "description": "Distribución de energía por bandas de frecuencia",
                    "score":   min(100, round((1 - voice_ratio) * 50 + (zcr * 50), 1)),
                    "details": f"Ratio voz: {voice_ratio:.2f}, ZCR: {zcr:.3f}",
                    "icon":    "activity",
                },
                "temporal": {
                    "label":   "Coherencia Temporal",
                    "description": "Variación natural de energía a lo largo del tiempo",
                    "score":   min(100, round((1 - rms_std * 5) * 50, 1)),
                    "details": f"Variación RMS: {rms_std:.3f}",
                    "icon":    "clock",
                },
                "silence": {
                    "label":   "Patrones de Silencio",
                    "description": "Naturalidad de los silencios y pausas",
                    "score":   round(silence_ratio * 80, 1),
                    "details": f"Ratio de silencio: {silence_ratio:.2f}",
                    "icon":    "volume-x",
                },
            },
            "metadata": {
                "sample_rate":  sample_rate,
                "channels":     n_channels,
                "duration_s":   round(n_frames / sample_rate, 1),
                "format":       "WAV",
                "bit_depth":    sampwidth * 8,
            },
            "flags": _generate_audio_flags(score, voice_ratio, rms_std, silence_ratio),
        }

    except Exception as e:
        logger.warning(f"Error analizando WAV: {e}")
        return _fallback_audio_result()


def _analyze_binary(file_path: Path) -> dict:
    """Análisis básico para formatos no-WAV (MP3, etc.)."""
    try:
        file_size = file_path.stat().st_size
        with open(file_path, 'rb') as f:
            header = f.read(512)

        # Detectar formato por header
        fmt = "Desconocido"
        if header[:3] == b'ID3' or (header[:2] == b'\xff\xfb'):
            fmt = "MP3"
        elif header[:4] == b'fLaC':
            fmt = "FLAC"
        elif b'OggS' in header[:8]:
            fmt = "OGG"

        # Score básico (sin análisis profundo)
        score = 30  # Score neutral sin datos suficientes

        return {
            "manipulation_score": score,
            "breakdown": {
                "format_check": {
                    "label":   "Verificación de Formato",
                    "description": f"Análisis básico de archivo {fmt}",
                    "score":   score,
                    "details": f"Formato: {fmt}, Tamaño: {file_size/1024:.1f}KB. Para análisis completo, usa formato WAV.",
                    "icon":    "file-audio",
                }
            },
            "metadata": {"format": fmt, "size_kb": round(file_size/1024, 1)},
            "flags": [{"type": "info", "message": f"Análisis limitado para {fmt}. Convierte a WAV para resultados más precisos."}],
        }
    except Exception as e:
        return _fallback_audio_result()


def _generate_audio_flags(score, voice_ratio, rms_std, silence_ratio) -> list:
    flags = []
    if score > 60:
        flags.append({"type": "danger", "message": "Alta probabilidad de voz sintética detectada"})
    if voice_ratio > 0.90:
        flags.append({"type": "warning", "message": "Distribución espectral inusualmente uniforme"})
    if rms_std < 0.05:
        flags.append({"type": "warning", "message": "Energía demasiado constante — poco natural"})
    if silence_ratio > 0.4:
        flags.append({"type": "warning", "message": "Patrones de silencio artificialmente perfectos"})
    if not flags:
        flags.append({"type": "success", "message": "Características espectrales consistentes con voz humana natural"})
    return flags


def get_audio_verdict(score: float) -> str:
    if score < 30:  return "Voz probablemente auténtica"
    if score < 50:  return "Resultados mixtos"
    if score < 70:  return "Posible voz sintética"
    return "Alta probabilidad de voz sintética"


def _fallback_audio_result() -> dict:
    return {
        "manipulation_score": 25,
        "breakdown": {
            "generic": {
                "label":   "Análisis General",
                "description": "Análisis básico del archivo de audio",
                "score":   25,
                "details": "No se pudo realizar análisis profundo de este formato",
                "icon":    "music",
            }
        },
        "metadata":  {"format": "Desconocido"},
        "flags": [{"type": "info", "message": "Sube el archivo en formato WAV para un análisis más preciso"}],
    }
