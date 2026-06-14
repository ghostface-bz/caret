FROM node:22-alpine

WORKDIR /app

# Install dependencies first for better layer caching.
COPY package.json package-lock.json* ./
RUN npm install

# Source is bind-mounted over this in docker-compose for live dev (./frontend:/app),
# but copy it too so `docker build` alone produces a runnable image.
COPY . .

EXPOSE 5173

CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "5173"]
