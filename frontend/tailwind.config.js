/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'coral': {
          DEFAULT: '#FF6F61',
          light: '#FF8C82',
          dark: '#E55A4D'
        },
        'forest': {
          DEFAULT: '#2C5530',
          light: '#3D7042',
          dark: '#1B3B1E'
        },
        'cream': {
          DEFAULT: '#FFF8F0',
          light: '#FFFAF5',
          dark: '#F5EEE6'
        }
      }
    },
  },
  plugins: [],
} 