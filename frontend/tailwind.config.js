/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: '#F9F9F7',
        ink: '#111111',
        mutedDivider: '#E5E5E0',
        editorialRed: '#CC0000',
        neutral: {
          100: '#F5F5F5',
          200: '#E5E5E5',
          400: '#A3A3A3',
          500: '#737373',
          600: '#525252',
          700: '#404040',
        }
      },
      fontFamily: {
        serif: ["'Playfair Display'", 'Georgia', 'serif'],
        body: ["'Lora'", 'Georgia', 'serif'],
        sans: ["'Inter'", '-apple-system', 'sans-serif'],
        mono: ["'JetBrains Mono'", 'Courier New', 'monospace'],
      },
      boxShadow: {
        'hard': '4px 4px 0px 0px #111111',
        'hard-sm': '2px 2px 0px 0px #111111',
        'hard-lg': '8px 8px 0px 0px #111111',
      }
    },
  },
  plugins: [],
}
