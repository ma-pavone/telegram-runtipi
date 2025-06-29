# ---- Base Builder Stage ----
# Usa uma imagem Python completa para compilar dependências
FROM python:3.11-slim as builder

# Define o diretório de trabalho
WORKDIR /usr/src/app

# Copia o arquivo de dependências para o diretório de trabalho
COPY requirements.txt ./

# Instala as dependências em um diretório de usuário para não precisar ser root
RUN pip install --user --no-cache-dir -r requirements.txt

# ---- Final Stage ----
# Usa uma imagem slim para a execução final
FROM python:3.11-slim

# Define o diretório de trabalho final
WORKDIR /app

# Copia as dependências instaladas do builder stage
COPY --from=builder /root/.local /root/.local

# Copia o código-fonte da sua aplicação
COPY src ./src

# Adiciona o diretório de binários dos pacotes de usuário ao PATH
ENV PATH=/root/.local/bin:$PATH

# Expõe a porta do health server
EXPOSE 7777

# Comando para iniciar a aplicação
CMD ["python", "-m", "src.app"]