import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        theme: {
          bg: "var(--bg-primary)",
          secondary: "var(--bg-secondary)",
          surface: "var(--bg-surface)",
          text: "var(--text-primary)",
          textMuted: "var(--text-secondary)",
          border: "var(--border-color)",
          borderSubtle: "var(--border-subtle)",
          sage: "var(--accent-sage)",
          sageDark: "var(--accent-sage-dark)",
          sageLight: "var(--accent-sage-light)",
        },
        brand: {
          charcoal: "#111820",
          charcoalLight: "#1A2533",
          green: "#10A86B",
          greenDark: "#0D8554",
          greenLight: "#E8F8F1",
          greenBorder: "#A3E6CD",
          muted: "#64748B",
        },
      },
    },
  },
  plugins: [],
};
export default config;
