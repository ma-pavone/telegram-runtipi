# Telegram Bot para gerenciamento do Noteserver Runtipi

Bot para controle e monitoramento de apps no Noteserver Runtipi via Telegram.

---

## Comandos Disponíveis

- `/help`  
  Mostra essa mensagem de ajuda.

- `/status`  
  Lista o status (rodando/parado) dos apps instalados no Runtipi usando seus nomes técnicos.

- `/toggle <app_id>`  
  Liga ou desliga o app especificado pelo ID técnico.

- `/list`  
  Lista os scripts disponíveis para execução no diretório configurado pela variável de ambiente `SCRIPTS_DIR`.

- `/run <script_name>`  
  Executa o script informado, caso exista e seja executável.

---

## Variáveis de Ambiente

- `TELEGRAM_BOT_TOKEN` — Token do bot Telegram.
- `RUNTIPI_API_URL` — URL da API do Runtipi.
- `RUNTIPI_API_TOKEN` — Token de autenticação da API Runtipi.
- `SCRIPTS_DIR` — Caminho absoluto do diretório que contém os scripts que podem ser listados e executados pelo bot.

---

## Docker

- Certifique-se de que o arquivo `.env` esteja na raiz, contendo as variáveis acima.
- No `docker-compose.yml`, utilize:
  ```yaml
  env_file:
    - .env
  volumes:
    - ${SCRIPTS_DIR}:${SCRIPTS_DIR}:ro
