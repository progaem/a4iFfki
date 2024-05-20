from utils.utils import load_config, masked_print
from api.bot import Bot
from storage.postgres import PostgresDatabase
from messaging.prompt_detector import PromptDetector
from sticker.creation_manager import StickerCreationManager
from storage.s3 import ImageS3Storage
from sticker.generator import StickerGenerator


if __name__ == "__main__":
    # load all variables from devo.conf to environmental variables
    load_config()

    # set up connection with db
    db_manager = PostgresDatabase()

    # create needed services
    prompt_detector = PromptDetector()
    sticker_file_manager = ImageS3Storage()
    text_to_image_generator = StickerGenerator()
    sticker_manager = StickerCreationManager(sticker_file_manager, text_to_image_generator)

    # Run telegram bot
    bot = Bot(db_manager, prompt_detector, sticker_manager)
    bot.run()
