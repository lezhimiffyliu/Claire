/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['DIN Round Pro', 'Nunito', 'system-ui', 'sans-serif'],
      },
      colors: {
        duo: {
          green: '#58cc02',
          'green-dark': '#46a302',
          'green-border': '#2d6930',
          gray: '#e5e5e5',
          'gray-dark': '#afafaf',
        },
      },
    },
  },
  plugins: [],
}
