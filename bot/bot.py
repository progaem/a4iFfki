#!/usr/bin/env python
import logging
import os
import random
import string

from telegram import Update, InputSticker
from telegram.constants import StickerFormat
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
import telegram.ext.filters as filters

from utils.utils import masked_print
from db.db_manager import DbManager, ChatSticker
from prompt.prompt_detector import PromptDetector
from sticker.sticker_generator import StickerGenerator

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class Bot:
    TELELGRAM_BOT_NAME = "a4iFfki"
    ACHIEVEMENT_EMOJI = "🥇"

    def __init__(self, db_manager: DbManager, prompt_detector: PromptDetector, sticker_generator: StickerGenerator):
        telegram_token = os.environ['TELEGRAM_BOT_TOKEN']
        self.application = Application.builder().token(telegram_token).build()

        logger.info("Telegram application was started with %s", masked_print(telegram_token))

        self.db_manager = db_manager
        self.prompt_detector = prompt_detector
        self.sticker_generator = sticker_generator

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Send a description of the bot when the command /start is issued."""
        await update.message.reply_text("TODO: write meaningful description of the bot")

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send a FAQ with short description of commands when the command /help is issued."""
        await update.message.reply_text("TODO: write meaningful description of the bot")

    async def on_give(self, update: Update, context: CallbackContext) -> None:
        """Send an achievement when person replied to someone."""
        message_text = update.message.text
        chat_id = update.message.chat_id
        chat_name = update.effective_chat.effective_name
        user_id = update.message.from_user.id

        if not update.message.reply_to_message:
            logger.info(f"{user_id} in {chat_id} mentioned выдаю ачивку, but it wasn't reply")
            return

        replied_user_id = update.message.reply_to_message.from_user.id
        replied_user_username = update.message.reply_to_message.from_user.username

        prompt = self.prompt_detector.detect(message_text)
        if not prompt:
            await update.message.reply_text(
                f'User {user_id} in {chat_id} chat mentioned \'выдаю ачивку\' to {replied_user_id}! But prompt was not identified :C')

        self.db_manager.save_prompt_message(chat_id, user_id, replied_user_id, message_text, prompt)

        achievement_sticker = self.sticker_generator.generate_sticker_from_prompt(prompt)
        user_description_sticker = self.sticker_generator.generate_description_sticker(prompt)
        chat_description_sticker = self.sticker_generator.generate_group_chat_description_sticker(prompt, 1)

        await self.add_chat_stickers(user_id, chat_id, chat_name, achievement_sticker, chat_description_sticker, context)

        await self.add_user_stickers(replied_user_id, replied_user_username, chat_id, chat_name, achievement_sticker, user_description_sticker, context)

        # TODO: reply with recently created user sticker
        await update.message.reply_text(
            f'User {user_id} in {chat_id} chat mentioned \'выдаю ачивку\' to {replied_user_id}! Possible prompt: {prompt}')

    # TODO: fix this method
    #  as of 05/11 it's throwing telegram.error.BadRequest: Peer_id_invalid exceptions when trying to create stickerset
    async def add_chat_stickers(self, called_user_id: int, chat_id: int, chat_name: str, achievement_sticker: tuple[str, bytes], chat_description_sticker: tuple[str, bytes], context: CallbackContext) -> None:
        """Adds new achievement stickers to the chat sticker pack"""
        # TODO: remove this return to continue investigations
        return

        bot = context.bot
        chat_sticker_pack = self.db_manager.get_chat_sticker_pack_name(chat_id)
        if not chat_sticker_pack:
            empty_sticker = self.sticker_generator.get_empty_sticker()
            # achievement, 4 empty stickers, description, 4 empty stickers
            stickers_to_add = [
                achievement_sticker,
                empty_sticker,
                empty_sticker,
                empty_sticker,
                empty_sticker,
                chat_description_sticker,
                empty_sticker,
                empty_sticker,
                empty_sticker,
                empty_sticker
            ]

            created_stickers = list(map(lambda sticker: InputSticker(sticker[1], [self.ACHIEVEMENT_EMOJI]), stickers_to_add))

            sticker_pack_name = self.__create_random_sticker_pack_name("chat")
            sticker_pack_title = f"Achievements for '{chat_name}"[:62] + "'"
            await bot.create_new_sticker_set(called_user_id, sticker_pack_name, sticker_pack_title, created_stickers, StickerFormat.STATIC)

            sticker_set = await bot.get_sticker_set(sticker_pack_name)

            await bot.send_sticker(chat_id, sticker_set.stickers[0])

            chat_stickers_to_update = []
            for i, sticker in enumerate(sticker_set.stickers):
                sticker_type = "empty"
                times_achieved = None
                if i == 0:
                    sticker_type = "achievement"
                    times_achieved = 1
                elif i == 5:
                    sticker_type = "description"

                chat_stickers_to_update.append(
                    ChatSticker(
                        sticker.file_id,
                        sticker.file_unique_id,
                        sticker_type,
                        times_achieved,
                        i,
                        chat_id,
                        sticker_pack_name,
                        called_user_id,
                        stickers_to_add[i][0]
                    )
                )
            self.db_manager.create_stickers(chat_stickers_to_update)
        # else: get index index_of_the_last_not_element
        # TODO: if group doesn't have a sticker pack
        #  - create it with 10 stickers (2 achievements, 8 empty)
        #  else:
        #    - if number of group stickers % 10, add new ones and 8 empty ones (achievement - 4 empty - description - 4 empty)
        #    - else find the index of the first empty ones and replace empty ones in the sticker pack

        # TODO: get the sticker pack by name
        #  - update (sticker_id - type - achievements_count - index_in_sticker_pack - file_path - group_id - group_sticker_pack_name) table
        #  (type: achievement/description/empty)

    async def add_user_stickers(self, user_id: int, user_name: str, chat_id: int, chat_name: str, achievement_sticker: tuple[str, bytes], user_description_sticker: tuple[str, bytes], context: CallbackContext) -> None:
        """Adds new achievement stickers to the user sticker pack"""
        # TODO: if person doesn't have a sticker pack
        #  - get person's alias
        #  - generate profile picture sticker
        #  - generate profile description sticker
        #  - create sticker pack with 10 new stickers (6 empty, 2 profile sticker, 2 achievements sticker)
        #  else:
        #  - if person has number stickers % 10 -- just add new ones and then 8 empty ones
        #  - else find the index of the first empty ones and replace empty ones in the sticker pack

        # TODO: get the persons sticker pack by name
        #  - update (sticker_id - type - index_in_sticker_pack - file_path - user_id - group_id - sticker_pack_name ) table
        #  (type: achievement/description/profile/profile_description/empty)
        pass

    def __create_random_sticker_pack_name(self, prefix_name: str):
        # As per telegram API documentation https://docs.python-telegram-bot.org/en/v20.6/telegram.bot.html#telegram.Bot.create_new_sticker_set:
        # Stickerpack name can contain only english letters, digits and underscores.
        # Must begin with a letter, can’t contain consecutive underscores and must end in “_by_<bot username>”. <bot_username> is case insensitive.
        # 1 - 64 characters.
        if not prefix_name or not prefix_name[0].isalpha():
            raise ValueError('Sticker pack should start with letter')
        sticker_pack_name_length = 16
        sticker_pack_name_to_generate = sticker_pack_name_length - len(prefix_name)
        sticker_pack_prefix = ''.join(
            random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=sticker_pack_name_to_generate))
        return f"{prefix_name}{sticker_pack_prefix}_by_{self.TELELGRAM_BOT_NAME}"

    def run(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))

        self.application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.Regex('выдаю ачивку'), self.on_give))
        # TODO: implement sticker replies
        #  self.application.add_handler(MessageHandler(filters.reply & filters.sticker, handle_sticker_replies))
        # TODO: implement notification message (if triggered, send a notification to all channels it was send to)

        # Run the bot until the user presses Ctrl-C
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
