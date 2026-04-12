/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: "#080B1A",
        surface: "#111827",
        "surface-2": "#1C2333",
        border: "#1F2937",
        primary: "#22C55E",
        "primary-dim": "#166534",
        accent: "#6366F1",
        warn: "#F97316",
        danger: "#EF4444",
        muted: "#9CA3AF",
      },
      fontFamily: {
        sans: ["var(--font-heebo)", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-in-out",
        "scale-in": "scaleIn 0.3s ease-out",
      },
      keyframes: {
        fadeIn: { from: { opacity: 0, transform: "translateY(8px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        scaleIn: { from: { transform: "scale(0.95)", opacity: 0 }, to: { transform: "scale(1)", opacity: 1 } },
      },
    },
  },
  plugins: [],
}
