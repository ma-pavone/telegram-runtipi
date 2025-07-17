# Bot de Controle do Runtipi para Telegram

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

Um bot simples, seguro e eficiente para gerenciar sua instância [Runtipi](https://runtipi.io/) diretamente pelo Telegram.

Este bot permite que você liste, inicie e pare seus aplicativos, além de executar scripts pré-definidos no seu servidor de forma segura, com acesso restrito apenas ao seu ID de chat do Telegram.

## ✨ Funcionalidades

- **Gerenciamento de Apps**: Liste todos os aplicativos instalados, veja seus status (`running` ou `stopped`) e ligue/desligue-os com um comando ou simplesmente enviando o nome do app.
- **Resumo Rápido**: Obtenha um resumo de quantos aplicativos estão ativos com o comando `/status`.
- **Executor de Scripts**: Execute com segurança qualquer script shell que você disponibilizar em um diretório montado.
- **Seguro e Privado**: O bot só responderá aos comandos enviados pelo seu Chat ID do Telegram, ignorando todas as outras interações.
- **Leve**: Construído com poucas dependências e otimizado para rodar de forma eficiente em seu servidor.

---

## 🚀 Instalação e Configuração

A forma mais fácil de instalar o bot é através da sua própria App Store do Runtipi.

### 1. Adicionar à App Store do Runtipi

Se você já tem uma App Store customizada, adicione este repositório a ela. Ao instalar pela interface do Runtipi, os campos abaixo serão solicitados e configurados como variáveis de ambiente automaticamente.

### 2. Configuração das Variáveis de Ambiente

Na interface do Runtipi, você precisará preencher os seguintes campos:

| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| `TELEGRAM_TOKEN` | O token de autenticação do seu bot, fornecido pelo `@BotFather`. | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`|
| `TELEGRAM_CHAT_ID` | O seu ID de usuário único do Telegram. Fale com o `@userinfobot` para obtê-lo. | `123456789` |
| `RUNTIPI_USERNAME` | Seu nome de usuário do Runtipi. | `admin` |
| `RUNTIPI_PASSWORD` | Sua senha do Runtipi. | `SuaSenhaSuperSegura` |
| `SCRIPTS_PATH` | O caminho **no host** para a pasta que contém seus scripts. | `/home/user/runtipi-scripts` |

### 3. Criando a Pasta de Scripts

No seu servidor (host), crie o diretório que você especificou em `SCRIPTS_PATH`. É aqui que você colocará os scripts que deseja executar via Telegram.

```bash
mkdir -p /home/user/runtipi-scripts
🤖 Como Usar o Bot
Após a instalação, inicie uma conversa com seu bot no Telegram. Ele responderá aos seguintes comandos:

Comandos Disponíveis
Comando	Descrição
/start ou /help	Mostra a mensagem de ajuda com a lista de comandos.
/apps	Lista todos os seus aplicativos Runtipi e o status deles (✅ Ativo / ❌ Inativo).
/status	Exibe um resumo rápido de quantos aplicativos estão em execução.
/scripts	Lista todos os scripts executáveis que você colocou na pasta de scripts.
/run [nome_do_script]	Executa um script específico da sua lista. Ex: /run backup.sh.

Exportar para as Planilhas
Ligar/Desligar Apps por Texto
Além dos comandos, você pode simplesmente enviar uma mensagem com o id exato de um aplicativo (ex: jellyfin) para iniciá-lo (se estiver parado) ou pará-lo (se estiver rodando).
```

📜 Executando Scripts Customizados
Esta é uma funcionalidade poderosa para automações, como fazer backups, atualizar serviços ou executar qualquer rotina que você precise.

Crie seu script: Crie um arquivo shell (ex: backup_vaultwarden.sh) dentro da pasta que você configurou em SCRIPTS_PATH.

Torne-o Executável: Esta é a etapa mais importante. O bot só listará e executará scripts que tiverem permissão de execução.

```bash
chmod +x /caminho/no/host/para/seu/script.sh
Use o bot:

Envie /scripts para garantir que seu novo script apareceu na lista.

Envie /run seu_script.sh para executá-lo.
```

O bot enviará a saída (e erros, se houver) do script diretamente no chat quando a execução terminar.

🐳 Docker Compose
Para referência, este é o docker-compose.yml usado pelo Runtipi para rodar o serviço.

```yaml
services:
  telegram-runtipi:
    image: maopppenheim/telegram-runtipi:0.0.1
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ${SCRIPTS_PATH}:/scripts:ro
    networks:
      - tipi_main_network

networks:
  tipi_main_network:
    external: true
```