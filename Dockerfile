FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/olivierpetitjean/sentinel-whisper-server" \
      org.opencontainers.image.url="https://github.com/olivierpetitjean/sentinel-whisper-server" \
      org.opencontainers.image.title="sentinel-whisper-server" \
      org.opencontainers.image.description="Minimal CPU-only Whisper ASR server for Sentinel (FastAPI + Swagger/OpenAPI)." \
      org.opencontainers.image.licenses="MIT"

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 9000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]