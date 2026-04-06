/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["'DM Sans'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
        display: ["'Syne'", "sans-serif"],
      },
      colors: {
        bg: "#0a0a0f",
        surface: "#111118",
        border: "#1e1e2e",
        accent: "#6ee7b7",
        "accent-dim": "#34d399",
        muted: "#4a4a6a",
        "text-primary": "#e2e8f0",
        "text-secondary": "#94a3b8",
        urgent: "#f87171",
        new: "#6ee7b7",
      },
    },
  },
  plugins: [],
};
