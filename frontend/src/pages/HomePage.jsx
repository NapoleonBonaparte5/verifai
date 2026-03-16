import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, Image, Music, Video, Shield, Zap,
  Lock, Eye, AlertTriangle, ChevronDown, Scan
} from 'lucide-react';
import toast from 'react-hot-toast';

const MAX_SIZE_MB = 200;
const MAX_SIZE    = MAX_SIZE_MB * 1024 * 1024;

const MEDIA_TYPES = [
  {
    id: 'image', label: 'Imagen', icon: Image,
    color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/20',
    formats: 'JPG, PNG, WebP, GIF, BMP',
    desc: 'Detecta imágenes generadas por DALL-E, Midjourney, Stable Diffusion y manipulación fotográfica',
  },
  {
    id: 'video', label: 'Video', icon: Video,
    color: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/20',
    formats: 'MP4, AVI, MOV, MKV, WebM',
    desc: 'Análisis frame-by-frame para detectar face-swap, lip-sync falso y deepfakes de video',
  },
  {
    id: 'audio', label: 'Audio', icon: Music,
    color: 'text-green-400', bg: 'bg-green-400/10', border: 'border-green-400/20',
    formats: 'WAV, MP3, OGG, FLAC',
    desc: 'Detecta voz sintética generada por ElevenLabs, clonación de voz y audio manipulado',
  },
];

const EXAMPLES = [
  { label: 'Obama deepfake', type: 'Video', year: '2018', verdict: 'FALSO', color: 'text-red-400' },
  { label: 'CEO fraude CFO', type: 'Audio', year: '2024', verdict: 'FALSO', color: 'text-red-400' },
  { label: 'Foto papal abrigo', type: 'Imagen', year: '2023', verdict: 'FALSO', color: 'text-red-400' },
];

const FAQ = [
  { q: '¿Qué precisión tiene VerifAI?', a: 'Combinamos múltiples técnicas de análisis (ELA, FFT, análisis de ruido, modelos de HuggingFace) para maximizar la precisión. En imágenes alcanzamos >90% en benchmarks públicos. Siempre recomendamos usarlo como herramienta auxiliar.' },
  { q: '¿Mis archivos son privados?', a: 'Sí. Los archivos se procesan en memoria y se eliminan automáticamente de los servidores en 30 minutos. No los almacenamos, analizamos ni compartimos.' },
  { q: '¿Qué tipo de manipulaciones detecta?', a: 'Imágenes generadas por IA (DALL-E, Midjourney, SD), deepfakes de video (face-swap, lip-sync), voz sintética (ElevenLabs, voice cloning), edición fotográfica y manipulación de metadata.' },
  { q: '¿Cuál es el límite de tamaño?', a: `Hasta ${MAX_SIZE_MB}MB por archivo. Para videos largos, considera extraer clips cortos con las zonas sospechosas.` },
  { q: '¿Necesito registrarme?', a: 'No. VerifAI es 100% gratuito y sin registro. Solo sube el archivo y obtén el análisis al instante.' },
];

