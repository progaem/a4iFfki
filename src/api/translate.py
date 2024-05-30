"""
This module handles Google Translate API management.
"""
import re
import os
import httpx

from common.common import BaseClass
from common.exceptions import GoogleAPIError


class GoogleTranslateAPI(BaseClass):
    """This class handles all requests to the Google Translate API"""
    GOOGLE_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
    GOOGLE_TRANSLATE_API_MAXIMUM_STRINGS = 128
    GOOGLE_TRANSLATE_API_TIMEOUT = 60.0

    def __init__(self):
        self.api_key = os.environ['GOOGLE_TRANSLATE_API']

    async def translate(self, text_to_translate: str) -> str:
        """Translates original achievement text to english using Google translate API.
        
        Throws AssertionError if the request doesn't comply with API restrictions
        Throws GoogleAPIError if there were problems during Google API execution
        """

        # Required request checks according to Google translate API:
        # https://cloud.google.com/translate/docs/reference/rest/v2/translate?hl=en#http-request
        assert (
            text_to_translate.count('\n') < self.GOOGLE_TRANSLATE_API_MAXIMUM_STRINGS
        ), (
            f"Number of strings passed to v2/translate Google API shouldn't exceed "
            f"{self.GOOGLE_TRANSLATE_API_MAXIMUM_STRINGS}"
        )

        # pylint: disable=fixme
        # TODO: add number of characters `len(achievement_message)` to pricing statistics
        # (free up to 500.000 per month, from 500.000 20$ every 1 mil characters)

        # Try invoking Google Translate API
        try:
            response = await self.__invoke_translate_api(text_to_translate)
            response.raise_for_status()
        # Handle exceptions
        except httpx.TimeoutException as e:
            raise GoogleAPIError(
                "Timeout occurred while invoking Google Translate API", "timeout", str(e)
            ) from e
        except httpx.NetworkError as e:
            raise GoogleAPIError(
                "Failed to establish connection with Google Translate API", "network", str(e)
            ) from e
        except Exception as e:
            raise GoogleAPIError(
                "Unexpected error occurred while invoking Google Translate API", "other", str(e)
            ) from e
        # pylint: disable=fixme
        # TODO: Add detected language `response['data']['translations']['detectedSourceLanguage']` to usage statistics
        translations_array = response.json()['data']['translations']

        assert len(translations_array) != 0, "Unable"

        translation = translations_array[0]['translatedText']
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
