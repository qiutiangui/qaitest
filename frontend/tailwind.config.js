/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#409EFF',
          light: '#66B1FF',
          lighter: '#79BBFF',
        },
        background: {
          DEFAULT: '#FFFFFF',
          secondary: '#F5F7FA',
          dark: '#001529',
        },
        text: {
          primary: '#303133',
          secondary: '#606266',
          placeholder: '#909399',
        },
        functional: {
          success: '#67C23A',
          danger: '#F56C6C',
          warning: '#E6A23C',
          info: '#409EFF',
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
