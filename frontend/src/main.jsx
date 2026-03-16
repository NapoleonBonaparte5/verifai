import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#161B22',
            color: '#E6EDF3',
            border: '1px solid #21262D',
            fontFamily: '"Inter", sans-serif',
            fontSize: '13px',
          },
          success: { iconTheme: { primary: '#2E7D32', secondary: '#161B22' } },
          error:   { iconTheme: { primary: '#C62828', secondary: '#161B22' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
);
