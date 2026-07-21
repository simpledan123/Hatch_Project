FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package.json package-lock.json /app/
RUN npm ci

COPY src /app/src
COPY index.html /app/index.html

RUN npm run build


FROM nginx:1.27-alpine

# 로컬 구성은 HTTP로 실행한다. 운영 환경에서는 docker-compose.prod.yml이
# HTTPS 템플릿을 같은 경로에 마운트한다.
COPY nginx.local.conf /etc/nginx/templates/default.conf.template

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
