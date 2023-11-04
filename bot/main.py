import os
from bot import Bot
from config import load_config

if __name__ == "__main__":

    load_config()

    bot = Bot()
    bot.run()
