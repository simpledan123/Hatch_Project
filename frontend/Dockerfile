FROM node:20-alpine

WORKDIR /app

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package.json /app/package.json
RUN npm install

COPY src /app/src
COPY index.html /app/index.html

CMD ["npm", "run", "dev"]
