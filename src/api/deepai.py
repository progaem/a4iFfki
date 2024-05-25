import httpx
import os

from PIL import Image
from io import BytesIO
from common.exceptions import DeepAIAPIError


class DeepAIAPI:
    """This class handles all requests to the Deep AI API"""
    # Deep AI API configuration
    DEEP_AI_URL = "https://api.deepai.org/api/text2img" # Deep AI API
    DEEP_AI_API_TIMEOUT = 60.0 # Timeout setting for Deep AI API
    
    def __init__(self):
        self.api_key = os.environ['DEEPAI_API_TOKEN']
    
    async def generate_image(self, prompt: str) -> Image:
        """Generates an image from english prompt using Google translate API
        
        Throws AssertionError if the request doesn't comply with API restrictions
        Throws DeepAIAPIError if there were problems during Deep AI API execution
        """
        
        # all charaters in the prompt should be ascii characters
        assert all(ord(character) < 128 for character in prompt), "All symbols passed to Deep AI API request should be ASCII characters"

        # TODO: add pricing statistics every 500 calls per month for $5
        
        # Try invoking Deep AI API
        try:
            response = await self.__invoke_generate_image_api(prompt)
            response.raise_for_status()
        # Handle exceptions
        except httpx.TimeoutException as e:
            raise DeepAIAPIError("Timeout occurred while invoking Deep AI API", "generate-timeout", str(e))
        except httpx.NetworkError as e:
            raise DeepAIAPIError("Failed to establish connection with Deep AI API", "generate-network", str(e))
        except Exception as e:
            raise DeepAIAPIError("Unexpected error occurred while invoking Deep AI API", "generate-other", str(e))
        else:
            # Fetch the link to the generated image
            image_url = response.json()['output_url']
            
            # Try downloading the generated image
            try:
                image = await self.__invoke_download_image_api(image_url)
                image.raise_for_status()
            # Handle exceptions
            except httpx.TimeoutException as e:
                raise DeepAIAPIError("Timeout occurred while fetching generated image from Deep AI API", "download-timeout", str(e))
            except httpx.NetworkError as e:
                raise DeepAIAPIError("Failed to establish connection with Deep AI API while fetching generated image", "download-network", str(e))
            except Exception as e:
                raise DeepAIAPIError("Unexpected error occurred while invoking Deep AI API while fetching generated image", "download-other", str(e))
            else:
                # Convert donwloaded image to bytes
                image = Image.open(BytesIO(image.content))
                return image

    async def __invoke_generate_image_api(self, prompt: str) -> httpx.Response:
        """Wraper around Deep AI API"""
        async with httpx.AsyncClient() as client:
            return await client.post(
                self.DEEP_AI_URL,
                data = {
                    'text': prompt,
                    'image_generator_version': 'hd',
                    'width': '512',
                    'height': '512',
                    'grid_size': '1', 
                },
                headers={'api-key': self.api_key},
                timeout=60.0
            )
    
    async def __invoke_download_image_api(self, image_url: str) -> httpx.Response:
        """Wrapper around call to fetch image from url"""
        async with httpx.AsyncClient() as client:
            return await client.get(image_url)