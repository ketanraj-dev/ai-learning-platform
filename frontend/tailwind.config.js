/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#020817",
          900: "#0F172A",
          800: "#1E293B",
          700: "#334155",
          600: "#475569",
        },
        brand: {
          500: "#3B82F6",
          400: "#60A5FA",
          300: "#93C5FD",
        },
        success: "#22C55E",
        warning: "#F59E0B",
        danger:  "#EF4444",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        "fade-in":    "fadeIn .35s ease forwards",
        "slide-up":   "slideUp .4s ease forwards",
        "pulse-slow": "pulse 3s cubic-bezier(.4,0,.6,1) infinite",
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: "translateY(16px)" }, to: { opacity: 1, transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};