import React, { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft, Download, Share2, CheckCircle, AlertTriangle,
  XCircle, Clock, Shield, ChevronDown, ExternalLink,
  Layers, Activity, Radio, Eye, Cpu, Brain, Film, Music
} from 'lucide-react';
import toast from 'react-hot-toast';

const ICON_MAP = {
  layers: Layers, activity: Activity, radio: Radio,
  eye: Eye, cpu: Cpu, brain: Brain, film: Film,
  music: Music, clock: Clock, 'file-audio': Music,
  'volume-x': Activity,
};

function ScoreGauge({ score, color }) {
  const [animated, setAnimated] = useState(0);
  const circumference = 251.2;

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(score), 300);
    return () => clearTimeout(timer);
  }, [score]);

  const strokeColor = color === 'green' ? '#2E7D32'
    : color === 'yellow' ? '#F57F17'
    : '#C62828';

  const offset = circumference - (animated / 100) * circumference;

  return (
    <div className="relative w-40 h-40 mx-auto">
      <svg className="w-40 h-40 -rotate-90" viewBox="0 0 100 100">
        {/* Background circle */}
        <circle cx="50" cy="50" r="40"
          fill="none" stroke="#21262D" strokeWidth="8" />
        {/* Score circle */}
        <circle cx="50" cy="50" r="40"
          fill="none"
          stroke={strokeColor}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)', filter: `drop-shadow(0 0 6px ${strokeColor}66)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-3xl font-bold text-white">{score}%</span>
        <span className="text-xs text-gray-500 mt-0.5">probabilidad</span>
      </div>
    </div>
  );
}

function HeatmapViewer({ heatmap, filename }) {
  if (!heatmap || !heatmap.data || heatmap.data.length === 0) return null;

  const { width, height, data } = heatmap;

  return (
    <div className="card p-5">
      <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
        <Eye size={16} className="text-blue-400" />
        Mapa de calor — Zonas sospechosas
      </h3>
      <p className="text-gray-500 text-xs mb-4">
        Las zonas más brillantes indican mayor probabilidad de manipulación.
      </p>
      <div className="flex justify-center">
        <canvas
          ref={el => {
            if (!el) return;
            const ctx = el.getContext('2d');
            el.width  = width;
            el.height = height;
            for (let i = 0; i < data.length; i++) {
              const val = data[i];
              const x   = i % width;
              const y   = Math.floor(i / width);
              // Heatmap color: low=blue, mid=yellow, high=red
              const r = Math.round(255 * Math.min(1, val * 2));
              const g = Math.round(255 * Math.max(0, 1 - Math.abs(val - 0.5) * 2));
              const b = Math.round(255 * Math.max(0, 1 - val * 2));
              ctx.fillStyle = `rgba(${r},${g},${b},${0.3 + val * 0.7})`;
              ctx.fillRect(x, y, 1, 1);
            }
          }}
          className="rounded-lg"
          style={{ width: '256px', height: '256px', imageRendering: 'pixelated' }}
        />
      </div>
      <p className="text-xs text-gray-600 text-center mt-3 font-mono">{width}x{height}px · Resolución de análisis</p>
    </div>
  );
}

