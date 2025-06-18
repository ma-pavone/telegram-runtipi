# Etapa de build (instalação de dependências)
FROM python:3.11.9-slim AS builder

RUN apt-get update && apt-get install -y build-essential \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /install

COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Etapa final (execução)
FROM python:3.11.9-slim

LABEL maintainer="ma-pavone"
LABEL description="Telegram Bot para controle do Runtipi"
LABEL version="2.1.0"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    docker.io \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN adduser --disabled-password --gecos '' --uid 1000 appuser

# Copia pacotes Python da build
COPY --from=builder /install /usr/local

# Copia o código-fonte
COPY src/ ./src/

# Permissões
RUN chown -R 1000:1000 /app
USER appuser

# Variáveis de ambiente
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "src/app.py"]
