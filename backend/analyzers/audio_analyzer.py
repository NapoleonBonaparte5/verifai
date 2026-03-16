"""
Analizador de Audio
Técnicas: Análisis espectral, detección de voz sintética, artefactos de compresión
"""

import os
import struct
import wave
import math
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger


def _read_wav(audio_path: str) -> Optional[tuple]:
    """Lee un archivo WAV y retorna (samples, sample_rate)"""
    try:
        with wave.open(audio_path, 'rb') as w:
            frames = w.readframes(w.getnframes())
            sr = w.getframerate()
            channels = w.getnchannels()
            sampwidth = w.getsampwidth()

        # Convertir bytes a numpy
        if sampwidth == 2:
            samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            samples = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            return None

        # Mono
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1)

        return samples, sr
    except Exception:
        return None


def spectral_analysis(audio_path: str) -> dict:
    """
    Analiza el espectrograma del audio.
    Las voces sintéticas tienen características espectrales distintivas:
    - Ausencia de ruido de fondo natural
    - Transiciones demasiado limpias
    - Patrones de frecuencia artificialmente uniformes
    """
    try:
        result = _read_wav(audio_path)
        if result is None:
            return {"suspicionScore": 0, "details": "Formato de audio no analizable directamente"}

        samples, sr = result

        if len(samples) < sr * 0.5:
            return {"suspicionScore": 0, "details": "Audio demasiado corto para análisis"}

        # FFT para análisis espectral
        chunk_size = min(4096, len(samples))
        fft = np.abs(np.fft.rfft(samples[:chunk_size]))
        freqs = np.fft.rfftfreq(chunk_size, 1.0 / sr)

        # Energía en bandas de frecuencia de voz (85-3400 Hz)
        voice_mask = (freqs >= 85) & (freqs <= 3400)
        high_mask = freqs > 3400
        total_energy = fft.sum() + 1e-10
        voice_energy = fft[voice_mask].sum() / total_energy
        high_energy = fft[high_mask].sum() / total_energy

        # Análisis de silencio (voces sintéticas suelen tener silencios perfectos)
        silence_threshold = 0.01
        silence_ratio = float(np.mean(np.abs(samples) < silence_threshold))

        # Varianza de amplitud (voces reales varían más)
        amplitude_var = float(np.var(np.abs(samples)))

        suspicion = 0.0

        # Muy poco ruido de alta frecuencia → posiblemente sintético
        if high_energy < 0.02:
            suspicion += 25

        # Silencios perfectos → TTS/síntesis
        if silence_ratio > 0.4:
            suspicion += 20

        # Varianza de amplitud muy baja → voz monótona sintética
        if amplitude_var < 0.001:
            suspicion += 25

        # Energía de voz dominante (>95%) → sin ruido de fondo
        if voice_energy > 0.95:
            suspicion += 15

        return {
            "suspicionScore": min(suspicion, 100),
            "voiceEnergyRatio": round(float(voice_energy), 3),
            "highFreqEnergyRatio": round(float(high_energy), 3),
            "silenceRatio": round(silence_ratio, 3),
            "amplitudeVariance": round(amplitude_var, 6),
            "sampleRate": sr,
            "durationSeconds": round(len(samples) / sr, 2),
            "details": _spectral_details(suspicion, silence_ratio, amplitude_var),
        }
    except Exception as e:
        logger.warning(f"Spectral analysis error: {e}")
        return {"suspicionScore": 0, "error": str(e)}


def _spectral_details(suspicion, silence_ratio, amp_var) -> str:
    if suspicion > 60:
        return "Múltiples indicadores de audio sintético detectados"
    elif suspicion > 30:
        if silence_ratio > 0.4:
            return "Silencios atípicamente perfectos — posible texto a voz (TTS)"
        if amp_var < 0.001:
            return "Variación de amplitud anormalmente baja — voz posiblemente sintética"
        return "Algunas características sospechosas detectadas"
    return "Características espectrales consistentes con audio natural"


