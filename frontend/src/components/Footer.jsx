import React from 'react';
import { Link } from 'react-router-dom';
import { Scan, Shield, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-dark-border bg-dark-card/30 mt-16">
      <div className="max-w-6xl mx-auto px-4 py-10">
        <div className="grid md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-blue-700/20 border border-blue-700/30 flex items-center justify-center">
                <Scan size={14} className="text-blue-400" />
              </div>
              <span className="font-display font-bold text-white">
                Verif<span className="text-blue-400">AI</span>
              </span>
            </div>
            <p className="text-gray-500 text-sm leading-relaxed">
              Detector gratuito de deepfakes e imágenes generadas por IA.
              Sin registro. Privacidad garantizada.
            </p>
            <div className="flex items-center gap-2 mt-3 text-xs text-gray-600">
              <Shield size={12} className="text-green-500" />
              Archivos eliminados en 30 minutos
            </div>
          </div>

          <div>
            <h4 className="text-white font-medium text-sm mb-3">Páginas</h4>
            <ul className="space-y-2">
              {[
                { to: '/',        label: 'Analizar archivo' },
                { to: '/about',   label: 'Cómo funciona' },
                { to: '/privacy', label: 'Política de privacidad' },
              ].map(({ to, label }) => (
                <li key={to}>
                  <Link to={to} className="text-gray-500 hover:text-white text-sm transition-colors">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-white font-medium text-sm mb-3">Detectamos</h4>
            <ul className="space-y-1.5">
              {['Deepfakes en video', 'Imágenes AI generadas', 'Voz sintética', 'Manipulación fotográfica', 'Firmas de DALL-E, Midjourney, SD'].map(item => (
                <li key={item} className="text-gray-500 text-sm flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-blue-500 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-dark-border pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-gray-600 text-xs">
            © {new Date().getFullYear()} VerifAI. Todos los derechos reservados.
          </p>
          <p className="text-gray-700 text-xs">
            ⚠️ Herramienta auxiliar — no garantiza 100% de precisión
          </p>
          <p className="text-gray-600 text-xs flex items-center gap-1">
            Hecho con <Heart size={10} className="text-red-500" /> por la comunidad
          </p>
        </div>
      </div>
    </footer>
  );
}
