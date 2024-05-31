"""
This module handles all AI sticker generation process
"""
from PIL import Image

from api.deepai import DeepAIAPI
from api.translate import GoogleTranslateAPI

from common.common import BaseClass
from common.exceptions import StickerGeneratorError

class StickerGenerator(BaseClass):
    """
    Class that handles the process of creating a sticker from prompt,
        through utilizing DeepAI and Google Translate API
    """

    def __init__(self, google_translate_api: GoogleTranslateAPI, deep_api: DeepAIAPI) -> None:
        super().__init__()
        self.google_translate_api = google_translate_api
        self.deep_api = deep_api

    async def generate_image(self, achievement_text: str) -> Image:
        """Generates image from text using Google Translate API and Deep AI API

        Throws StickerGeneratorError if there were problems during invocation
            of either of these APIs
        """
        # Translate achievement text to english
        try:
            achievement_text_in_en = await self.google_translate_api.translate(achievement_text)
        except Exception as e:
            self.logger.error(str(e))
            raise StickerGeneratorError(
                "Problem appeared during Google Translate API invocation", "google-api", str(e)
            ) from e

        # Manipulate a prompt for better user experience
        prompt = (
            f'Create a humorous sticker representing the achievement of {achievement_text_in_en}. '
            f'The design should be in the form of a vector graphic with simple lines and a limited '
            f'color palette. The background should be white to emphasize the sticker format.'
            f'Make sticker circular and framed.')

        # Generate image from prompt
        try:
            image = await self.deep_api.generate_image(prompt)
        except Exception as e:
            self.logger.error(str(e))
            raise StickerGeneratorError(
                "Problem appeared during Deep AI API invocation", "deepai-api", str(e)
            ) from e

        return image
