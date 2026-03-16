import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Menu, X, Scan } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Navbar() {
  const [scrolled, setScrolled]     = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { pathname }                 = useLocation();

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', fn);
    return () => window.removeEventListener('scroll', fn);
  }, []);
  useEffect(() => setMobileOpen(false), [pathname]);

  const links = [
    { href: '/',        label: 'Analizar' },
    { href: '/about',   label: 'Cómo funciona' },
    { href: '/privacy', label: 'Privacidad' },
  ];

  return (
    <header className={`sticky top-0 z-50 transition-all duration-300 ${
      scrolled ? 'border-b border-dark-border bg-dark-bg/90 backdrop-blur-md' : 'bg-transparent'
    }`}>
      <nav className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="relative w-8 h-8 rounded-lg bg-blue-700/20 border border-blue-700/30
                          flex items-center justify-center
                          group-hover:bg-blue-700/30 group-hover:border-blue-700/50 transition-all">
            <Scan size={16} className="text-blue-400" />
          </div>
          <span className="font-display font-bold text-white text-lg tracking-tight">
            Verif<span className="text-blue-400">AI</span>
          </span>
          <span className="hidden sm:block text-xs font-mono text-gray-600 border border-dark-border
                           px-1.5 py-0.5 rounded">
            BETA
          </span>
        </Link>

        {/* Desktop */}
        <div className="hidden md:flex items-center gap-1">
          {links.map(({ href, label }) => (
            <Link key={href} to={href}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150
                ${pathname === href
                  ? 'text-blue-400 bg-blue-700/10'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}>
              {label}
            </Link>
          ))}
        </div>

        {/* Mobile button */}
        <button
          className="md:hidden p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all"
          onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </nav>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="md:hidden border-b border-dark-border bg-dark-bg/95 backdrop-blur-md">
            <div className="max-w-6xl mx-auto px-4 py-3 flex flex-col gap-1">
              {links.map(({ href, label }) => (
                <Link key={href} to={href}
                  className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all
                    ${pathname === href ? 'text-blue-400 bg-blue-700/10' : 'text-gray-300 hover:bg-white/5'}`}>
                  {label}
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
