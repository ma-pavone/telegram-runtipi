# Dockerfile
FROM python:3.11-slim

# Argumentos de build
ARG BUILD_DATE
ARG VERSION="1.0.0"

# Labels para metadados
LABEL maintainer="seu-email@exemplo.com" \
      description="Bot Telegram para controle do Runtipi" \
      version="${VERSION}" \
      build_date="${BUILD_DATE}"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN groupadd -r botuser && useradd -r -g botuser botuser

RUN mkdir -p /app /scripts /app/logs && \
    chown -R botuser:botuser /app /scripts

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN chown -R botuser:botuser /app

USER botuser

EXPOSE 7777

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7777/health || exit 1

CMD ["python", "-m", "src.app"]