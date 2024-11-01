/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        chalk: ['Cabin Sketch', 'cursive'],     // チョーク風フォント
        handwriting: ['Klee One', 'cursive'],   // 手書き風フォント
      },
      colors: {
        'chalkboard': {
          DEFAULT: '#2A4734',  // 黒板のベース色
          dark: '#1C3427',     // 黒板の影色
          light: '#375842',    // 黒板のハイライト色
        },
        'wood': {
          DEFAULT: '#C19A6B',  // 木目のベース色
          dark: '#A37747',     // 木目の影色
          light: '#DEB887',    // 木目のハイライト色
        },
        'paper': {
          DEFAULT: '#FFF9E5',  // ノートのベース色
          lines: '#E8E0CC',    // ノートの罫線色
        }
      },
      backgroundImage: {
        'chalk-texture': "url('/chalk-texture.png')",  // チョークのテクスチャ
      }
    },
  },
  plugins: [],
}