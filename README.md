# Telegram Bot para Runtipi

Um bot para Telegram que permite controlar e monitorar seus aplicativos Runtipi, além de executar scripts remotamente.

---

## Funcionalidades

- **Listar Apps**: Veja todos os aplicativos instalados e seu status (rodando/parado).
- **Controlar Apps**: Inicie ou pare qualquer aplicativo com uma simples mensagem.
- **Executar Scripts**: Liste e execute scripts shell localizados em um diretório seguro.
- **Status Rápido**: Obtenha um resumo rápido de quantos apps estão ativos.
- **Segurança**: O bot responde apenas a um `chat_id` do Telegram pré-configurado.
- **Health Check**: Expõe um endpoint `/health` na porta `7777` para monitoramento.

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

1.  Adicione o repositório deste projeto à sua lista de App Stores customizadas no Runtipi.
2.  Encontre "Telegram Runtipi Bot" na sua App Store e clique em "Instalar".
3.  Preencha os campos de configuração na interface do Runtipi:
    - **Credenciais do Runtipi**: Usuário e senha para o bot se autenticar na API.
    - **Configurações do Telegram**: O token do seu bot e o ID do chat autorizado.
    - **Caminho dos Scripts**: O diretório no seu servidor que contém os scripts que o bot poderá executar.
4.  Clique em "Instalar" e o Runtipi cuidará do resto.