/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        clinical: {
          50:  "#f0effe",
          100: "#dddcfb",
          200: "#c0bef8",
          300: "#9896f2",
          400: "#6d6ae9",
          500: "#4946d4",
          600: "#3430b8",
          700: "#231f98",
          800: "#130f72",
          900: "#080345",
        },
        teal: {
          50:  "#f0fdfa",
          100: "#ccfbf1",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
        },
        violet: {
          50:  "#f5f3ff",
          100: "#ede9fe",
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
        },
        safe: {
          50:  "#f0fdf4",
          100: "#dcfce7",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
        },
        warning: {
          50:  "#fffbeb",
          100: "#fef3c7",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
        },
        danger: {
          50:  "#fef2f2",
          100: "#fee2e2",
          400: "#f87171",
          500: "#ef4444",
          600: "#dc2626",
          700: "#b91c1c",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        "card":       "0 1px 3px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.07)",
        "card-hover": "0 4px 8px rgba(0,0,0,0.08), 0 12px 32px rgba(0,0,0,0.10)",
        "glow-blue":  "0 0 24px rgba(59,130,246,0.25)",
        "glow-teal":  "0 0 24px rgba(20,184,166,0.25)",
      },
      animation: {
        "fade-up":    "fadeUp 0.35s ease-out",
        "shimmer":    "shimmer 2s infinite",
      },
      keyframes: {
        fadeUp: {
          "0%":   { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
      },
    },
  },
  plugins: [],
};
