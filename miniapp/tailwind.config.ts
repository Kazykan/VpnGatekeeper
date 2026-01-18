import type { Config } from "tailwindcss"
// Импортируем плагин напрямую

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    // Важно: добавьте путь к компонентам konsta, чтобы Tailwind видел их классы
    "./node_modules/konsta/react/**/*.js",
  ],
  darkMode: "class", // Позволяет включать темную тему через class="dark"
  theme: {
    extend: {},
  },
  // Добавляем плагин сюда
}

export default config
