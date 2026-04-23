/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#008a8a',
          600: '#007777',
          700: '#006666',
          800: '#005555',
          900: '#004d4d',
        },
        accent: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#00d084',
          600: '#00b371',
          700: '#009960',
        },
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #008a8a 0%, #00d084 100%)',
        'gradient-light': 'linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%)',
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 138, 138, 0.1)',
        'glass-lg': '0 16px 48px rgba(0, 138, 138, 0.15)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
