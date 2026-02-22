# IndestructibleEco v1.0 — Web Frontend
# Build: docker build -t eco-web:latest platforms/web/
# Context: platforms/web/
FROM node:20-alpine AS builder
WORKDIR /app

# Copy package.json and strip workspace:* dependencies that don't resolve in Docker
COPY ./package.json ./
RUN node -e " \
  const pkg = JSON.parse(require('fs').readFileSync('package.json','utf8')); \
  for (const section of ['dependencies','devDependencies','peerDependencies']) { \
    if (pkg[section]) { \
      for (const [k,v] of Object.entries(pkg[section])) { \
        if (String(v).includes('workspace:')) delete pkg[section][k]; \
      } \
    } \
  } \
  pkg.scripts = pkg.scripts || {}; \
  pkg.scripts.build = 'vite build'; \
  require('fs').writeFileSync('package.json', JSON.stringify(pkg, null, 2)); \
" && npm install --legacy-peer-deps

# Copy app source and build
COPY ./app/ ./app/
RUN cd app && npx vite build --outDir ../dist

FROM nginx:1.25-alpine AS production
LABEL org.opencontainers.image.title="IndestructibleEco Web Frontend" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="IndestructibleOrg" \
      org.opencontainers.image.source="https://github.com/indestructibleorg/indestructibleeco"

# SECURITY NOTE: Nginx runs as root (uid 0) to bind privileged port 80.
# This is a documented exception. In production, consider:
# 1. Using a reverse proxy (e.g., Envoy) that handles port 80/443
# 2. Running nginx on unprivileged port (e.g., 8080) with port mapping
# 3. Using Linux capabilities (CAP_NET_BIND_SERVICE) instead of full root

# Nginx config with API proxy, WebSocket, SPA fallback, health check
RUN printf 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
\n\
    location /health {\n\
        access_log off;\n\
        return 200 '\''{"status":"healthy","service":"eco-web"}'\'';\n\
        add_header Content-Type application/json;\n\
    }\n\
\n\
    location /api/ {\n\
        proxy_pass http://eco-api-svc:3000;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
\n\
    location /ws {\n\
        proxy_pass http://eco-api-svc:3000;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade $http_upgrade;\n\
        proxy_set_header Connection "upgrade";\n\
    }\n\
\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
\n\
    gzip on;\n\
    gzip_types text/plain text/css application/json application/javascript text/xml;\n\
}\n' > /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
