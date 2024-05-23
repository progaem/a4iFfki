import re
import os
import httpx

from utils.exceptions import GoogleAPIError


class GoogleTranslateAPI:
    """This class handles all requests to the Google Translate API"""
    # Google translate API configuration
    GOOGLE_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2" # Google translate API
    GOOGLE_TRANSLATE_API_MAXIMUM_STRINGS = 128 # Maximum amount of strings to be allowed in Google translate API request
    GOOGLE_TRANSLATE_API_TIMEOUT = 60.0 # Timeout setting for Google translate API
    
    def __init__(self):
        self.api_key = os.environ['GOOGLE_TRANSLATE_API']
    
    async def translate(self, text_to_translate: str) -> str:
        """Translates original achievement text to english using Google translate API.
        
        Throws AssertionError if the request doesn't comply with API restrictions
        Throws GoogleAPIError if there were problems during Google API execution
        """
        
        # Required request checks according to Google translate API: https://cloud.google.com/translate/docs/reference/rest/v2/translate?hl=en#http-request
        assert text_to_translate.count('\n') < self.GOOGLE_TRANSLATE_API_MAXIMUM_STRINGS, f"Number of strings passed to v2/translate Google API shouldn't exceed {self.GOOGLE_TRANSLATE_API_MAXIMUM_STRINGS}"
        
        # TODO: add number of characters `len(achievement_message)` to pricing statistics
        # (free up to 500.000 per month, from 500.000 20$ every 1 mil characters)
        
        # Try invoking Google Translate API
        try:
            response = await self.__invoke_translate_api(text_to_translate)
            response.raise_for_status()
        # Handle exceptions
        except httpx.TimeoutException as e:
            raise GoogleAPIError("Timeout occurred while invoking Google Translate API", "timeout", str(e))
        except httpx.NetworkError as e:
            raise GoogleAPIError("Failed to establish connection with Google Translate API", "network", str(e))
        except Exception as e:
            raise GoogleAPIError("Unexpected error occurred while invoking Google Translate API", "other", str(e))
        else:
            # TODO: Add detected language `response['data']['translations']['detectedSourceLanguage']` to usage statistics
            translationsArray = response.json()['data']['translations']
            
            assert len(translationsArray) != 0, "Unable"
            
            translation = translationsArray[0]['translatedText']
            translation = re.sub(r'[^\w\s]', '', translation) # remove all non alphabetical symbols
            return translation

    async def __invoke_translate_api(self, text_to_translate: str) -> httpx.Response:
        """Wraper around Google Translate API"""
        async with httpx.AsyncClient() as client:
            return await client.post(
                    self.GOOGLE_TRANSLATE_URL,
                    data = {
                        'q': text_to_translate,
                        'target': 'en',
                        'key': self.api_key
                    },
                    timeout=self.GOOGLE_TRANSLATE_API_TIMEOUT
                )