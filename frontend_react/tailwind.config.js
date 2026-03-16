/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          900: '#0a0a0c',
          800: '#141418',
          700: '#1c1c24',
          neon: '#00ff9f',
          red: '#ff003c',
        }
      }
    },
  },
  plugins: [],
}
