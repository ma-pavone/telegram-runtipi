# src/app.py
import logging
from config.settings import BotConfig
from bot.core import RuntipiBot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    config = BotConfig.from_env()
    bot = RuntipiBot(config)
    bot.run()

if __name__ == "__main__":
    main()