function BreakdownCard({ item, delay }) {
  const [open, setOpen] = useState(false);
  const Icon = ICON_MAP[item.icon] || Shield;
  const score = item.score;

  const scoreColor = score === null || score === undefined ? 'text-gray-500'
    : score < 40 ? 'text-green-400'
    : score < 65 ? 'text-yellow-400'
    : 'text-red-400';

  const barColor = score === null ? 'bg-gray-600'
    : score < 40 ? 'bg-green-500'
    : score < 65 ? 'bg-yellow-500'
    : 'bg-red-500';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="card overflow-hidden"
    >
      <button
        className="w-full p-4 text-left flex items-center gap-4 hover:bg-white/2 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <div className="w-9 h-9 rounded-xl bg-blue-700/10 border border-blue-700/20
                         flex items-center justify-center flex-shrink-0">
          <Icon size={16} className="text-blue-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-medium text-white text-sm">{item.label}</span>
            <span className={`font-mono font-bold text-sm ${scoreColor}`}>
              {score !== null && score !== undefined ? `${score}%` : 'N/A'}
            </span>
          </div>
          <div className="w-full bg-dark-border rounded-full h-1.5 overflow-hidden">
            <motion.div
              className={`h-full ${barColor} rounded-full`}
              initial={{ width: 0 }}
              animate={{ width: score !== null && score !== undefined ? `${score}%` : '0%' }}
              transition={{ duration: 1, delay: delay + 0.2 }}
            />
          </div>
        </div>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={14} className="text-gray-500 flex-shrink-0" />
        </motion.div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="px-4 pb-4 border-t border-dark-border pt-3 space-y-2">
              <p className="text-gray-500 text-xs">{item.description}</p>
              {item.details && (
                <p className="text-gray-400 text-xs font-mono bg-dark-surface px-3 py-2 rounded-lg">
                  {item.details}
                </p>
              )}
              {item.detected_tool && (
                <div className="flex items-center gap-2 text-xs text-orange-400 bg-orange-400/10
                                 border border-orange-400/20 px-3 py-2 rounded-lg">
                  <AlertTriangle size={12} />
                  Herramienta detectada: <span className="font-bold">{item.detected_tool}</span>
                </div>
              )}
              {item.available === false && (
                <p className="text-xs text-gray-600 italic">
                  Configura HUGGINGFACE_API_TOKEN para activar este módulo
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function FlagItem({ flag }) {
  const colors = {
    success: 'border-green-400/20 bg-green-400/5 text-green-400',
    warning: 'border-yellow-400/20 bg-yellow-400/5 text-yellow-400',
    danger:  'border-red-400/20 bg-red-400/5 text-red-400',
    info:    'border-blue-400/20 bg-blue-400/5 text-blue-400',
  };
  const icons = {
    success: CheckCircle, warning: AlertTriangle, danger: XCircle, info: Shield,
  };
  const Icon = icons[flag.type] || Shield;
  return (
    <div className={`flex items-start gap-2 px-3 py-2.5 rounded-xl border text-xs ${colors[flag.type] || colors.info}`}>
      <Icon size={13} className="flex-shrink-0 mt-0.5" />
      <span>{flag.message}</span>
    </div>
  );
}

export default function ResultPage() {
  const { id }      = useParams();
  const { state }   = useLocation();
  const navigate    = useNavigate();
  const [result, setResult]   = useState(state?.result || null);
  const [loading, setLoading] = useState(!state?.result);

  useEffect(() => {
    if (!result) {
      fetch(`/api/results/${id}`)
        .then(r => r.json())
        .then(data => { setResult(data); setLoading(false); })
        .catch(() => { toast.error('No se encontró el resultado'); navigate('/'); });
    }
  }, [id]);

  const handleDownload = async () => {
    try {
      const res = await fetch(`/api/download/report/${id}`);
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = `verifai-${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Reporte PDF descargado');
    } catch {
      toast.error('Error al descargar el reporte');
    }
  };

  const handleShare = () => {
    const text = result
      ? `Analicé este contenido con VerifAI. Veredicto: ${result.verdict} (${result.overall_score}% probabilidad de manipulación)`
      : 'Verificado con VerifAI';
    if (navigator.share) {
      navigator.share({ title: 'VerifAI', text, url: window.location.href });
    } else {
      navigator.clipboard.writeText(`${text}\n${window.location.href}`);
      toast.success('Enlace copiado al portapapeles');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="relative w-16 h-16">
            <div className="w-16 h-16 border-2 border-blue-700/30 border-t-blue-500 rounded-full animate-spin" />
          </div>
          <p className="text-gray-400 font-medium">Cargando resultado...</p>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const score   = result.overall_score || 0;
  const color   = result.verdict_color || 'yellow';
  const verdict = result.verdict || 'DESCONOCIDO';

  const verdictConfig = {
    green:  { bg: 'bg-green-400/10', border: 'border-green-400/20', text: 'text-green-400', Icon: CheckCircle },
    yellow: { bg: 'bg-yellow-400/10', border: 'border-yellow-400/20', text: 'text-yellow-400', Icon: AlertTriangle },
    red:    { bg: 'bg-red-400/10', border: 'border-red-400/20', text: 'text-red-400', Icon: XCircle },
  };
  const vc = verdictConfig[color] || verdictConfig.yellow;

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      {/* Back + actions */}
      <div className="flex items-center justify-between mb-8">
        <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm">
          <ArrowLeft size={16} />
          Nuevo análisis
        </Link>
        <div className="flex gap-2">
          <button onClick={handleShare} className="btn-ghost text-sm py-2 px-4">
            <Share2 size={14} />
            Compartir
          </button>
          <button onClick={handleDownload} className="btn-primary text-sm py-2 px-4">
            <Download size={14} />
            PDF
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* LEFT — Veredicto principal */}
        <div className="lg:col-span-1 space-y-5">
          {/* Score card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card p-6 text-center"
          >
            <ScoreGauge score={score} color={color} />

            <div className={`mt-5 px-4 py-3 rounded-xl border ${vc.bg} ${vc.border} flex items-center justify-center gap-2`}>
              <vc.Icon size={18} className={vc.text} />
              <span className={`font-display font-bold text-sm ${vc.text}`}>{verdict}</span>
            </div>

            <p className="text-gray-500 text-xs mt-3 leading-relaxed">
              {result.confidence_label}
            </p>
          </motion.div>

          {/* File info */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card p-4 space-y-3"
          >
            <h3 className="text-white font-semibold text-sm">Información del archivo</h3>
            {[
              { label: 'Archivo',  value: result.filename },
              { label: 'Tipo',     value: (result.file_type || '').toUpperCase() },
              { label: 'Tiempo',   value: `${result.analysis_time}s` },
              { label: 'Fecha',    value: result.analyzed_at?.slice(0, 10) },
              { label: 'HF Model', value: result.hf_available ? '✅ Activo' : '⚠️ Sin token' },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between text-xs">
                <span className="text-gray-500">{label}</span>
                <span className="text-gray-300 font-mono truncate max-w-[140px] text-right">{value}</span>
              </div>
            ))}
          </motion.div>

          {/* Flags */}
          {result.flags?.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="space-y-2"
            >
              <h3 className="text-white font-semibold text-sm px-1">Alertas detectadas</h3>
              {result.flags.map((flag, i) => <FlagItem key={i} flag={flag} />)}
            </motion.div>
          )}
        </div>

        {/* RIGHT — Breakdown + heatmap + recommendations */}
        <div className="lg:col-span-2 space-y-5">
          {/* Breakdown */}
          <div>
            <h2 className="font-display text-lg font-bold text-white mb-4">
              Desglose del análisis
            </h2>
            <div className="space-y-3">
              {Object.entries(result.breakdown || {}).map(([key, item], i) => (
                <BreakdownCard key={key} item={item} delay={i * 0.06} />
              ))}
            </div>
          </div>

          {/* Heatmap */}
          {result.heatmap && result.heatmap.data?.length > 0 && (
            <HeatmapViewer heatmap={result.heatmap} filename={result.filename} />
          )}

          {/* Comparison */}
          {result.comparison && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-5"
            >
              <h3 className="font-semibold text-white mb-3">Comparación con original</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                {[
                  { label: 'Similitud', value: `${result.comparison.similarity_pct}%` },
                  { label: 'Zona modificada', value: `${result.comparison.modified_area_pct}%` },
                  { label: 'Veredicto', value: result.comparison.verdict },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-dark-surface rounded-xl p-3">
                    <div className="text-white font-bold text-sm">{value}</div>
                    <div className="text-gray-500 text-xs mt-1">{label}</div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Recommendations */}
          {result.recommendations?.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="card p-5"
            >
              <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                <Shield size={16} className="text-blue-400" />
                Recomendaciones
              </h3>
              <ul className="space-y-2">
                {result.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-gray-400">
                    <span className="text-blue-400 mt-0.5 flex-shrink-0">▸</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Metadata */}
          {result.metadata && Object.keys(result.metadata).length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
              className="card p-5"
            >
              <h3 className="font-semibold text-white mb-3 text-sm">Metadata del archivo</h3>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(result.metadata)
                  .filter(([, v]) => v !== null && v !== undefined && !Array.isArray(v))
                  .map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs bg-dark-surface px-3 py-2 rounded-lg">
                      <span className="text-gray-500 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="text-gray-300 font-mono truncate ml-2 max-w-[100px] text-right">
                        {String(v)}
                      </span>
                    </div>
                  ))}
              </div>
              {result.metadata.suspicious_flags?.length > 0 && (
                <div className="mt-3 space-y-1">
                  {result.metadata.suspicious_flags.map((flag, i) => (
                    <div key={i} className="text-xs text-yellow-400 bg-yellow-400/10
                                            border border-yellow-400/20 px-3 py-2 rounded-lg flex items-center gap-2">
                      <AlertTriangle size={11} />
                      {flag}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Disclaimer */}
          <div className="text-xs text-gray-600 leading-relaxed p-4 border border-dark-border
                           rounded-xl bg-dark-surface/50">
            <strong className="text-gray-500">⚠️ Disclaimer:</strong> Este análisis es orientativo.
            VerifAI utiliza múltiples técnicas para maximizar la precisión, pero ningún sistema
            garantiza 100% de exactitud. Usa este reporte como herramienta auxiliar y complementa
            con verificación manual experta antes de tomar decisiones importantes.
          </div>
        </div>
      </div>
    </div>
  );
}
