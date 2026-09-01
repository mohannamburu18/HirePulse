/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fdf4ff',
          100: '#fae8ff',
          200: '#f5d0fe',
          300: '#f0abfc',
          400: '#e879f9',
          500: '#d946ef',
          600: '#c026d3',
          700: '#a21caf',
          800: '#86198f',
          900: '#701a75',
          950: '#4a044e',
        },
        dark: {
          bg: '#090a10',
          surface: '#11131f',
          card: '#16192b',
          border: 'rgba(255, 255, 255, 0.08)',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'radial-gradient(circle at 50% 0%, rgba(192, 38, 211, 0.18) 0%, rgba(147, 51, 234, 0.12) 35%, transparent 70%)',
        'purple-pink-gradient': 'linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #f43f5e 100%)',
      },
      boxShadow: {
        'glow-sm': '0 0 20px -5px rgba(217, 70, 239, 0.3)',
        'glow-md': '0 0 35px -5px rgba(217, 70, 239, 0.4)',
        'glow-lg': '0 0 60px -10px rgba(168, 85, 247, 0.5)',
      },
      animation: {
        'pulse-subtle': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        }
      }
    },
  },
  plugins: [],
}

