FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Production image: serve with nginx ────────────────────────────────────────
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# nginx config: SPA fallback to index.html
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location ~ ^/(auth|machines|config|health) {\n\
        proxy_pass http://backend:8000;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80
