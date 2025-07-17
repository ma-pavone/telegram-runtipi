# Telegram Bot para Runtipi

Um bot para Telegram que permite controlar e monitorar seus aplicativos Runtipi, além de executar scripts remotamente.

---

## Funcionalidades

- **Listar Apps**: Veja todos os aplicativos instalados e seu status (rodando/parado).
- **Controlar Apps**: Inicie ou pare qualquer aplicativo com uma simples mensagem.
- **Executar Scripts**: Liste e execute scripts shell localizados em um diretório seguro.
- **Status Rápido**: Obtenha um resumo rápido de quantos apps estão ativos.
- **Segurança**: O bot responde apenas a um `chat_id` do Telegram pré-configurado.

---

## Comandos Disponíveis

- `/start` ou `/help` - Mostra a mensagem de ajuda.
- `/apps` - Lista todos os apps instalados com seus respectivos status.
- `/status` - Mostra um resumo de quantos apps estão rodando e parados.
- `/scripts` - Lista os scripts executáveis disponíveis no diretório configurado.
- `/run <nome_do_script>` - Executa um script específico.
- *Qualquer outra mensagem* (ex: `jellyfin`) - Tenta dar toggle (ligar/desligar) no app com aquele nome.

---

## Instalação via Runtipi App Store

1. Adicione o repositório deste projeto à sua lista de App Stores customizadas no Runtipi.
2. Encontre "Telegram Runtipi Bot" na sua App Store e clique em "Instalar".
3. Preencha os campos de configuração na interface do Runtipi:
   - **Credenciais do Runtipi**: Usuário e senha para o bot se autenticar na API.
   - **Configurações do Telegram**: O token do seu bot e o ID do chat autorizado.
   - **Caminho dos Scripts**: O diretório no seu servidor que contém os scripts que o bot poderá executar.
4. Clique em "Instalar" e o Runtipi cuidará do resto.

---

## Instalação Manual

### Pré-requisitos

- Docker e Docker Compose instalados
- Bot do Telegram criado via @BotFather
- Acesso ao seu servidor Runtipi

### Configuração

1. Clone o repositório:
   ```bash
   git clone https://github.com/ma-pavone/telegram-runtipi.git
   cd telegram-runtipi
   ```

2. Crie o arquivo `.env` baseado no `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Edite o arquivo `.env` com suas configurações:
   ```
   TELEGRAM_TOKEN=seu_token_aqui
   TELEGRAM_CHAT_ID=seu_chat_id_aqui
   RUNTIPI_HOST=http://192.168.15.3:80
   RUNTIPI_USERNAME=seu_usuario
   RUNTIPI_PASSWORD=sua_senha
   SCRIPTS_PATH=/caminho/para/scripts
   ```

4. Inicie o bot:
   ```bash
   docker-compose up -d
   ```

### Usando o Makefile (Opcional)

Se você preferir usar o Makefile para gerenciar o bot:

```bash
# Verificar variáveis de ambiente
make check-env

# Construir a imagem
make build

# Iniciar o bot
make up

# Ver logs
make logs

# Parar o bot
make down
```