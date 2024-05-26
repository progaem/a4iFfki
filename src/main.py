"""
This module serves as the entry point for the sticker bot application.
The application initializes and binds together components for bot orchestration
"""
from api.deepai import DeepAIAPI
from api.translate import GoogleTranslateAPI

from bot.access import WarningsProcessor
from bot.bot import Bot
from bot.stickers import StickerManager

from message.filter import LanguageFilter

from storage.postgres import PostgresDatabase
from storage.s3 import ImageS3Storage

from sticker.artist import StickerArtist
from sticker.generator import StickerGenerator


if __name__ == "__main__":
    database = PostgresDatabase()
    sticker_file_manager = ImageS3Storage()

    google_api = GoogleTranslateAPI()
    deepai_api = DeepAIAPI()
    sticker_generator = StickerGenerator(google_api, deepai_api)
    sticker_artist = StickerArtist(sticker_file_manager, sticker_generator)

    language_filter = LanguageFilter()

    warning_processor = WarningsProcessor(database)
    sticker_manager = StickerManager(database, sticker_artist)
    bot = Bot(database, sticker_file_manager, language_filter, warning_processor, sticker_artist, sticker_manager)
    bot.run()
