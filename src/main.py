from api.deepai import DeepAIAPI
from api.translate import GoogleTranslateAPI
from bot.access import WarningsProcessor
from bot.stickers import StickerManager
from bot.bot import Bot
from storage.postgres import PostgresDatabase
from message.filter import LanguageFilter
from sticker.artist import StickerArtist
from storage.s3 import ImageS3Storage
from sticker.generator import StickerGenerator


if __name__ == "__main__":
    database = PostgresDatabase()
    sticker_file_manager = ImageS3Storage()
    
    google_api = GoogleTranslateAPI()
    deepai_api = DeepAIAPI()
    sticker_generator = StickerGenerator(google_api, deepai_api)
    sticker_artist = StickerArtist(sticker_file_manager, sticker_generator)

    prompt_detector = LanguageFilter()
    
    warning_processor = WarningsProcessor(database)
    sticker_manager = StickerManager(database, sticker_artist)
    bot = Bot(database, prompt_detector, warning_processor, sticker_artist, sticker_manager)
    bot.run()
