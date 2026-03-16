import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import Footer from './components/Footer.jsx';

const HomePage    = lazy(() => import('./pages/HomePage.jsx'));
const ResultPage  = lazy(() => import('./pages/ResultPage.jsx'));
const AboutPage   = lazy(() => import('./pages/AboutPage.jsx'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage.jsx'));
const NotFound    = lazy(() => import('./pages/NotFound.jsx'));

const Loader = () => (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="flex flex-col items-center gap-4">
      <div className="w-10 h-10 border-2 border-blue-700/30 border-t-blue-500 rounded-full animate-spin" />
      <span className="text-gray-500 text-sm font-mono">Cargando...</span>
    </div>
  </div>
);

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Suspense fallback={<Loader />}>
          <Routes>
            <Route path="/"           element={<HomePage />} />
            <Route path="/result/:id" element={<ResultPage />} />
            <Route path="/about"      element={<AboutPage />} />
            <Route path="/privacy"    element={<PrivacyPage />} />
            <Route path="*"           element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
