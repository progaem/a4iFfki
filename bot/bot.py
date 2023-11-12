#!/usr/bin/env python
import logging
import os
import random
import string

from telegram import Update, InputSticker
from telegram._bot import BT
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
    ACHIEVEMENT_EMOJI = "🥇"

    def __init__(self, db_manager: DbManager, prompt_detector: PromptDetector, sticker_generator: StickerGenerator):
        self.telgram_bot_name = os.environ['TELEGRAM_BOT_NAME']

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
        bot = context.bot
        message_text = update.message.text
        chat_id = update.message.chat_id
        chat_name = update.effective_chat.effective_name
        user_id = update.message.from_user.id

        if not update.message.reply_to_message:
            logger.info(f"{user_id} in {chat_id} mentioned выдаю ачивку, but it wasn't reply")
            return

        replied_user_id = update.message.reply_to_message.from_user.id
        replied_user_username = update.message.reply_to_message.from_user.username
        logger.info(f"{user_id} in {chat_id} mentioned выдаю ачивку replying to {replied_user_id} message")

        prompt = self.prompt_detector.detect(message_text)
        if not prompt:
            await update.message.reply_text(
                f'User {user_id} in {chat_id} chat mentioned \'выдаю ачивку\' to {replied_user_id}! But prompt was not identified :(')

        self.db_manager.save_prompt_message(chat_id, user_id, replied_user_id, message_text, prompt)

        achievement_sticker = self.sticker_generator.generate_sticker_from_prompt(prompt)
        chat_description_sticker = self.sticker_generator.generate_group_chat_description_sticker(prompt, 1)
        user_profile_sticker = await self.__create_profile_sticker(bot, replied_user_id, replied_user_username)
        user_description_sticker = self.sticker_generator.generate_description_sticker(prompt)

        # TODO: take sticker admin user id
        # TODO: paste here your username if you have premium account
        stickers_owner_id = 249427415
        file_id = await self.add_chat_stickers(stickers_owner_id, chat_id, chat_name, achievement_sticker, chat_description_sticker, context)

        await bot.send_sticker(chat_id, file_id)

        logger.info("Starting to add new stickers to user sticker set")
        await self.add_user_stickers(replied_user_id, replied_user_username, chat_id, chat_name, achievement_sticker, user_description_sticker, context)

        # TODO: reply with recently created user sticker
        await update.message.reply_text(
            f'User {user_id} in {chat_id} chat mentioned \'выдаю ачивку\' to {replied_user_id}! Possible prompt: {prompt}')

    async def add_chat_stickers(
            self,
            stickers_owner: int,
            chat_id: int,
            chat_name: str,
            achievement_sticker: tuple[str, bytes],
            chat_description_sticker: tuple[str, bytes],
            context: CallbackContext) -> str:
        """Adds new achievement stickers to the chat sticker pack and returns the file_id of the achievement sticker"""
        # since the sticker pack was just created, the last achievement id is 0
        last_achievement_index = 0
        stickers_to_add = dict()
        chat_sticker_set_name = ""

        bot = context.bot
        (chat_stickers, session) = self.db_manager.get_chat_sticker_set(chat_id)
        logger.info(f"Chat stickers found in {chat_name}: {chat_stickers}")
        # if chat sticker pack is not created - create it with all the stickers we want to create
        if not chat_stickers:
            # define stickers to create: achievement, 4 empty stickers, description, 4 empty stickers
            logger.info(f"Chat sticker set for chat {chat_name} was not initialized. Trying to initialize it...")
            empty_sticker = self.sticker_generator.get_empty_sticker()
            stickers_to_add = {
                0: achievement_sticker,
                1: empty_sticker,
                2: empty_sticker,
                3: empty_sticker,
                4: empty_sticker,
                5: chat_description_sticker,
                6: empty_sticker,
                7: empty_sticker,
                8: empty_sticker,
                9: empty_sticker
            }
            created_stickers = list(map(lambda sticker: InputSticker(sticker[1], [self.ACHIEVEMENT_EMOJI]), stickers_to_add.values()))

            # create a new sticker pack with previously defined stickers
            chat_sticker_set_name = self.__create_random_sticker_pack_name("chat")
            sticker_pack_title = f"Achievements for '{chat_name}"[:62] + "'"
            await bot.create_new_sticker_set(stickers_owner, chat_sticker_set_name, sticker_pack_title, created_stickers, StickerFormat.STATIC)
            logger.info(f"New sticker set was created under name {chat_sticker_set_name} and assigned owner {stickers_owner}")
        else:
            chat_sticker_set_name = chat_stickers[0].chat_sticker_pack_name
            last_achievement_index = len(list(filter(lambda sticker: sticker.type == "achievement", chat_stickers))) - 1
            logger.info(
                f"Sticker set was created under name {chat_sticker_set_name} already existed, the index of the last achievement sticker is {last_achievement_index}")
            # if number of achievements is % 5, we need to create new empty stickers
            if last_achievement_index % 5 == 4:
                logger.info(f"Number of achievement stickers in the {chat_sticker_set_name} sticker set is a multiple of 5. Trying to 10 stickers to the sticker set (including empty ones)")
                empty_sticker = self.sticker_generator.get_empty_sticker()
                last_sticker_index = last_achievement_index + 5
                last_achievement_index = last_achievement_index + 5
                stickers_to_add = {
                    last_sticker_index + 1: achievement_sticker,
                    last_sticker_index + 2: empty_sticker,
                    last_sticker_index + 3: empty_sticker,
                    last_sticker_index + 4: empty_sticker,
                    last_sticker_index + 5: empty_sticker,
                    last_sticker_index + 6: chat_description_sticker,
                    last_sticker_index + 7: empty_sticker,
                    last_sticker_index + 8: empty_sticker,
                    last_sticker_index + 9: empty_sticker,
                    last_sticker_index + 10: empty_sticker
                }

                # add stickers to the stickers
                for i, sticker in stickers_to_add.items():
                    await bot.add_sticker_to_set(stickers_owner, chat_sticker_set_name,  InputSticker(sticker[1], [self.ACHIEVEMENT_EMOJI]))
                    logger.info(f"Successfully added sticker number {i} to the sticker set {chat_sticker_set_name} located at the path {sticker[0]}")
            else:
                logger.info(
                    f"Number of achievement stickers in the {chat_sticker_set_name} sticker set is NOT a multiple of 5 (It's {last_achievement_index}). Trying to add new stickers in place of others")
                stickers_to_add = {
                    last_achievement_index + 1: achievement_sticker,
                    last_achievement_index + 6: chat_description_sticker
                }
                # delete two empty stickers next to last achievement and description stickers (the last sticker deleted first so indices of earlier stickers won't change)
                await bot.delete_sticker_from_set(chat_stickers[last_achievement_index + 6].file_id)
                await bot.delete_sticker_from_set(chat_stickers[last_achievement_index + 1].file_id)
                logger.info(f"Two empty stickers in the {chat_sticker_set_name} sticker set were deleted")

                # add new stickers to the sticker set
                await bot.add_sticker_to_set(stickers_owner, chat_sticker_set_name,
                                             InputSticker(achievement_sticker[1], [self.ACHIEVEMENT_EMOJI]))
                await bot.add_sticker_to_set(stickers_owner, chat_sticker_set_name,
                                             InputSticker(chat_description_sticker[1], [self.ACHIEVEMENT_EMOJI]))
                logger.info(f"Two new stickers (located at {achievement_sticker[0]} and {chat_description_sticker[0]}) were added at the end of {chat_sticker_set_name} sticker set")

                # set the achievement stickers next to the previous ones (the first sticker should be added first)
                sticker_set = await bot.get_sticker_set(chat_sticker_set_name)
                achievement_sticker_id = sticker_set.stickers[-2].file_id
                chat_description_sticker_id = sticker_set.stickers[-1].file_id
                await bot.set_sticker_position_in_set(achievement_sticker_id, last_achievement_index + 1)
                await bot.set_sticker_position_in_set(chat_description_sticker_id, last_achievement_index + 6)
                logger.info(f"New stickers were set at the positions {last_achievement_index + 1} and {last_achievement_index + 6} in the {chat_sticker_set_name} sticker set")

            last_achievement_index = last_achievement_index + 1

        # get the updated sticker set from telegram (needed to get file_id and file_unique_id for each sticker)
        sticker_set = await bot.get_sticker_set(chat_sticker_set_name)
        logger.info(f"Fetching the newly created {chat_sticker_set_name} sticker set")

        # update stickers in the database
        chat_stickers_to_update = []
        for sticker_index, sticker_file in stickers_to_add.items():
            sticker = sticker_set.stickers[sticker_index]
            sticker_type = "empty"
            times_achieved = None
            # each first line of stickers that comes before last achievement are achievements
            if sticker_index % 10 < 5 and sticker_index <= last_achievement_index:
                sticker_type = "achievement"
                times_achieved = 1
            # each second line of stickers that comes before last achievement's description are descriptions
            elif sticker_index % 10 >= 5 and sticker_index <= last_achievement_index + 5:
                sticker_type = "description"
            chat_stickers_to_update.append(
                ChatSticker(
                    file_id=sticker.file_id,
                    file_unique_id=sticker.file_unique_id,
                    type=sticker_type,
                    times_achieved=times_achieved,
                    index_in_sticker_pack=sticker_index,
                    chat_id=chat_id,
                    chat_sticker_pack_name=chat_sticker_set_name,
                    sticker_pack_owner_id=stickers_owner,
                    file_path=sticker_file[0]
                )
            )

        # We need to close previously opened session (look at DbManager#get_chat_sticker_set implementation for more details)
        session.commit()
        session.close()

        self.db_manager.create_stickers_or_update_if_exist(chat_stickers_to_update)
        logger.info(f"Newly created stickers {list(map(lambda sticker: sticker[0], stickers_to_add.values()))} were added to the {chat_sticker_set_name} sticker set")

        return sticker_set.stickers[last_achievement_index].file_id

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

    async def __create_profile_sticker(self, bot: BT, replied_user_id: int, replied_user_username: str) -> tuple[str, bytes]:
        # Note: Method not located in sticker_generator since need two additional API calls
        profile_photos = await bot.get_user_profile_photos(replied_user_id, limit=1)
        # In case profile doesn't have any photos or the user doesn't allow ALL other users to see their profile photos - generate description instead
        if not profile_photos.photos:
            return self.sticker_generator.generate_description_sticker(f"@{replied_user_username}'s achievements sticker set")
        profile_photo_id = profile_photos.photos[0][0].file_id

        prepared_for_download_photo = await bot.get_file(profile_photo_id)
        photo = await prepared_for_download_photo.download_as_bytearray()
        return self.sticker_generator.generate_sticker_with_profile_picture(bytes(photo))

    def __create_random_sticker_pack_name(self, prefix_name: str):
        # Note: As per telegram API documentation https://docs.python-telegram-bot.org/en/v20.6/telegram.bot.html#telegram.Bot.create_new_sticker_set:
        # Stickerpack name can contain only english letters, digits and underscores.
        # Must begin with a letter, can’t contain consecutive underscores and must end in “_by_<bot username>”. <bot_username> is case insensitive.
        # 1 - 64 characters.
        if not prefix_name or not prefix_name[0].isalpha():
            raise ValueError('Sticker pack should start with letter')
        sticker_pack_name_length = 16
        sticker_pack_name_to_generate = sticker_pack_name_length - len(prefix_name)
        sticker_pack_prefix = ''.join(
            random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=sticker_pack_name_to_generate))
        return f"{prefix_name}{sticker_pack_prefix}_by_{self.telgram_bot_name}"

    def run(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))

        self.application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.Regex('выдаю ачивку'), self.on_give))
        # TODO: implement sticker replies
        #  self.application.add_handler(MessageHandler(filters.reply & filters.sticker, handle_sticker_replies))
        # TODO: implement notification message (if triggered, send a notification to all channels it was send to)

        # Run the bot until the user presses Ctrl-C
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
