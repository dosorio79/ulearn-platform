FROM node:20-alpine AS build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
COPY HELP.md /app/HELP.md
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/frontend/dist/ /usr/share/nginx/html/
COPY frontend/nginx/default.conf /etc/nginx/conf.d/default.conf
