module.exports = {
  content: [
    "./src/**/*.{html,js}",
    "./*.{html,js}"
  ],
  theme: {
    extend: {
      colors: {
        neonBlue: "#4D7CFE",
        neonPurple: "#B55CFF",
        darkBg: "#0C0F19",
        cardBg: "#141824"
      },
      boxShadow: {
        neon: "0 0 25px rgba(93, 143, 255, 0.6)",
        neonPurple: "0 0 25px rgba(181, 92, 255, 0.6)"
      }
    }
  },
  plugins: []
};