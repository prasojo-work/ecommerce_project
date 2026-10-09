# syntax=docker/dockerfile:1

# LYSHEIM web — Next.js App Router, served by `next start`.
# Built by compose.yml; see docs/04-delivery/RUNBOOK.md section 2.

FROM node:24-bookworm-slim AS base

ENV PNPM_HOME=/pnpm \
    PATH="/pnpm:$PATH" \
    NEXT_TELEMETRY_DISABLED=1

RUN npm install --global pnpm@12.3.4

FROM base AS builder

WORKDIR /app

# Dependencies first, so this layer stays cached until the manifest or lockfile changes.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

# Next inlines NEXT_PUBLIC_* into the client bundle, so it is a build-time input.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

RUN pnpm build

FROM base AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

COPY --from=builder --chown=node:node /app ./

USER node

EXPOSE 3000

CMD ["pnpm", "start"]
