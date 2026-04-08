# KAIA – Kinetic AI Agent
# Docker Image für Railway-Deployment

FROM python:3.11-slim

# System-Dependencies
# ffmpeg: für faster-whisper (Audio-Verarbeitung)
# build-essential: für native Python-Pakete
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Dependencies zuerst installieren (Docker Layer Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# Datenverzeichnis anlegen (wird als Railway Volume gemountet)
RUN mkdir -p /app/data

# Streamlit-Konfiguration
COPY .streamlit/config.toml /app/.streamlit/config.toml

# Port den Railway erwartet
EXPOSE 8501

# Start
CMD streamlit run app.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true
