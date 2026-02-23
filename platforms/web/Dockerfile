# IndestructibleEco v1.0 — Web Frontend
# Build: docker build -t eco-web:latest platforms/web/
# Context: platforms/web/
FROM node:20-alpine AS builder
WORKDIR /app

# Copy the app/ subdirectory which contains the TypeScript React app
# (app/ has its own package.json, vite.config.ts, index.html, and src/)
COPY ./app/ ./

# Install all dependencies (including dev deps for build)
RUN npm install --legacy-peer-deps

# Build the app
RUN npm run build

FROM nginx:1.25-alpine AS production
LABEL org.opencontainers.image.title="IndestructibleEco Web Frontend" \
      org.opencontainers.image.version="1.0.2" \
      org.opencontainers.image.vendor="IndestructibleOrg" \
      org.opencontainers.image.source="https://github.com/indestructibleorg/eco-base"

# Fix nginx to run as non-root (uid 101 = nginx user in alpine)
# Create required cache directories with correct permissions
RUN mkdir -p /var/cache/nginx/client_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp \
             /var/cache/nginx/uwsgi_temp \
             /var/cache/nginx/scgi_temp \
             /var/run/nginx \
  && chown -R nginx:nginx /var/cache/nginx /var/run/nginx \
  && chmod -R 755 /var/cache/nginx /var/run/nginx

# Nginx config with API proxy to production namespace, WebSocket, SPA fallback, health check
RUN printf 'user nginx;\n\
worker_processes auto;\n\
pid /var/run/nginx/nginx.pid;\n\
\n\
events {\n\
    worker_connections 1024;\n\
}\n\
\n\
http {\n\
    include       /etc/nginx/mime.types;\n\
    default_type  application/octet-stream;\n\
    sendfile on;\n\
    keepalive_timeout 65;\n\
\n\
    server {\n\
        listen 80;\n\
        server_name _;\n\
        root /usr/share/nginx/html;\n\
        index index.html;\n\
\n\
        location /health {\n\
            access_log off;\n\
            return 200 '"'"'{"status":"healthy","service":"eco-web"}'"'"';\n\
            add_header Content-Type application/json;\n\
        }\n\
\n\
        location /api {\n\
            proxy_pass http://eco-api-svc.eco-production.svc.cluster.local:3000;\n\
            proxy_set_header Host $host;\n\
            proxy_set_header X-Real-IP $remote_addr;\n\
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
            proxy_set_header X-Forwarded-Proto $scheme;\n\
        }\n\
\n\
        location /ws {\n\
            proxy_pass http://eco-api-svc.eco-production.svc.cluster.local:3000;\n\
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
    }\n\
}\n' > /etc/nginx/nginx.conf

COPY --from=builder /app/dist /usr/share/nginx/html
RUN chown -R nginx:nginx /usr/share/nginx/html

USER nginx

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