def compression_artifact_analysis(audio_path: str) -> dict:
    """
    Los deepfakes de audio suelen pasar por múltiples compresiones
    que dejan artefactos detectables.
    """
    try:
        result = _read_wav(audio_path)
        if result is None:
            return {"suspicionScore": 0, "details": "No analizable"}

        samples, sr = result

        # Buscar clipping (indicador de procesamiento excesivo)
        clip_ratio = float(np.mean(np.abs(samples) > 0.95))

        # Buscar discontinuidades bruscas (joins de TTS)
        diffs = np.abs(np.diff(samples))
        discontinuity_ratio = float(np.mean(diffs > 0.1))

        suspicion = 0.0
        if clip_ratio > 0.05:
            suspicion += 30
        if discontinuity_ratio > 0.01:
            suspicion += 25

        return {
            "suspicionScore": min(suspicion, 100),
            "clippingRatio": round(clip_ratio, 4),
            "discontinuityRatio": round(discontinuity_ratio, 4),
            "details": _compression_details(clip_ratio, discontinuity_ratio),
        }
    except Exception as e:
        return {"suspicionScore": 0, "error": str(e)}


def _compression_details(clip, discont) -> str:
    if clip > 0.05:
        return "Clipping detectado — señal procesada o saturada artificialmente"
    if discont > 0.01:
        return "Discontinuidades abruptas — posibles cortes y uniones de audio sintético"
    return "Artefactos de compresión dentro de rango normal"


async def analyze_audio(audio_path: str, meta: dict) -> dict:
    """Análisis completo de audio para detección de síntesis/deepfake"""
    logger.info(f"Analizando audio: {meta.get('originalName')}")

    spectral = spectral_analysis(audio_path)
    compression = compression_artifact_analysis(audio_path)

    weights = {"spectral": 0.65, "compression": 0.35}

    s_score = spectral.get("suspicionScore", 0)
    c_score = compression.get("suspicionScore", 0)

    total_suspicion = s_score * weights["spectral"] + c_score * weights["compression"]
    authenticity_score = max(0, min(100, 100 - total_suspicion))
    verdict, verdict_color = _get_verdict(authenticity_score)

    return {
        "authenticityScore": round(authenticity_score, 1),
        "suspicionScore": round(total_suspicion, 1),
        "verdict": verdict,
        "verdictColor": verdict_color,
        "breakdown": {
            "spectral": {
                "name": "Análisis Espectral",
                "score": round(s_score, 1),
                "details": spectral.get("details", ""),
                "sampleRate": spectral.get("sampleRate", 0),
                "duration": spectral.get("durationSeconds", 0),
            },
            "compression": {
                "name": "Artefactos de Compresión",
                "score": round(c_score, 1),
                "details": compression.get("details", ""),
            },
        },
        "audioInfo": {
            "sampleRate": spectral.get("sampleRate", 0),
            "durationSeconds": spectral.get("durationSeconds", 0),
            "format": meta.get("ext", "").upper(),
        },
        "recommendations": _audio_recommendations(authenticity_score, spectral),
    }


def _get_verdict(score):
    if score >= 80:
        return "Probablemente Auténtico", "green"
    elif score >= 60:
        return "Incierto — Revisión Recomendada", "yellow"
    elif score >= 40:
        return "Sospechoso — Posible Síntesis", "orange"
    else:
        return "Alta Probabilidad de Audio Sintético", "red"


def _audio_recommendations(score, spectral):
    recs = []
    if score < 60:
        recs.append("Verifica el audio comparándolo con grabaciones conocidas de la misma persona")
        recs.append("Busca inconsistencias en el tono o pronunciación")
    if spectral.get("silenceRatio", 0) > 0.4:
        recs.append("Los silencios perfectos son una señal característica de texto a voz (TTS)")
    if score >= 80:
        recs.append("El audio muestra características naturales consistentes con grabación real")
    if not recs:
        recs.append("Usa múltiples herramientas de verificación para mayor confianza")
    return recs
