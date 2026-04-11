# KAIA – Kinetic AI Agent
# Docker Image für Hetzner Cloud Deployment

FROM python:3.11-slim

# System-Dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies zuerst installieren (Docker Layer Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# Datenverzeichnis anlegen
RUN mkdir -p /app/data

# Streamlit-Konfiguration
COPY .streamlit/config.toml /app/.streamlit/config.toml

EXPOSE 8501

CMD streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
