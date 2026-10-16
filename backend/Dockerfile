# syntax=docker/dockerfile:1.7
# ---------- build stage: compile/install dependencies into a virtualenv ----------
FROM python:3.12-slim-bookworm AS build

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt

# ---------- runtime stage: slim image with only the venv and the app ----------
FROM python:3.12-slim-bookworm AS runtime

ARG APP_VERSION=dev
LABEL org.opencontainers.image.title="slotsync-backend" \
      org.opencontainers.image.description="SlotSync appointment booking API (FastAPI)" \
      org.opencontainers.image.source="https://github.com/anushkabhansalii/apoointment-booking-devops-project" \
      org.opencontainers.image.version="${APP_VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_VERSION=${APP_VERSION}

# Pick up Debian security fixes, then drop pip/setuptools from the system
# Python: the app runs from /opt/venv and never needs them at runtime.
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* \
 && pip uninstall -y pip setuptools wheel 2>/dev/null || true

# Unprivileged user with a fixed UID so Kubernetes runAsNonRoot can verify it.
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app app ./app
COPY --chown=app:app docker-entrypoint.sh ./

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
