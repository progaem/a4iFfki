from PIL import Image, ImageDraw, ImageFont
import io
import math
import random
import string


class StickerGenerator:
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
    FONT_PATH = "data/resources/GothamProBlack.ttf"
    # With default font size {FONT_SIZE}, the maximum characters that would fit into line without new spaces
    MAX_SYMBOLS_IN_LINE = 25
    EMPTY_STICKER_PATH = "data/stickers/empty.png"

    def __init__(self):
        pass

    def get_empty_sticker(self) -> tuple[str, bytes]:
        """Gets already generated empty achievement sticker"""
        try:
            with open(self.EMPTY_STICKER_PATH, 'rb') as file:
                file_bytes = file.read()
            return self.EMPTY_STICKER_PATH, file_bytes
        except FileNotFoundError:
            return self.__generate_empty_sticker()

    def __generate_empty_sticker(self) -> tuple[str, bytes]:
        """Generates empty achievement sticker"""
        image = self.__generate_sticker_of_color(self.DEFAULT_CIRCLE_COLOR)
        return self.__save_and_convert_to_bytes(image, self.EMPTY_STICKER_PATH)

    def generate_description_sticker(self, description: str) -> tuple[str, bytes]:
        """Generates description sticker for achievement sticker"""
        image = self.__generate_sticker_of_color(self.CIRCLE_COLOR)
        image = self.__add_text_on_sticker(image, description, 0)
        return self.__save_and_convert_to_bytes(image)

    def generate_group_chat_description_sticker(self, description: str, number_of_people_achieved: int) -> tuple[str, bytes]:
        """Generates description sticker for achievement sticker with number of people achieved it"""
        image = self.__generate_sticker_of_gradient(self.INNER_GROUP_STICKER_COLOR, self.OUTER_GROUP_STICKER_COLOR)
        image = self.__add_number_with_arc_on_sticker(image, number_of_people_achieved)
        image = self.__add_text_on_sticker(image, description, 2 * (1 - self.STICKER_ARC_MARGIN))
        return self.__save_and_convert_to_bytes(image)

    # TODO: implement
    def generate_sticker_from_prompt(self, prompt: str) -> tuple[str, bytes]:
        """Generates sticker from prompt"""
        return self.generate_description_sticker("чето нагенереное нейросетью")

    # TODO: implement
    def generate_sticker_with_profile_picture(self, image: Image) -> tuple[str, bytes]:
        """Generates sticker from profile picture"""
        # TODO: crop image to circle of certain size
        #  https://note.nkmk.me/en/python-pillow-square-circle-thumbnail/
        #  or this https://stackoverflow.com/questions/51486297/cropping-an-image-in-a-circular-way-using-python
        image.resize(self.WIDTH, self.HEIGHT)
        return self.__save_and_convert_to_bytes(image)

    # TODO: make fancier
    def generate_sticker_with_profile_description(self, profile_name: str, group_name: str) -> tuple[str, bytes]:
        """Generates profile description sticker from profile name and group name"""
        description = f"Это стикерпак ачивок @{profile_name} для группы {group_name}"
        # TODO: make number the place in total amount of achievements in group
        return self.generate_group_chat_description_sticker(description, 1)

    @staticmethod
    def __save_and_convert_to_bytes(image: Image, file_path: str = "") -> tuple[str, bytes]:
        """Conversion to bytes"""
        # code taken from https://jdhao.github.io/2019/07/06/python_opencv_pil_image_to_bytes/
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        byte_image = buf.getvalue()

        if not file_path:
            file_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            file_path = f"data/stickers/{file_name}.png"
        with open(file_path, "wb") as binary_file:
            binary_file.write(byte_image)
        return file_path, byte_image

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
                distance_to_center = math.sqrt((x - self.WIDTH / 2) ** 2 + (y - self.HEIGHT / 2) ** 2)

                # Make it on a scale from 0 to 1
                distance_to_center = float(distance_to_center) / (math.sqrt(2) * self.WIDTH / 2)

                # Calculate r, g, and b values
                r = outer_color[0] * distance_to_center + inner_color[0] * (1 - distance_to_center)
                g = outer_color[1] * distance_to_center + inner_color[1] * (1 - distance_to_center)
                b = outer_color[2] * distance_to_center + inner_color[2] * (1 - distance_to_center)

                # Place the pixel
                x_to_center = x - self.WIDTH / 2
                y_to_center = y - self.HEIGHT / 2
                if x_to_center * x_to_center + y_to_center * y_to_center <= self.WIDTH * self.WIDTH / 4:
                    image.putpixel((x, y), (int(r), int(g), int(b)))

        return image

    def __add_text_on_sticker(self, image: Image, text: str, margin_to_leave: float) -> Image:
        description = self.__adapt_text_to_fit_circle(text, margin_to_leave)
        # TODO: understand how many words we can fit in the circle and throw an error on the bot level
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
        text_position = ((self.WIDTH - text_width) // 2, self.HEIGHT * self.STICKER_ARC_MARGIN - text_height)

        draw.text(text_position, str(number), fill=self.TEXT_COLOR, font=font)
        return image

    # TODO: experiment with changing font size
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
                    max_symbols = max_symbols - 2  # because it's a circle each time max number of symbols shrinks
                    description += f"\n{word} "
                else:
                    description += word + " "
        return description

