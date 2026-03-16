// ─── About Page ─────────────────────────────────────────────────
import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Zap, Lock, Eye, Brain, AlertTriangle } from 'lucide-react';

export function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-4xl font-bold text-white mb-4">Cómo funciona VerifAI</h1>
        <p className="text-gray-400 text-lg leading-relaxed mb-10">
          VerifAI combina múltiples técnicas de análisis forense digital con modelos de inteligencia
          artificial para detectar deepfakes, imágenes generadas por IA y audio sintético.
        </p>

        <div className="space-y-6 mb-12">
          {[
            {
              icon: Eye, title: 'Error Level Analysis (ELA)',
              text: 'Cuando una imagen es manipulada o generada por IA, diferentes regiones tienen niveles de compresión distintos. ELA detecta estas inconsistencias con alta precisión.',
              color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/20',
            },
            {
              icon: Zap, title: 'Análisis de Frecuencias (FFT)',
              text: 'La Transformada Rápida de Fourier analiza el espectro de frecuencias de la imagen. Las imágenes generadas por IA muestran patrones regulares anómalos en este espectro.',
              color: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/20',
            },
            {
              icon: Brain, title: 'Modelos de Hugging Face',
              text: 'Integramos clasificadores neuronales (ViT) entrenados en el dataset DFDC (DeepFake Detection Challenge) con millones de ejemplos reales y falsos.',
              color: 'text-green-400', bg: 'bg-green-400/10', border: 'border-green-400/20',
            },
            {
              icon: Shield, title: 'Análisis de Ruido Estadístico',
              text: 'Las imágenes reales tienen patrones de ruido naturales e irregulares. Las imágenes generadas por IA tienen ruido artificialmente uniforme que podemos detectar.',
              color: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/20',
            },
            {
              icon: AlertTriangle, title: 'Firmas de Herramientas AI',
              text: 'Cada herramienta generativa (DALL-E, Midjourney, Stable Diffusion) deja firmas características: dimensiones específicas, texturas perfectas, patrones de suavizado.',
              color: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-400/20',
            },
            {
              icon: Lock, title: 'Metadata EXIF',
              text: 'Analizamos la metadata del archivo en busca de software de edición, inconsistencias de fecha, ausencia de datos de cámara y otras señales de manipulación.',
              color: 'text-cyan-400', bg: 'bg-cyan-400/10', border: 'border-cyan-400/20',
            },
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                className="card p-6 flex gap-5"
              >
                <div className={`w-11 h-11 rounded-xl ${item.bg} ${item.border} border flex items-center justify-center flex-shrink-0`}>
                  <Icon size={20} className={item.color} />
                </div>
                <div>
                  <h3 className="font-semibold text-white mb-1">{item.title}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">{item.text}</p>
                </div>
              </motion.div>
            );
          })}
        </div>

        <div className="card p-6 border-yellow-400/20 bg-yellow-400/5">
          <h3 className="font-semibold text-yellow-400 mb-2 flex items-center gap-2">
            <AlertTriangle size={16} />
            Limitaciones importantes
          </h3>
          <p className="text-gray-400 text-sm leading-relaxed">
            Ningún sistema de detección garantiza 100% de precisión. VerifAI es una herramienta
            auxiliar que combina múltiples señales para dar una estimación estadística. Siempre
            complementa el análisis con verificación manual y fuentes primarias. Los deepfakes
            más sofisticados pueden evadir la detección automática.
          </p>
        </div>
      </motion.div>
    </div>
  );
}

// ─── Privacy Page ─────────────────────────────────────────────
export function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-4xl font-bold text-white mb-2">Política de Privacidad</h1>
        <p className="text-gray-500 text-sm mb-10">Última actualización: marzo 2026</p>

        {[
          { title: '1. Archivos subidos',
            text: 'Los archivos que subes se procesan en memoria y se guardan temporalmente en servidores seguros únicamente para realizar el análisis. Se eliminan automáticamente en un máximo de 30 minutos. No los leemos, analizamos con fines ajenos al servicio, ni los compartimos con terceros.' },
          { title: '2. Datos personales',
            text: 'VerifAI no recopila datos personales identificables. No pedimos nombre, email ni ningún dato de usuario. El servicio es completamente anónimo.' },
          { title: '3. Analytics',
            text: 'Usamos Google Analytics con IP anonimizada para entender el uso del servicio de forma agregada y anónima. No usamos cookies de marketing.' },
          { title: '4. Anuncios',
            text: 'Mostramos anuncios de Google AdSense para financiar el servicio gratuito. Google puede usar cookies propias para personalización de anuncios.' },
          { title: '5. Seguridad',
            text: 'Todas las comunicaciones van cifradas con HTTPS/TLS. Los archivos se almacenan en ubicaciones temporales con acceso restringido.' },
          { title: '6. GDPR',
            text: 'Cumplimos con el RGPD. Dado que no recopilamos datos personales, no hay datos que solicitar ni borrar. Contacto: privacy@verifai.app' },
        ].map(s => (
          <div key={s.title} className="mb-8">
            <h2 className="font-display text-lg font-semibold text-white mb-3">{s.title}</h2>
            <p className="text-gray-400 text-sm leading-relaxed">{s.text}</p>
          </div>
        ))}
      </motion.div>
    </div>
  );
}

// ─── Not Found ────────────────────────────────────────────────
export function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="text-8xl font-display font-bold text-blue-700/20 mb-4">404</div>
      <h1 className="font-display text-2xl font-bold text-white mb-3">Página no encontrada</h1>
      <p className="text-gray-500 mb-8">La página que buscas no existe o fue movida.</p>
      <a href="/" className="btn-primary">Volver al inicio</a>
    </div>
  );
}

export default AboutPage;
