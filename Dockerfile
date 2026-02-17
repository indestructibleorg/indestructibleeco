# syntax=docker/dockerfile:1

# Build stage
FROM node:20-slim AS builder

# Enable Corepack for pnpm
RUN corepack enable && corepack prepare pnpm@10.4.1 --activate

WORKDIR /app

# Copy package files and patches directory for pnpm patchedDependencies
COPY package.json pnpm-lock.yaml ./
COPY patches ./patches

# Install dependencies
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build application (client + server)
RUN pnpm run build

# Production stage
FROM node:20-slim AS runtime

# Enable Corepack for pnpm
RUN corepack enable && corepack prepare pnpm@10.4.1 --activate

WORKDIR /app

# Copy package files and patches directory for pnpm patchedDependencies
COPY package.json pnpm-lock.yaml ./
COPY patches ./patches

# Install production dependencies only
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --prod --frozen-lockfile

# Copy built artifacts from builder
COPY --from=builder /app/dist ./dist

# Create non-root user for running the application
RUN groupadd -r nodeapp && useradd -r -g nodeapp -s /bin/false nodeapp && \
    chown -R nodeapp:nodeapp /app

# Switch to non-root user
USER nodeapp

# Expose port
EXPOSE 8080

# Set environment variables
ENV NODE_ENV=production
ENV PORT=8080

# Start the server
CMD ["node", "dist/index.js"]
