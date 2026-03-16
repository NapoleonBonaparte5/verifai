/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg:      '#0D1117',
          card:    '#161B22',
          border:  '#21262D',
          surface: '#1C2128',
          hover:   '#262C36',
        },
        brand: {
          blue:   '#1565C0',
          light:  '#1E88E5',
          glow:   'rgba(21, 101, 192, 0.3)',
        },
        status: {
          authentic: '#2E7D32',
          fake:      '#C62828',
          warning:   '#F57F17',
          unknown:   '#4527A0',
        },
      },
      fontFamily: {
        sans:    ['"Inter"', 'system-ui', 'sans-serif'],
        display: ['"Syne"', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'scan':       'scan 2s linear infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'glow':       'glow 2s ease-in-out infinite alternate',
        'float':      'float 6s ease-in-out infinite',
      },
      keyframes: {
        scan: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(400%)' },
        },
        glow: {
          '0%':   { boxShadow: '0 0 5px rgba(21,101,192,0.3)' },
          '100%': { boxShadow: '0 0 25px rgba(21,101,192,0.7)' },
        },
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%':     { transform: 'translateY(-8px)' },
        },
      },
    },
  },
  plugins: [],
};
