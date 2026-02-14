FROM node:20

WORKDIR /app

# Копируем файлы зависимостей
COPY package.json package-lock.json* ./

# Использование --legacy-peer-deps критично для React 19
RUN npm install --legacy-peer-deps

# Копируем остальной код
COPY . .

# Очищаем кэш Next.js, если он попал в билд-контекст
RUN rm -rf .next

EXPOSE 3000

CMD ["npm", "run", "dev"]