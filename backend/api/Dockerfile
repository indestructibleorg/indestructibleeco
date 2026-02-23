FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json .npmrc ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
LABEL org.opencontainers.image.source="https://github.com/indestructibleorg/indestructibleeco"
LABEL org.opencontainers.image.title="IndestructibleEco API Service"
LABEL org.opencontainers.image.vendor="IndestructibleOrg"
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json .

EXPOSE 3000
RUN addgroup --system --gid 1001 eco && adduser --system --uid 1001 --ingroup eco eco
USER eco
CMD ["node", "dist/server.js"]