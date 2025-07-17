# Telegram Runtipi Bot

Um bot completo para controle e monitoramento de aplicativos no seu servidor Runtipi através do Telegram.

## Funcionalidades

- **Controle de Aplicativos:** Liste, inicie e pare qualquer aplicativo instalado na sua Runtipi com comandos simples.
- **Status Rápido:** Obtenha um resumo rápido de quantos aplicativos estão rodando ou parados.
- **Executor de Scripts:** Liste e execute scripts de shell (`.sh`) localizados em um diretório do seu servidor diretamente pelo bot, de forma segura.
- **Segurança:** O bot opera apenas com um `chat_id` autorizado, garantindo que somente você possa controlar o servidor.
- **Health Check:** Possui um endpoint `/health` para monitoramento por serviços como Healthchecks.io.

## Comandos Disponíveis

- `/help`: Mostra a mensagem de ajuda.
- `/apps`: Lista detalhada de todos os aplicativos e seus status.
- `/status`: Resumo do status dos aplicativos (rodando/parados).
- `/scripts`: Lista os scripts disponíveis para execução.
- `/run <script_name>`: Executa um script específico.
- Para ligar/desligar um app, basta enviar seu ID (ex: `jellyfin`).