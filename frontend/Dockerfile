# Dev-mode image (ADR-0017): the working tree is bind-mounted over /app at
# runtime (see docker-compose.yml), with node_modules kept in its own
# anonymous volume so the mount doesn't shadow what's installed here.
# Source changes are picked up live via Vite HMR — only a package.json/
# package-lock.json change requires `docker compose build frontend` again.
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
