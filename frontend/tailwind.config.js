/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#101918",
          surface: "#182321",
          elevated: "#202D2A",
          border: "#354540",
          selected: "#203D37",
          text: "#F3F7F4",
          muted: "#B6C6C1",
          teal: "#5EEAD4",
          accent: "#2DD4BF",
        },
        teal: {
          DEFAULT: "#0F766E",
          50: "#F0F9F7",
          100: "#E8F3F0",
          200: "#CDE7E2",
          300: "#99CFCC",
          400: "#5EB1AD",
          500: "#2A918C",
          600: "#137D76",
          700: "#0F766E",
          800: "#115E59",
          900: "#134E4A",
          950: "#042F2E",
        },
        ivory: {
          DEFAULT: "#FAF8F3",
          50: "#FCFAF6",
          100: "#FAF8F3",
          200: "#F3EFE6",
          300: "#EAE3D5",
        },
        ink: {
          DEFAULT: "#18312F",
          muted: "#526461",
          subtle: "#7E908D",
          border: "#E4E8E3",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          ivory: "#FAF8F3",
          teal: "#E8F3F0",
          border: "#E4E8E3",
        },
        status: {
          success: "#237A57",
          'success-bg': "#EEF7F2",
          'success-border': "#CCE3D7",
          warning: "#946200",
          'warning-bg': "#FEF8EC",
          'warning-border': "#F7E6BE",
          error: "#B42318",
          'error-bg': "#FDF2F1",
          'error-border': "#F9D1CE",
        },
        brand: {
          50: "#F0F9F7",
          100: "#E8F3F0",
          500: "#0F766E",
          600: "#115E59",
          700: "#134E4A",
        }
      },
      boxShadow: {
        'xs': '0 1px 2px 0 rgb(24 49 47 / 0.04)',
        '2xs': '0 1px 1px 0 rgb(24 49 47 / 0.03)',
        'soft': '0 2px 8px 0 rgb(24 49 47 / 0.05)',
        'card': '0 4px 16px -2px rgb(24 49 47 / 0.06)',
      },
      backdropBlur: {
        'xs': '2px',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.25s ease-out forwards',
      },
    },
  },
  plugins: [],
}
