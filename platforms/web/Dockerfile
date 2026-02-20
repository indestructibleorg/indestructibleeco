# IndestructibleEco v1.0 — Web Frontend
# Build: docker build -t eco-web:latest platforms/web/
# Context: platforms/web/
FROM node:20-alpine AS builder
WORKDIR /app
COPY app/package.json ./
RUN npm install --legacy-peer-deps
COPY app/ ./
RUN npm run build 2>/dev/null || npx vite build

FROM nginx:1.25-alpine AS production
LABEL org.opencontainers.image.title="IndestructibleEco Web Frontend" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="IndestructibleOrg" \
      org.opencontainers.image.source="https://github.com/indestructibleorg/indestructibleeco"
COPY --from=builder /app/dist /usr/share/nginx/html
COPY <<'NGINX_CONF' /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location /health {
        access_log off;
        return 200 '{"status":"healthy","service":"eco-web"}';
        add_header Content-Type application/json;
    }

    location /api/ {
        proxy_pass http://eco-api-svc.eco-staging.svc.cluster.local:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://eco-api-svc.eco-staging.svc.cluster.local:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
}
NGINX_CONF
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
