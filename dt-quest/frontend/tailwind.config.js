/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dt-dark': '#0f0f1a',
        'dt-card': '#1a1a2e',
        'dt-accent': '#4f46e5',
        'dt-success': '#10b981',
        'dt-warning': '#f59e0b',
        'dt-error': '#ef4444',
      },
    },
  },
  plugins: [],
}
