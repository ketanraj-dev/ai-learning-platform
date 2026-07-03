/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#07090F",
          900: "#0F1623",
          800: "#162235",
          700: "#1C2B40",
          600: "#2A3D57",
        },
        brand: {
          600: "#C16A1E",
          500: "#E8843C",
          400: "#EFA460",
          300: "#F5C28E",
        },
        link: {
          500: "#5B8AF0",
          400: "#7BA4F5",
          300: "#A3C0FA",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        sans:    ["Inter", "sans-serif"],
        mono:    ["JetBrains Mono", "monospace"],
      },
      animation: {
        "fade-in":    "fadeIn .35s ease forwards",
        "slide-up":   "slideUp .4s ease forwards",
        "pulse-slow": "pulse 3s cubic-bezier(.4,0,.6,1) infinite",
        "glow":       "glow 5s ease-in-out infinite",
      },
      keyframes: {
        fadeIn:  { from: { opacity: "0" },                                      to: { opacity: "1" } },
        slideUp: { from: { opacity: "0", transform: "translateY(16px)" },       to: { opacity: "1", transform: "translateY(0)" } },
        glow:    { "0%, 100%": { opacity: "0.3" }, "50%": { opacity: "0.7" } },
      },
    },
  },
  plugins: [],
};
