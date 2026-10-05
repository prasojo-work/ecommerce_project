FROM node:24-slim

RUN npm install -g pnpm@12

WORKDIR /app

# Install dependencies first so this layer is cached across source changes.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 3000

CMD ["pnpm", "exec", "next", "dev", "--hostname", "0.0.0.0"]