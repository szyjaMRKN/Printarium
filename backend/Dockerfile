# Backend: FastAPI + SQLite
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data \
    BACKUP_DIR=/backups \
    UPLOAD_DIR=/uploads

# fonts-dejavu-core jest potrzebny do polskich znaków w dokumentach PDF.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /data /backups /uploads \
    && useradd --uid 10001 --create-home ewidencja \
    && chown -R 10001:10001 /data /backups /uploads

# Aplikacja nie potrzebuje roota — kontener startuje jako użytkownik bez uprawnień administratora.
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
