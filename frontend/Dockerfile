FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package.json /app/package.json
RUN npm install

COPY src /app/src
COPY index.html /app/index.html

RUN npm run build


FROM nginx:1.27-alpine

# nginx 공식 이미지는 /etc/nginx/templates/*.template 파일을
# 컨테이너 시작 시 envsubst로 자동 처리하여 /etc/nginx/conf.d/ 에 배치함
COPY nginx.conf /etc/nginx/templates/default.conf.template

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]