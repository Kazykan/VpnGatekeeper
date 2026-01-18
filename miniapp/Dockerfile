# Базовый образ
FROM node:20


# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости отдельно — это ускоряет сборку
COPY package.json package-lock.json ./

RUN npm install

# Копируем остальной код
COPY . .

# Открываем порт
EXPOSE 3000

# Запуск dev-сервера
CMD ["npm", "run", "dev"]
