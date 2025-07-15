# 🤖 Telegram Runtipi Bot

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

Bot do Telegram escrito em **Python** para **gerenciar um servidor [Runtipi](https://runtipi.io/)**. Permite visualizar status de apps, iniciar/parar serviços e executar scripts `.sh` diretamente do Telegram.

## ✨ Funcionalidades

- 🔍 **Listagem de Apps**: Visualize todos os aplicativos do Runtipi e seus status.
- 🟢🔴 **Controle de Apps**: Inicie ou pare qualquer app via comando.
- 🧾 **Execução de Scripts**: Scripts `.sh` executáveis a partir de comandos do bot.
- 🔐 **Segurança**: Restringe comandos a um `CHAT_ID` autorizado.
- ⚡ **Cache Inteligente**: Reduz chamadas repetidas à API.
- 🧩 **Integração com Runtipi**: App compatível com App Store personalizada do Runtipi.

---

## 📜 Comandos Disponíveis

| Comando | Descrição |
|--------|-----------|
| `/start` ou `/help` | Mostra lista de comandos disponíveis |
| `/apps` | Lista os apps com seus status (🟢 Rodando, 🔴 Parado) |
| `/status` | Mostra resumo de apps rodando/parados |
| `/toggle <app_id>` | Inicia ou para um app específico. Ex: `/toggle jellyfin` |
| `/scripts` | Lista scripts `.sh` disponíveis |
| `/run <script.sh>` | Executa script autorizado. Ex: `/run backup.sh` |

---

## ⚙️ Configuração

Crie um arquivo `.env` com base no exemplo abaixo:

```env
# Token do bot Telegram (@BotFather)
TELEGRAM_TOKEN="SEU_TOKEN_AQUI"

# ID do chat autorizado (use @userinfobot)
ALLOWED_CHAT_ID="SEU_CHAT_ID"

# Endereço do servidor Runtipi
RUNTIPI_HOST="http://192.168.15.3:8080"

# Credenciais de login
RUNTIPI_USER="admin"
RUNTIPI_PASSWORD="minhaSenhaSecreta"

# (Opcional) Nível de log: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL="INFO"

# (Opcional) Caminho interno onde estão os scripts
SCRIPTS_DIR="/scripts"
