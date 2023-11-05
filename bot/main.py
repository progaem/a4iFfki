from utils.utils import load_config, masked_print
from bot import Bot
from db.db_manager import DbManager
from prompt.prompt_detector import PromptDetector
from sticker.sticker_generator import StickerGenerator


if __name__ == "__main__":
    # load all variables from devo.conf to environmental variables
    load_config()

    # set up connection with db
    db_manager = DbManager()

    # create needed services
    prompt_detector = PromptDetector()
    sticker_generator = StickerGenerator()

    # Run telegram bot
    bot = Bot(db_manager, prompt_detector, sticker_generator)
    bot.run()
