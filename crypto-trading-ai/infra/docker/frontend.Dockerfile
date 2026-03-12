FROM node:20-alpine

WORKDIR /app
RUN npm install -g pnpm

COPY package.json /app/package.json
COPY pnpm-workspace.yaml /app/pnpm-workspace.yaml
COPY frontend /app/frontend
COPY shared /app/shared

WORKDIR /app/frontend
RUN pnpm install

CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "3000"]
