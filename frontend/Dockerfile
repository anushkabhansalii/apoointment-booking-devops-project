# syntax=docker/dockerfile:1.7
# ---------- stage 1: build the static React bundle with Node ----------
# The bundle is plain HTML/JS/CSS, identical for every CPU architecture, so it is
# built once on the native build platform; only the Nginx stage is per-arch.
# (Running npm under QEMU emulation for arm64 is slow and can hang.)
FROM --platform=$BUILDPLATFORM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
ARG APP_VERSION=dev
ENV VITE_APP_VERSION=${APP_VERSION}
RUN npm run build

# ---------- stage 2: serve it with an unprivileged Nginx ----------
# nginx-unprivileged runs as UID 101 and listens on 8080, so no root and no
# privileged port is needed. Node, npm and the source never reach this image.
FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime

ARG APP_VERSION=dev
LABEL org.opencontainers.image.title="slotsync-frontend" \
      org.opencontainers.image.description="SlotSync booking dashboard (React + Nginx)" \
      org.opencontainers.image.source="https://github.com/anushkabhansalii/apoointment-booking-devops-project" \
      org.opencontainers.image.version="${APP_VERSION}"

USER root
RUN apk upgrade --no-cache
USER 101

# The official image renders /etc/nginx/templates/*.template with envsubst at
# start-up, so BACKEND_URL can differ between Compose and Kubernetes.
ENV BACKEND_URL=http://backend:8000
COPY --chown=101:101 nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build --chown=101:101 /app/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
