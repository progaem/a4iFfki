from enum import Enum
import io
import math
import random

from PIL import Image, ImageDraw, ImageFont

from common.common import BaseClass
from sticker.generator import StickerGenerator
from storage.s3 import ImageS3Storage

class StickerType(Enum):
    EMPTY = 1
    ACHIEVEMENT = 2
    DESCRIPTION = 3
    PROFILE = 4
    PROFILE_DESCRIPTION = 5

class StickerArtist(BaseClass):
    WIDTH = 512
    HEIGHT = 512
    BACKGROUND_COLOR = (255, 255, 255, 0)  # Transparent background
    DEFAULT_CIRCLE_COLOR = (125, 125, 125, 255)  # Gray circle with alpha channel
    CIRCLE_COLOR = (255, 255, 255, 255)  # White circle with alpha channel
    TEXT_COLOR = (0, 0, 0)  # Black text
    OUTER_GROUP_STICKER_COLOR = (255, 255, 255)  # Color at the center
    INNER_GROUP_STICKER_COLOR = (181, 89, 163)  # Color at the center
    NUMBER_FONT_SIZE = 40  # Font size for number on the bottom of the sticker
    STICKER_ARC_MARGIN = 0.95  # Margin for arc that wraps group sticker
    STICKER_ARC_WIDTH = 10  # Width of the arc
    FONT_SIZE = 30  # TODO: make a range
    FONT_PATH = "../resources/GothamProBlack.ttf"
    # With {FONT_SIZE}, the maximum characters that would fit into line without new spaces
    MAX_SYMBOLS_IN_LINE = 25
    EMPTY_STICKER_PATH = "sticker_files/empty.png"

    def __init__(self, sticker_file_manager: ImageS3Storage, sticker_generator: StickerGenerator):
        super().__init__()
        self.sticker_file_manager = sticker_file_manager
        self.sticker_generator = sticker_generator

    def get_empty_sticker(self) -> tuple[str, bytes]:
        """Gets an empty achievement sticker"""
        try:
            file_bytes = self.sticker_file_manager.get_bytes_from_path(self.EMPTY_STICKER_PATH)
            return self.EMPTY_STICKER_PATH, file_bytes
        except FileNotFoundError:
            return self.__generate_empty_sticker()

    def draw_description_sticker(self, description: str) -> tuple[str, bytes]:
        """Draws a description sticker for achievement"""
        # Choosing pleasant color palette
        red_color = random.randint(60, 170)
        green_color = random.randint(60, 170)
        blue_color = random.randint(60, 170)

        image = self.__generate_sticker_of_gradient(
            (red_color, green_color, blue_color),
            self.OUTER_GROUP_STICKER_COLOR
        )
        image = self.__add_text_on_sticker(image, description, 0)
        return self.sticker_file_manager.save_and_convert_to_bytes(image)

    def draw_chat_description_sticker(
        self,
        description: str,
        number_of_people_achieved: int
    ) -> tuple[str, bytes]:
        """Draws a description sticker for achievement with number of people achieved it"""
        image = self.__generate_sticker_of_gradient(
            self.INNER_GROUP_STICKER_COLOR,
            self.OUTER_GROUP_STICKER_COLOR
        )
        image = self.__add_number_with_arc_on_sticker(image, number_of_people_achieved)
        image = self.__add_text_on_sticker(image, description, 2 * (1 - self.STICKER_ARC_MARGIN))
        return self.sticker_file_manager.save_and_convert_to_bytes(image)

    async def draw_sticker_from_prompt(self, prompt: str) -> tuple[str, bytes]:
        """Draws a achievement sticker from prompt"""
        # Note: during local development you can change it to
        # image = self.__generate_sticker_of_random_color()
        # image = self.__add_text_on_sticker(image, f"picture about {prompt}", 0)
        image = await self.sticker_generator.generate_image(prompt)
        return self.sticker_file_manager.save_and_convert_to_bytes(image)

    def draw_sticker_from_profile_picture(self, image: bytes) -> tuple[str, bytes]:
        """Draws a sticker from profile picture"""
        image = Image.open(io.BytesIO(image))
        image = self.__expand2square(
            image,
            self.CIRCLE_COLOR
        ).resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)
        image = self.__mask_circle_transparent(image)
        return self.sticker_file_manager.save_and_convert_to_bytes(image)

    def draw_sticker_from_username(self, username: str) -> tuple[str, bytes]:
        """Draws a sticker from username"""
        image = self.__generate_sticker_of_random_color()
        image = self.__add_text_on_sticker(image, username, 0)
        return self.sticker_file_manager.save_and_convert_to_bytes(image)

    def draw_persons_stickerset_description_sticker(
        self,
        username: str,
        chat_name: str
    ) -> tuple[str, bytes]:
        """Draws description sticker for persons stickerset"""
        description = f"Stickerset of @{username}'s achievements for chat \'{chat_name}\'"
        # TODO: make number the place in total amount of achievements in group
        return self.draw_chat_description_sticker(description, 1)

    def __generate_empty_sticker(self) -> tuple[str, bytes]:
        image = self.__generate_sticker_of_color(self.DEFAULT_CIRCLE_COLOR)
        return self.sticker_file_manager.save_and_convert_to_bytes(image, self.EMPTY_STICKER_PATH)

    def __expand2square(self, image: Image, background_color) -> Image:
        width, height = image.size
        if width == height:
            return image
        if width > height:
            result = Image.new(image.mode, (width, width), background_color)
            result.paste(image, (0, (width - height) // 2))
            return result
        else:
            result = Image.new(image.mode, (height, height), background_color)
            result.paste(image, ((height - width) // 2, 0))
            return result

    def __mask_circle_transparent(self, image: Image) -> Image:
        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)

        result = image.copy()
        result.putalpha(mask)

        return result

    def __generate_sticker_of_random_color(self) -> Image:
        # Choosing pleasant color palette
        red_color = random.randint(80, 200)
        green_color = random.randint(80, 200)
        blue_color = random.randint(80, 200)

        return self.__generate_sticker_of_color((red_color, green_color, blue_color, 255))

    def __generate_sticker_of_color(self, color) -> Image:
        image = Image.new("RGBA", (self.WIDTH, self.HEIGHT), self.BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)

        circle_position = (self.WIDTH // 2, self.HEIGHT // 2)
        circle_radius = min(self.WIDTH, self.HEIGHT) // 2
        draw.ellipse(
            (circle_position[0] - circle_radius, circle_position[1] - circle_radius,
             circle_position[0] + circle_radius, circle_position[1] + circle_radius),
            fill=color
        )
        return image

    def __generate_sticker_of_gradient(self, inner_color, outer_color) -> Image:
        image = Image.new("RGBA", (self.WIDTH, self.HEIGHT), self.BACKGROUND_COLOR)

        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                # Find the distance to the center
                distance_to_center = math.sqrt(
                    (x - self.WIDTH / 2) ** 2 + (y - self.HEIGHT / 2) ** 2)

                # Make it on a scale from 0 to 1
                distance_to_center = float(distance_to_center) / (math.sqrt(2) * self.WIDTH / 2)

                # Calculate r, g, and b values
                r = outer_color[0] * distance_to_center + inner_color[0] * (1 - distance_to_center)
                g = outer_color[1] * distance_to_center + inner_color[1] * (1 - distance_to_center)
                b = outer_color[2] * distance_to_center + inner_color[2] * (1 - distance_to_center)

                # Place the pixel
                x_to_center = x - self.WIDTH / 2
                y_to_center = y - self.HEIGHT / 2
                squares_sum = x_to_center * x_to_center + y_to_center * y_to_center
                if squares_sum <= self.WIDTH * self.WIDTH / 4:
                    image.putpixel((x, y), (int(r), int(g), int(b)))

        return image

    def __add_text_on_sticker(self, image: Image, text: str, margin_to_leave: float) -> Image:
        description = self.__adapt_text_to_fit_circle(text, margin_to_leave)
        font = ImageFont.truetype(self.FONT_PATH, self.FONT_SIZE)

        draw = ImageDraw.Draw(image)
        textbbox_val = draw.textbbox((0, 0), description, font=font)
        text_width = textbbox_val[2] - textbbox_val[0]
        text_height = textbbox_val[3] - textbbox_val[1]
        text_position = ((self.WIDTH - text_width) // 2, (self.HEIGHT - text_height) // 2)

        draw.text(text_position, description, fill=self.TEXT_COLOR, font=font)
        return image

    def __add_number_with_arc_on_sticker(self, image: Image, number: int) -> Image:
        draw = ImageDraw.Draw(image)

        # drawing arc part
        draw.arc(
            [
                self.HEIGHT * (1 - self.STICKER_ARC_MARGIN),
                self.WIDTH * (1 - self.STICKER_ARC_MARGIN),
                self.HEIGHT * self.STICKER_ARC_MARGIN,
                self.WIDTH * self.STICKER_ARC_MARGIN
            ],
            start=110,
            end=70,
            fill=self.TEXT_COLOR,
            width=self.STICKER_ARC_WIDTH)

        # drawing number_part
        font = ImageFont.truetype(self.FONT_PATH, self.NUMBER_FONT_SIZE)

        textbbox_val = draw.textbbox((0, 0), str(number), font=font)
        text_width = textbbox_val[2] - textbbox_val[0]
        text_height = textbbox_val[3] - textbbox_val[1]
        text_position = (
            (self.WIDTH - text_width) // 2,
            self.HEIGHT * self.STICKER_ARC_MARGIN - text_height
        )

        draw.text(text_position, str(number), fill=self.TEXT_COLOR, font=font)
        return image

    def __adapt_text_to_fit_circle(self, description: str, margin_to_leave: float) -> str:
        """adapt text to fit in the circle"""
        max_symbols = self.MAX_SYMBOLS_IN_LINE * (1 - margin_to_leave)
        if len(description) > max_symbols:
            words = description.split(' ')
            # greedy algo
            count = 0
            description = ""
            for word in words:
                count = count + len(word) + 1
                if count > max_symbols:
                    count = len(word) + 1
                    # because it's a circle each time max number of symbols shrinks
                    max_symbols = max_symbols - 2
                    description += f"\n{word} "
                else:
                    description += word + " "
        return description
