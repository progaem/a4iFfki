import logging
import os

from PIL import Image
from api.deepai import DeepAIAPI
from api.translate import GoogleTranslateAPI
from utils.exceptions import StickerGeneratorError

# Enable logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StickerGenerator:
    """Class that handles the process of creating a sticker from prompt, through utilizing DeepAI and Google Translate API"""
    
    def __init__(self, google_translate_api: GoogleTranslateAPI, deep_api: DeepAIAPI) -> None:
        self.google_translate_api = google_translate_api
        self.deep_api = deep_api
    
    async def generate_image(self, achievement_text: str) -> Image:
        """Generates image from text using Google Translate API and Deep AI API
        
        Throws StickerGeneratorError if there were problems during invocation of either of these APIs
        """
        # Translate achievement text to english
        try:
            achievement_text_in_en = await self.google_translate_api.translate(achievement_text)
        except Exception as e:
            logger.error(str(e))
            raise StickerGeneratorError("Problem appeared during Google Translate API invocation", "google-api", str(e))
        
        # Manipulate a prompt for better user experience
        prompt = f'Create a humorous sticker representing the achievement of {achievement_text_in_en}. The design should be in the form of a vector graphic with simple lines and a limited color palette. Include a symbolic element, like a trophy, to signify the achievement. The background should be white to emphasize the sticker format'
        
        # Generate image from prompt
        try:
            image = await self.deep_api.generate_image(prompt)
        except Exception as e:
            raise StickerGeneratorError("Problem appeared during Deep AI API invocation", "deepai-api", str(e))

        return image