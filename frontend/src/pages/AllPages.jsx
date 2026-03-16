// HowItWorks.jsx
import React from 'react';
import { motion } from 'framer-motion';
import { Eye, Zap, Shield, Music, Video, FileSearch, AlertTriangle } from 'lucide-react';

export function HowItWorks() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-4xl font-bold text-white mb-4">Cómo funciona VerifAI</h1>
        <p className="text-gray-400 text-lg mb-12 leading-relaxed">
          VerifAI aplica un conjunto de técnicas forenses digitales para analizar la autenticidad
          de imágenes, videos y audios. Cada análisis combina múltiples métodos para dar un resultado
          más fiable.
        </p>

        {/* Steps */}
        <div className="space-y-6 mb-16">
          {[
            { step: '01', title: 'Sube tu archivo', desc: 'Arrastra o selecciona el archivo que quieres analizar. Soportamos imágenes (JPG, PNG, WEBP), videos (MP4, AVI, MOV) y audio (MP3, WAV, FLAC) hasta 200MB.' },
            { step: '02', title: 'Análisis multicapa', desc: 'Nuestros algoritmos aplican simultáneamente varias técnicas: ELA, análisis de ruido, metadatos EXIF, frecuencias FFT y modelos de IA de Hugging Face.' },
            { step: '03', title: 'Resultado detallado', desc: 'Recibes un score de autenticidad del 0 al 100% con el desglose de cada técnica, las anomalías detectadas y recomendaciones de acción.' },
            { step: '04', title: 'Archivo eliminado', desc: 'Tu archivo se elimina automáticamente de nuestros servidores a los 30 minutos. No guardamos ningún dato personal.' },
          ].map(({ step, title, desc }) => (
            <div key={step} className="card p-6 flex gap-5">
              <div className="font-mono text-3xl font-bold text-brand/30 flex-shrink-0 w-12">{step}</div>
              <div>
                <h3 className="font-display font-semibold text-white mb-2">{title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Techniques */}
        <h2 className="font-display text-2xl font-bold text-white mb-6">Técnicas de análisis</h2>
        <div className="grid md:grid-cols-2 gap-5 mb-12">
          {[
            {
              icon: Eye,
              title: 'Error Level Analysis (ELA)',
              color: 'text-brand',
              bg: 'bg-brand/10',
              border: 'border-brand/20',
              desc: 'Recomprime la imagen y calcula la diferencia con el original. Las zonas editadas tienen niveles de error diferentes al resto, revelando manipulaciones.',
            },
            {
              icon: Zap,
              title: 'Análisis de Patrones de Ruido',
              color: 'text-purple-400',
              bg: 'bg-purple-400/10',
              border: 'border-purple-400/20',
              desc: 'Las imágenes generadas por IA tienen ruido sintético extremadamente uniforme. Las fotografías reales presentan variaciones naturales e irregulares.',
            },
            {
              icon: FileSearch,
              title: 'Metadatos EXIF',
              color: 'text-blue-400',
              bg: 'bg-blue-400/10',
              border: 'border-blue-400/20',
              desc: 'Analiza los metadatos embebidos en la imagen para detectar inconsistencias, ausencia de datos de cámara o rastros de herramientas de IA como Stable Diffusion.',
            },
            {
              icon: Zap,
              title: 'Análisis de Frecuencias (FFT)',
              color: 'text-orange-400',
              bg: 'bg-orange-400/10',
              border: 'border-orange-400/20',
              desc: 'Transforma la imagen al dominio de frecuencias. Las imágenes AI presentan dominancia artificial en frecuencias bajas con distribución atípica.',
            },
            {
              icon: Music,
              title: 'Análisis Espectral de Audio',
              color: 'text-green-400',
              bg: 'bg-green-400/10',
              border: 'border-green-400/20',
              desc: 'Examina el espectrograma del audio buscando silencios perfectos, variación de amplitud anormal y ausencia de ruido de fondo natural, características del TTS.',
            },
            {
              icon: Shield,
              title: 'Modelos IA (Hugging Face)',
              color: 'text-red-400',
              bg: 'bg-red-400/10',
              border: 'border-red-400/20',
              desc: 'Consulta modelos pre-entrenados especializados en detección de imágenes generadas por IA, entrenados con millones de ejemplos reales y sintéticos.',
            },
          ].map(({ icon: Icon, title, color, bg, border, desc }) => (
            <div key={title} className="card p-5">
              <div className={`w-10 h-10 rounded-xl ${bg} ${border} border flex items-center justify-center mb-3`}>
                <Icon size={18} className={color} />
              </div>
              <h3 className="font-semibold text-white text-sm mb-2">{title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* Disclaimer */}
        <div className="p-5 bg-warning/5 border border-warning/20 rounded-xl flex gap-3">
          <AlertTriangle size={18} className="text-warning flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-warning font-semibold text-sm mb-1">Limitaciones importantes</p>
            <p className="text-gray-400 text-sm leading-relaxed">
              VerifAI es una herramienta auxiliar de apoyo. Ningún sistema de detección de deepfakes
              garantiza el 100% de precisión. Los deepfakes más sofisticados pueden evadir la detección.
              Siempre contrasta los resultados con otras fuentes y usa el sentido crítico.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-4xl font-bold text-white mb-2">Política de Privacidad</h1>
        <p className="text-gray-500 text-sm mb-10">Última actualización: marzo 2026</p>
        {[
          { title: '1. Datos que recopilamos', text: 'VerifAI no recopila datos personales identificables. No pedimos nombre, email ni ningún dato de usuario. Los únicos datos procesados son los archivos que subes voluntariamente para su análisis.' },
          { title: '2. Archivos subidos', text: 'Los archivos que subes se almacenan temporalmente en nuestros servidores durante un máximo de 30 minutos y se eliminan automáticamente. No leemos, vendemos ni compartimos el contenido de tus archivos.' },
          { title: '3. Cookies y analytics', text: 'Usamos Google Analytics con IP anonimizada para entender el uso del servicio de forma agregada. No usamos cookies de marketing ni seguimiento individual.' },
          { title: '4. Anuncios (Google AdSense)', text: 'Mostramos anuncios de Google AdSense para financiar el servicio gratuito. Google puede usar cookies propias. Puedes gestionar preferencias en adssettings.google.com.' },
          { title: '5. Seguridad', text: 'Todas las comunicaciones van cifradas con HTTPS/TLS. Los archivos se almacenan en servidores seguros y se borran definitivamente tras el análisis.' },
          { title: '6. Cumplimiento GDPR', text: 'Cumplimos con el RGPD de la Unión Europea. Al no recopilar datos personales, no hay datos que solicitar ni borrar. Contacto: hola@verifai.app' },
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

export function TermsPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-4xl font-bold text-white mb-2">Términos de Uso</h1>
        <p className="text-gray-500 text-sm mb-10">Última actualización: marzo 2026</p>
        {[
          { title: '1. Uso del servicio', text: 'VerifAI es una herramienta de análisis de autenticidad de medios digitales. Al usarla, aceptas estos términos. El servicio se ofrece "tal cual", sin garantías de disponibilidad.' },
          { title: '2. Limitación de precisión', text: 'VerifAI es una herramienta auxiliar. No garantizamos una precisión del 100%. Los resultados son orientativos y deben contrastarse con otras fuentes. No nos hacemos responsables de decisiones tomadas basándose únicamente en estos análisis.' },
          { title: '3. Uso aceptable', text: 'Está prohibido usar VerifAI para procesar archivos con contenido ilegal, o para cualquier actividad que viole leyes aplicables. El servicio es para uso legítimo de verificación y detección de desinformación.' },
          { title: '4. Propiedad intelectual', text: 'Los usuarios son responsables de tener los derechos necesarios sobre los archivos que analizan. VerifAI no reclama ningún derecho sobre los archivos procesados.' },
          { title: '5. Limitación de responsabilidad', text: 'VerifAI no se responsabiliza por errores en el análisis ni por decisiones tomadas basándose en los resultados. Usa la herramienta con sentido crítico.' },
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

export function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="font-display text-8xl font-bold text-brand/10 mb-4">404</div>
      <h1 className="font-display text-2xl font-bold text-white mb-3">Página no encontrada</h1>
      <p className="text-gray-500 mb-8">La página que buscas no existe.</p>
      <a href="/" className="btn-brand">Volver al análisis</a>
    </div>
  );
}
