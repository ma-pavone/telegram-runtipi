FROM python:3.11.9-slim AS builder

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11.9-slim

LABEL maintainer="ma-pavone"
LABEL description="Telegram Bot para controle do Runtipi"
LABEL version="2.0.0"

WORKDIR /app

# Instala apenas curl para health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copia as dependências instaladas do builder
COPY --from=builder /root/.local /root/.local

# Copia o código fonte
COPY src/ ./src/

# Variáveis de ambiente padrão
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/root/.local/bin:$PATH

# Comando padrão
CMD ["python", "src/app.py"]