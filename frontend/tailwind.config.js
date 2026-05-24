/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        parchment: "#F4EFE4",
        pitch: "#1A6B3C",
        "pitch-light": "#2D8A52",
        "pitch-dark": "#0F4A28",
        ink: "#1A1A1A",
        "ink-muted": "#6B6B5F",
        accent: "#C8402A",
        gold: "#C9963A",
      },
      fontFamily: {
        display: ["Bebas Neue", "sans-serif"],
        body: ["DM Sans", "sans-serif"],
      },
    },
  },
  plugins: [],
};