export default function HomePage() {
  const navigate              = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress]   = useState(0);
  const [openFaq, setOpenFaq]     = useState(null);

  const onDrop = useCallback(async (accepted, rejected) => {
    if (rejected.length > 0) {
      const err = rejected[0].errors[0];
      toast.error(err.code === 'file-too-large'
        ? `Archivo demasiado grande. Máximo ${MAX_SIZE_MB}MB`
        : `Archivo no aceptado: ${err.message}`
      );
      return;
    }
    const file = accepted[0];
    if (!file) return;

    setUploading(true);
    setProgress(10);

    const formData = new FormData();
    formData.append('file', file);

    try {
      setProgress(30);
      const res = await fetch('/api/analyze', { method: 'POST', body: formData });
      setProgress(80);

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || 'Error al analizar el archivo');
      }

      const data = await res.json();
      setProgress(100);
      toast.success('Análisis completado');
      navigate(`/result/${data.analysis_id}`, { state: { result: data } });
    } catch (err) {
      toast.error(err.message || 'Error al procesar el archivo');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, [navigate]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: MAX_SIZE,
    multiple: false,
    disabled: uploading,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'],
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
      'audio/*': ['.mp3', '.wav', '.ogg', '.flac', '.m4a'],
    },
  });

  return (
    <div className="relative min-h-screen">
      <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none" />

      {/* Hero */}
      <section className="relative max-w-6xl mx-auto px-4 pt-16 pb-10">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full
                          bg-blue-700/10 border border-blue-700/20 text-blue-400
                          text-xs font-medium mb-6">
            <Scan size={12} />
            <span>IA avanzada · Sin registro · Privado</span>
          </div>

          <h1 className="font-display text-4xl md:text-6xl font-bold text-white mb-5 leading-tight">
            ¿Es este contenido
            <br />
            <span className="text-blue-400">real o falso?</span>
          </h1>

          <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
            Detecta deepfakes, imágenes generadas por IA y audio sintético.
            Análisis forense avanzado en segundos. Gratis y sin registro.
          </p>
        </motion.div>

        {/* Uploader */}
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="max-w-2xl mx-auto"
        >
          <div
            {...getRootProps()}
            className={`relative border-2 border-dashed rounded-2xl p-12 text-center
              cursor-pointer transition-all duration-300 overflow-hidden
              ${isDragActive ? 'drop-active border-blue-600' : 'border-dark-border hover:border-blue-700/40 hover:bg-blue-700/2'}
              ${uploading ? 'pointer-events-none' : ''}
            `}
          >
            <input {...getInputProps()} aria-label="Subir archivo para análisis" />

            {/* Corner decorations */}
            {['top-3 left-3 border-t-2 border-l-2 rounded-tl-lg',
              'top-3 right-3 border-t-2 border-r-2 rounded-tr-lg',
              'bottom-3 left-3 border-b-2 border-l-2 rounded-bl-lg',
              'bottom-3 right-3 border-b-2 border-r-2 rounded-br-lg'].map((cls, i) => (
              <div key={i} className={`absolute w-4 h-4 ${cls} border-blue-700/30`} />
            ))}

            {/* Scanner animation when uploading */}
            {uploading && <div className="scanner-line" />}

            <AnimatePresence mode="wait">
              {uploading ? (
                <motion.div key="uploading"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="flex flex-col items-center gap-4"
                >
                  <div className="relative w-16 h-16">
                    <div className="w-16 h-16 border-2 border-blue-700/30 border-t-blue-500 rounded-full animate-spin" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Scan size={20} className="text-blue-400" />
                    </div>
                  </div>
                  <div>
                    <p className="text-white font-semibold">Analizando con IA...</p>
                    <p className="text-gray-500 text-sm mt-1">Aplicando {progress < 50 ? 'análisis de frecuencias' : 'modelos de detección'}</p>
                  </div>
                  <div className="w-48 bg-dark-surface rounded-full h-1.5 overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full"
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </motion.div>
              ) : (
                <motion.div key="idle"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                >
                  <motion.div
                    animate={isDragActive ? { scale: 1.1 } : { scale: 1 }}
                    className={`w-16 h-16 rounded-2xl mx-auto mb-5 flex items-center justify-center
                      border transition-all duration-300
                      ${isDragActive ? 'bg-blue-700/20 border-blue-600' : 'bg-dark-surface border-dark-border'}`}
                  >
                    <Upload size={26} className={isDragActive ? 'text-blue-400' : 'text-gray-500'} />
                  </motion.div>

                  <p className="text-white font-semibold text-xl mb-2">
                    {isDragActive ? 'Suelta para analizar' : 'Arrastra tu archivo aquí'}
                  </p>
                  <p className="text-gray-500 text-sm mb-5">
                    o <span className="text-blue-400 font-medium cursor-pointer hover:underline">selecciona desde tu dispositivo</span>
                  </p>

                  <div className="flex flex-wrap justify-center gap-2">
                    {['JPG', 'PNG', 'MP4', 'AVI', 'MP3', 'WAV', 'WebP', 'MOV'].map(fmt => (
                      <span key={fmt} className="text-xs font-mono text-gray-600 bg-dark-surface
                                                 border border-dark-border px-2 py-1 rounded-lg">
                        {fmt}
                      </span>
                    ))}
                  </div>

                  <p className="text-gray-700 text-xs mt-4">
                    Máximo {MAX_SIZE_MB}MB · Archivos eliminados en 30 minutos
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </section>

      {/* Stats */}
      <section className="border-y border-dark-border bg-dark-card/40">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: '6+',    label: 'Técnicas de análisis' },
              { value: '>90%',  label: 'Precisión en imágenes' },
              { value: '<15s',  label: 'Tiempo de análisis' },
              { value: '100%',  label: 'Gratuito y privado' },
            ].map((s, i) => (
              <motion.div key={s.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className="text-center"
              >
                <div className="font-display text-2xl font-bold text-blue-400 mb-0.5">{s.value}</div>
                <div className="text-xs text-gray-500">{s.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Media types */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="font-display text-2xl font-bold text-white mb-3 text-center">
          ¿Qué puedes analizar?
        </h2>
        <p className="text-gray-500 text-center text-sm mb-8">
          Análisis multimodal — imágenes, video y audio en un solo lugar
        </p>
        <div className="grid md:grid-cols-3 gap-5">
          {MEDIA_TYPES.map((type, i) => {
            const Icon = type.icon;
            return (
              <motion.div key={type.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -4 }}
                className="card p-6"
              >
                <div className={`w-11 h-11 rounded-xl ${type.bg} ${type.border} border
                                 flex items-center justify-center mb-4`}>
                  <Icon size={20} className={type.color} />
                </div>
                <h3 className="font-display font-semibold text-white mb-1">{type.label}</h3>
                <p className="text-xs font-mono text-gray-600 mb-3">{type.formats}</p>
                <p className="text-gray-500 text-sm leading-relaxed">{type.desc}</p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-4 py-8 pb-16">
        <h2 className="font-display text-2xl font-bold text-white mb-10 text-center">
          Técnicas de análisis
        </h2>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { icon: Eye,           title: 'ELA Analysis',           desc: 'Error Level Analysis detecta regiones con niveles de compresión inconsistentes tras manipulación digital.' },
            { icon: Zap,           title: 'Análisis FFT',           desc: 'Transformada rápida de Fourier identifica patrones de frecuencia típicos de imágenes generadas por IA.' },
            { icon: Shield,        title: 'Análisis de Ruido',      desc: 'Detecta inconsistencias en el ruido estadístico que revelan composición o generación artificial.' },
            { icon: Scan,          title: 'Modelo HuggingFace',     desc: 'Clasificador neuronal ViT entrenado en el dataset DFDC con millones de ejemplos de deepfakes.' },
            { icon: AlertTriangle, title: 'Firmas de IA Generativa',desc: 'Identifica texturas perfectas, dimensiones características y patrones de DALL-E, Midjourney y SD.' },
            { icon: Lock,          title: 'Metadata EXIF',          desc: 'Analiza metadata del archivo en busca de software de edición, inconsistencias de fecha y origen.' },
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <motion.div key={item.title}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.07 }}
                className="card p-5"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-700/10 border border-blue-700/20
                                   flex items-center justify-center flex-shrink-0">
                    <Icon size={16} className="text-blue-400" />
                  </div>
                  <h3 className="font-semibold text-white text-sm">{item.title}</h3>
                </div>
                <p className="text-gray-500 text-xs leading-relaxed">{item.desc}</p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Casos famosos */}
      <section className="max-w-6xl mx-auto px-4 pb-16">
        <h2 className="font-display text-2xl font-bold text-white mb-8 text-center">
          Deepfakes famosos detectados
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          {EXAMPLES.map((ex, i) => (
            <div key={i} className="card p-5 flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-red-400/10 border border-red-400/20
                               flex items-center justify-center flex-shrink-0">
                <AlertTriangle size={18} className="text-red-400" />
              </div>
              <div>
                <p className="text-white font-medium text-sm">{ex.label}</p>
                <p className="text-gray-600 text-xs">{ex.type} · {ex.year}</p>
                <p className={`text-xs font-bold font-mono mt-0.5 ${ex.color}`}>{ex.verdict}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-3xl mx-auto px-4 pb-20">
        <h2 className="font-display text-2xl font-bold text-white mb-8 text-center">
          Preguntas frecuentes
        </h2>
        <div className="space-y-3">
          {FAQ.map((item, i) => (
            <div key={i} className="card overflow-hidden">
              <button
                className="w-full flex items-center justify-between p-5 text-left hover:bg-white/2 transition-colors"
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
              >
                <span className="font-medium text-white text-sm">{item.q}</span>
                <motion.div animate={{ rotate: openFaq === i ? 180 : 0 }} transition={{ duration: 0.2 }}>
                  <ChevronDown size={16} className="text-gray-500 flex-shrink-0 ml-4" />
                </motion.div>
              </button>
              <AnimatePresence>
                {openFaq === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <p className="px-5 pb-5 text-gray-400 text-sm leading-relaxed border-t border-dark-border pt-3">
                      {item.a}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
