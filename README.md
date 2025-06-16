# Telegram Runtipi Controller 🤖

Bot Telegram simples e funcional para monitorar e controlar os apps do seu servidor [Runtipi](https://github.com/runtipi/runtipi).

---

## 📦 Funcionalidades

- 🔍 Listar todos os apps instalados
- 📊 Ver status dos apps (rodando ou parados)
- 🟢🔴 Ligar/Desligar apps via comando `toggle`
- 🔐 Restringe comandos ao chat ID autorizado

---

## 🚀 Como Usar

### 1. Clonar o repositório

```bash
git clone https://github.com/ma-pavone/telegram_runtipi.git
cd telegram_runtipi
2. Criar o .env
Crie um arquivo .env com as seguintes variáveis:

env
Copy
Edit
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=123456789
RUNTIPI_HOST=http://192.168.x.x
RUNTIPI_USERNAME=admin
RUNTIPI_PASSWORD=suasenha
⚠️ TELEGRAM_CHAT_ID pode ser obtido usando o bot em modo debug, logando o update.effective_chat.id

3. Subir com Docker Compose
bash
Copy
Edit
docker compose up -d --build
📡 Comandos Disponíveis no Bot
Comando	Descrição
/start	Mostra os comandos e boas-vindas
/apps	Lista os apps instalados com status
/status	Lista somente status de apps
toggle <nome_app>	Liga ou desliga o app (ex: toggle jellyfin)

🐳 Docker
Dockerfile otimizado
dockerfile
Copy
Edit
FROM python:3.11.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
CMD ["python", "src/telegram_runtipi.py"]
🔐 Segurança
As credenciais do Runtipi são carregadas por variável de ambiente (.env)

O acesso é restrito por TELEGRAM_CHAT_ID