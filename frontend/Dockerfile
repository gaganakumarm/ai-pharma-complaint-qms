FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL=http://localhost:8000
ARG VITE_MAX_UPLOAD_SIZE_MB=10
ARG VITE_AI_REQUEST_TIMEOUT_MS=120000
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_MAX_UPLOAD_SIZE_MB=$VITE_MAX_UPLOAD_SIZE_MB
ENV VITE_AI_REQUEST_TIMEOUT_MS=$VITE_AI_REQUEST_TIMEOUT_MS
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
