/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        body: ['"DM Sans"', 'sans-serif'],
        mono: ['"DM Mono"', 'monospace'],
      },
      colors: {
        ink: { DEFAULT: '#1a1a2e', soft: '#4a4a6a' },
        surface: { DEFAULT: '#f7f7fb', 2: '#eeeef7' },
        brand: {
          blue: '#1565FF',
          'blue-soft': '#D6E4FF',
          violet: '#7b2ff7',
          teal: '#06b6d4',
          rose: '#f43f5e',
          amber: '#f59e0b',
          green: '#10b981',
          yellow: '#FFE135',
        },
      },
      boxShadow: {
        card: '0 2px 12px rgba(67,97,238,.10)',
        'card-hover': '0 8px 28px rgba(67,97,238,.18)',
      },
      borderRadius: { xl: '14px' },
    },
  },
  plugins: [],
}
