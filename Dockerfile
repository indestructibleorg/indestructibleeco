# syntax=docker/dockerfile:1
# Base stage for dependencies
FROM node:20-slim AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./

# Build stage
FROM base AS build
ENV NODE_ENV=production
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

# Production stage
FROM node:20-slim AS production
ENV NODE_ENV=production
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
WORKDIR /app
COPY --from=build /app/package.json /app/package.json
COPY --from=build /app/pnpm-lock.yaml /app/pnpm-lock.yaml
RUN --mount=type=cache,id=pnpm-production,target=/pnpm/store pnpm install --prod --frozen-lockfile
COPY --from=build /app/dist /app/dist

EXPOSE 3000
CMD ["npm", "start"]
