# Single-container build: React app + FastAPI + shared models in one image (D-005).
# Runs unchanged on Hugging Face Spaces (port 7860), a laptop, or a Raspberry Pi 4 (arm64) at the cooperative (D-004).
#
#   docker build -t karibu .
#   docker run -p 7860:7860 karibu
#   docker buildx build --platform linux/arm64 -t karibu:pi .     # edge box image

# ---- 1. build the frontend (copies ../shared into dist/shared) ----
FROM node:18-alpine AS web
WORKDIR /src
COPY shared ./shared
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci --no-audit --no-fund
COPY frontend ./frontend
RUN cd frontend && npm run build

# ---- 2. runtime: Python + stdlib sqlite, no ML libraries needed at runtime ----
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    SHARED_DIR=/app/shared STATIC_DIR=/app/frontend/dist DB_PATH=/data/karibu.db \
    CORS_ORIGINS="" PORT=7860
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app ./backend/app
COPY shared ./shared
COPY --from=web /src/frontend/dist ./frontend/dist
RUN mkdir -p /data && chmod 777 /data
WORKDIR /app/backend
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
