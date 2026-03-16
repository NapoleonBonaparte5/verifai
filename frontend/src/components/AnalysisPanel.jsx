import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, ShieldAlert, ShieldCheck, AlertTriangle,
  RotateCcw, File, ChevronDown, CheckCircle2, XCircle,
  Minus, Info, Clock
} from 'lucide-react';
import toast from 'react-hot-toast';

const VERDICT_CONFIG = {
  green:  { icon: ShieldCheck,  label: 'Probablemente Auténtico',           bg: 'bg-score-green',  text: 'score-green' },
  yellow: { icon: AlertTriangle, label: 'Incierto — Revisión Recomendada',  bg: 'bg-score-yellow', text: 'score-yellow' },
  orange: { icon: ShieldAlert,   label: 'Sospechoso — Posible Manipulación', bg: 'bg-score-orange', text: 'score-orange' },
  red:    { icon: ShieldAlert,   label: 'Alta Probabilidad de Deepfake/IA', bg: 'bg-score-red',    text: 'score-red' },
};

const MEDIA_ICONS = {
  image: '🖼️', video: '🎥', audio: '🎵',
};

export default function AnalysisPanel({ file, fileId, onReset }) {
  const [status, setStatus]   = useState('idle'); // idle | analyzing | done | error
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState('');
  const [elapsed, setElapsed] = useState(0);
  const [openSection, setOpenSection] = useState(null);

  // Timer during analysis
  useEffect(() => {
    let t;
    if (status === 'analyzing') {
      setElapsed(0);
      t = setInterval(() => setElapsed(e => e + 0.1), 100);
    }
    return () => clearInterval(t);
  }, [status]);

  const handleAnalyze = async () => {
    setStatus('analyzing');
    setError('');
    setResult(null);

    try {
      const res  = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileId, options: {} }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error en el análisis');

      setResult(data);
      setStatus('done');
      toast.success(`Análisis completado en ${(data.analysisTime / 1000).toFixed(1)}s`);
    } catch (err) {
      setStatus('error');
      setError(err.message);
      toast.error(err.message);
    }
  };

  return (
    <div className="card-glow p-6 space-y-5">

      {/* File info header */}
      <div className="flex items-center gap-3 p-4 bg-dark-surface rounded-xl border border-dark-border">
        <div className="text-2xl">{MEDIA_ICONS[file.mediaType] || '📁'}</div>
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium text-sm truncate">{file.name}</p>
          <p className="text-gray-500 text-xs">
            {file.size} · <span className="font-mono">.{file.ext?.toUpperCase()}</span>
            {' · '}
            <span className="capitalize text-gray-400">{file.mediaType}</span>
          </p>
        </div>
        <button
          onClick={onReset}
          className="p-2 rounded-lg hover:bg-white/5 text-gray-500 hover:text-white transition-all"
          title="Cambiar archivo"
        >
          <RotateCcw size={15} />
        </button>
      </div>

      <AnimatePresence mode="wait">

        {/* IDLE */}
        {status === 'idle' && (
          <motion.div key="idle"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          >
            <div className="text-center py-4 mb-4">
              <p className="text-gray-400 text-sm">
                El análisis utilizará múltiples técnicas forenses para determinar
                la autenticidad de tu archivo.
              </p>
            </div>
            <button onClick={handleAnalyze} className="btn-brand w-full justify-center py-4 text-base">
              <Shield size={18} />
              Iniciar Análisis de Autenticidad
              <span className="text-brand-dark text-xs ml-1 opacity-70">~5-15s</span>
            </button>
          </motion.div>
        )}

        {/* ANALYZING */}
        {status === 'analyzing' && (
          <motion.div key="analyzing"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="py-6"
          >
            <ScannerAnimation elapsed={elapsed} mediaType={file.mediaType} />
          </motion.div>
        )}

        {/* DONE */}
        {status === 'done' && result && (
          <motion.div key="done"
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <ResultDisplay result={result} openSection={openSection} setOpenSection={setOpenSection} />

            <div className="flex gap-3">
              <button
                onClick={() => { setStatus('idle'); setResult(null); }}
                className="btn-ghost flex-1 justify-center text-sm"
              >
                <RotateCcw size={14} />
                Analizar de nuevo
              </button>
              <button onClick={onReset} className="btn-ghost flex-1 justify-center text-sm">
                Nuevo archivo
              </button>
            </div>
          </motion.div>
        )}

        {/* ERROR */}
        {status === 'error' && (
          <motion.div key="error"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <div className="flex items-start gap-3 p-4 bg-red-500/5 border border-red-500/20 rounded-xl">
              <XCircle size={18} className="text-danger flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-danger font-medium text-sm">Error en el análisis</p>
                <p className="text-gray-500 text-xs mt-1">{error}</p>
              </div>
            </div>
            <button onClick={() => setStatus('idle')} className="btn-ghost w-full justify-center text-sm">
              <RotateCcw size={14} />
              Intentar de nuevo
            </button>
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}

// ── Scanner animation during analysis ─────────────────────────
function ScannerAnimation({ elapsed, mediaType }) {
  const steps = {
    image: ['Cargando imagen...', 'Ejecutando ELA...', 'Analizando ruido...', 'Verificando EXIF...', 'Análisis de frecuencias...', 'Consultando modelo IA...'],
    video: ['Cargando video...', 'Extrayendo frames...', 'Analizando consistencia...', 'Detectando artefactos...', 'Calculando score...'],
    audio: ['Cargando audio...', 'Análisis espectral...', 'Detectando síntesis...', 'Verificando artefactos...', 'Calculando score...'],
  };
  const currentSteps = steps[mediaType] || steps.image;
  const stepIndex = Math.min(Math.floor(elapsed / 2), currentSteps.length - 1);

  return (
    <div className="flex flex-col items-center gap-5">
      {/* Animated scanner */}
      <div className="relative w-20 h-20">
        <div className="absolute inset-0 rounded-full border-2 border-brand/20 animate-ping" />
        <div className="absolute inset-2 rounded-full border-2 border-brand/30" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Shield size={24} className="text-brand animate-pulse" />
        </div>
        {/* Rotating ring */}
        <svg className="absolute inset-0 w-full h-full animate-spin" style={{ animationDuration: '2s' }}>
          <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(0,245,212,0.3)"
            strokeWidth="2" strokeDasharray="60 160" strokeLinecap="round" />
        </svg>
      </div>

      <div className="text-center">
        <p className="text-white font-medium text-sm mb-1">Analizando autenticidad...</p>
        <p className="terminal text-xs opacity-70 mb-3">{currentSteps[stepIndex]}</p>
        <p className="text-gray-600 text-xs font-mono">{elapsed.toFixed(1)}s</p>
      </div>

      {/* Step dots */}
      <div className="flex gap-1.5">
        {currentSteps.map((_, i) => (
          <div key={i} className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
            i <= stepIndex ? 'bg-brand' : 'bg-dark-border'
          }`} />
        ))}
      </div>

      {/* Progress bar */}
      <div className="w-full bg-dark-surface rounded-full h-0.5 overflow-hidden">
        <motion.div
          className="progress-brand h-full rounded-full"
          animate={{ width: ['5%', '90%'] }}
          transition={{ duration: 14, ease: 'easeOut' }}
        />
      </div>

      <p className="text-gray-600 text-xs text-center max-w-xs">
        Aplicando técnicas forenses: ELA, análisis de ruido, metadata, frecuencias y modelos IA
      </p>
    </div>
  );
}

// ── Result display ─────────────────────────────────────────────
function ResultDisplay({ result, openSection, setOpenSection }) {
  const score   = result.authenticityScore || 0;
  const color   = result.verdictColor || 'yellow';
  const config  = VERDICT_CONFIG[color] || VERDICT_CONFIG.yellow;
  const VIcon   = config.icon;
  const breakdown = result.breakdown || {};

  return (
    <div className="space-y-4">
      {/* Main verdict */}
      <div className={`p-5 rounded-2xl border ${config.bg}`}>
        <div className="flex items-center gap-4">
          {/* Score gauge */}
          <div className="relative flex-shrink-0">
            <ScoreGauge score={score} color={color} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <VIcon size={18} className={config.text} />
              <p className={`font-display font-bold text-sm ${config.text}`}>{config.label}</p>
            </div>
            <p className="text-gray-400 text-xs leading-relaxed">
              {score >= 80
                ? 'Los indicadores forenses son consistentes con contenido auténtico.'
                : score >= 60
                ? 'Se detectaron algunas anomalías. Se recomienda verificación adicional.'
                : score >= 40
                ? 'Múltiples indicadores apuntan a posible manipulación o generación por IA.'
                : 'Alta probabilidad de que este contenido sea un deepfake o generado por IA.'
              }
            </p>
            <div className="flex items-center gap-3 mt-2">
              <span className="terminal text-xs opacity-70">
                Score: {score.toFixed(1)}%
              </span>
              <span className="text-gray-600 text-xs">·</span>
              <span className="flex items-center gap-1 text-gray-500 text-xs">
                <Clock size={11} />
                {(result.analysisTime / 1000).toFixed(1)}s
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Breakdown by technique */}
      <div className="space-y-2">
        <p className="text-gray-500 text-xs font-medium uppercase tracking-wider px-1">
          Desglose por técnica
        </p>
        {Object.entries(breakdown).map(([key, data]) => (
          <BreakdownItem
            key={key}
            data={data}
            isOpen={openSection === key}
            onToggle={() => setOpenSection(openSection === key ? null : key)}
          />
        ))}
      </div>

      {/* Recommendations */}
      {result.recommendations?.length > 0 && (
        <div className="p-4 bg-dark-surface rounded-xl border border-dark-border">
          <p className="text-white text-xs font-semibold mb-3 flex items-center gap-1.5">
            <Info size={13} className="text-brand" />
            Recomendaciones
          </p>
          <ul className="space-y-2">
            {result.recommendations.map((rec, i) => (
              <li key={i} className="text-gray-400 text-xs flex items-start gap-2">
                <span className="text-brand mt-0.5 flex-shrink-0">▸</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-gray-600 text-xs text-center px-2">
        ⚠️ Esta herramienta es auxiliar y no garantiza un 100% de precisión.
        Contrasta siempre con otras fuentes antes de sacar conclusiones.
      </p>
    </div>
  );
}

// ── Score gauge ────────────────────────────────────────────────
function ScoreGauge({ score, color }) {
  const colorMap = { green: '#00e676', yellow: '#ffb347', orange: '#ff7043', red: '#ff4d4d' };
  const c = colorMap[color] || '#ffb347';
  const r = 28;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;

  return (
    <div className="relative w-20 h-20">
      <svg width="80" height="80" className="-rotate-90">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#1e2d45" strokeWidth="6" />
        <motion.circle
          cx="40" cy="40" r={r}
          fill="none"
          stroke={c}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - dash }}
          transition={{ duration: 1.2, ease: 'easeOut', delay: 0.3 }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display font-bold text-lg leading-none" style={{ color: c }}>
          {Math.round(score)}
        </span>
        <span className="text-gray-600 text-xs">%</span>
      </div>
    </div>
  );
}

// ── Breakdown item ─────────────────────────────────────────────
function BreakdownItem({ data, isOpen, onToggle }) {
  const score      = data.score || 0;
  const isGood     = score < 30;
  const isMedium   = score >= 30 && score < 60;
  const isBad      = score >= 60;

  const barColor = isGood ? '#00e676' : isMedium ? '#ffb347' : '#ff4d4d';
  const Icon     = isGood ? CheckCircle2 : isBad ? XCircle : Minus;
  const iconColor = isGood ? 'text-safe' : isBad ? 'text-danger' : 'text-warning';

  return (
    <div className="bg-dark-surface border border-dark-border rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 p-3 hover:bg-white/2 transition-colors"
      >
        <Icon size={14} className={`${iconColor} flex-shrink-0`} />
        <span className="flex-1 text-left text-white text-xs font-medium">{data.name}</span>

        {/* Mini bar */}
        <div className="w-20 h-1.5 bg-dark-border rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: barColor }}
            initial={{ width: 0 }}
            animate={{ width: `${score}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>

        <span className="text-xs font-mono w-8 text-right" style={{ color: barColor }}>
          {Math.round(score)}%
        </span>
        <motion.div animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={13} className="text-gray-600 flex-shrink-0" />
        </motion.div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="px-4 pb-4 pt-2 border-t border-dark-border">
              <p className="text-gray-400 text-xs leading-relaxed">{data.details}</p>
              {data.flags?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {data.flags.map(f => (
                    <span key={f} className="tag text-xs text-danger border-danger/20 bg-danger/5 font-mono">
                      {f}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
