/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'media',
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
        },
        // Anysphere dark theme colors
        'anysphere': {
          DEFAULT: '#181818',  // Main background
          light: '#292929',    // Slightly lighter background (caret row color)
          dark: '#0F0F0F',     // Darker variant
          text: '#D6D6DD',     // Primary text color
          accent: '#3bafab',   // Teal accent color
          purple: '#E394DC',   // Purple accent color
          blue: '#1524de',     // Blue accent color
          selection: '#163761' // Selection background
        }
      }
    },
  },
  plugins: [],
} 