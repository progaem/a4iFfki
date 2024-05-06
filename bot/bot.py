#!/usr/bin/env python
import logging
import os
import random
import string

from functools import wraps
from urllib import response

from telegram import Update, InputSticker
from telegram._bot import BT
from telegram.constants import StickerFormat
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
import telegram.ext.filters as filters

from utils.utils import masked_print
from db.db_manager import DbManager, ChatSticker, UserSticker
from prompt.prompt_detector import PromptDetector
from sticker.sticker_generator import StickerGenerator

# TODO: add Misha
LIST_OF_ADMINS = [249427415]

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
    
    def restricted_to_admins(func):
        """Restricts the usage of the command to admins of the bot"""
        @wraps(func)
        async def wrapped(bot, update, context, *args, **kwargs):
            user_id = update.message.from_user.id
            logger.info(f"wrapper function called by {user_id}")
            if user_id not in LIST_OF_ADMINS:
                return
            return await func(bot, update, context, *args, **kwargs)
        return wrapped
    
    @restricted_to_admins
    async def ban(self, update: Update, context: CallbackContext) -> None:
        """Bans a person from invoking a bot forever
        
        See more: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#restrict-access-to-a-handler-decorator
        """
        logger.info("ban was executed")
        #TODO: implement
        await update.message.reply_text("@user, the admin has restricted your access to the bot")
    
    @restricted_to_admins
    async def unban(self, update: Update, context: CallbackContext) -> None:
        """Unbans a person, lifting the restriction to invoke a bot
        
        See more: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#restrict-access-to-a-handler-decorator
        """
        #TODO: implement
        await update.message.reply_text("@user, the admin has lifted the restriction on your access to the bot")
    
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Send a description of the bot when the command /start is issued."""
        await update.message.reply_text("TODO: write meaningful description of the bot")

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send a FAQ with short description of commands when the command /help is issued."""
        await update.message.reply_text("TODO: write meaningful description of the bot")
    
    async def show_sticker_set(self, update: Update, context: CallbackContext) -> None:
        """Send a link to sticker set of the user"""
        chat_id = update.message.chat_id
        chat_name = update.effective_chat.effective_name
        user_id = update.message.from_user.id
        username = update.message.from_user.username

        chat_stickerset_name = self.db_manager.get_chat_sticker_set_name(chat_id)
        user_stickerset_name = self.db_manager.get_user_sticker_set_name(user_id, chat_id)

        response = ""
        if chat_stickerset_name:
            response = f'Link to \'{chat_name}\'achievements: https://t.me/addstickers/{chat_stickerset_name}\n'
            if user_stickerset_name:
                response += f'Link to @{username}\'s achievements in the chat \'{chat_name}\': https://t.me/addstickers/{user_stickerset_name}'
            else:
                response += f'@{username} doesn\'t have any achievements in the chat \'{chat_name}\''
        else:
            response = f'Nobody in the chat \'{chat_name}\' has received an achievement yet'

        await update.message.reply_text(response)

    async def on_give(self, update: Update, context: CallbackContext) -> None:
        """Give an achievement to a person in reply message on mention achievements"""
        bot = context.bot
        message_text = update.message.text
        chat_id = update.message.chat_id
        chat_name = update.effective_chat.effective_name
        user_id = update.message.from_user.id
        invoking_user_name = update.message.from_user.username

        if not update.message.reply_to_message:
            logger.info(f"{user_id} in {chat_id} mentioned выдаю ачивку, but it wasn't reply")
            return

        cited_user_id = update.message.reply_to_message.from_user.id
        cited_user_username = update.message.reply_to_message.from_user.username
        logger.info(f"{user_id} in {chat_id} mentioned выдаю ачивку replying to {cited_user_id} message")

        prompt = self.prompt_detector.detect(message_text)
        if not prompt:
            await update.message.reply_text(
                f'User {user_id} in {chat_id} chat mentioned \'выдаю ачивку\' to {cited_user_id}! But prompt was not identified :(')

        # TODO: defend from ddos (1 new achievement per person per day, except me to add initial achievements)
        self.db_manager.save_prompt_message(chat_id, user_id, cited_user_id, message_text, prompt)

        # check if the sticker owner is defined for this chat
        stickers_owner_id = await self.__determine_stickerset_owner(chat_id, context)

        # generate all needed stickers
        achievement_sticker = self.sticker_generator.generate_sticker_from_prompt(prompt)
        chat_description_sticker = self.sticker_generator.generate_group_chat_description_sticker(prompt, 1)
        user_description_sticker = self.sticker_generator.generate_description_sticker(prompt)

        # update chat's sticker set
        logger.info(f"Adding new stickers to chat {chat_id}'s sticker set")
        achievement_description_chat_sticker_file_id = await self.add_chat_stickers(stickers_owner_id, chat_id, chat_name, achievement_sticker, chat_description_sticker, prompt, context)

        # update user's sticker set
        logger.info(f"Adding new stickers to user {cited_user_id}'s sticker set in chat {chat_id}")
        achievement_user_sticker_file_id = await self.add_user_stickers(stickers_owner_id, cited_user_id, cited_user_username, chat_id, chat_name, achievement_sticker, user_description_sticker, prompt, context)

        # Respond in the chat
        #    with the greeting message
        await update.message.reply_text(
            f'Congrats @{cited_user_username} you just received the achievement from @{invoking_user_name} in \'{chat_name}\' chat for \'{prompt}\'')
        
        #    with the achievement sticker from user's sticker set
        await bot.send_sticker(chat_id, achievement_user_sticker_file_id)

        #    with the achievement's description sticker from chat's sticker set (since it indicate the rarity of the given sticker?)
        await bot.send_sticker(chat_id, achievement_description_chat_sticker_file_id)

    async def on_sticker_reply(self, update: Update, context: CallbackContext) -> None:
        """Send an achievement when person replied to another person with a chat sticker"""
        bot = context.bot
        sticker_file_id = update.message.sticker.file_unique_id
        chat_id = update.message.chat_id
        chat_name = update.effective_chat.effective_name
        user_id = update.message.from_user.id
        invoking_user_name = update.message.from_user.username

        if not update.message.reply_to_message:
            logger.info(f"{user_id} in {chat_id} mentioned выдаю ачивку, but it wasn't reply")
            return

        cited_user_id = update.message.reply_to_message.from_user.id
        cited_user_username = update.message.reply_to_message.from_user.username

        # TODO: We might need an additional cash layer in front of this kind of data (chat_id -> sticker_id[])
        (chat_sticker_set_info, session) = self.db_manager.get_chat_sticker_set(chat_id)
        logger.info(f"Current state of chat stickers: {chat_sticker_set_info}")
        stickers_to_types = dict(map(lambda s: (s.file_unique_id, [s.type, s.index_in_sticker_set]), chat_sticker_set_info))

        # Check if the sticker was from the chat stickerset
        if sticker_file_id in stickers_to_types:

            (sticker_type, sticker_index) = stickers_to_types[sticker_file_id]
            if sticker_type == 'achievement':

                #TODO: add the ddos check

                # get information about old tickets
                achievement_sticker_file_path = list(filter(lambda sticker_info: sticker_info.index_in_sticker_set == sticker_index, chat_sticker_set_info))[0].file_path
                description_sticker = list(filter(lambda sticker_info: sticker_info.index_in_sticker_set == sticker_index + 5, chat_sticker_set_info))[0]

                logger.info(f"We intend to remove the sticker {description_sticker} at the location {sticker_index + 5}")
                # determine chat's stickers set owner
                stickerset_owner = description_sticker.sticker_set_owner_id

                # update user's stickers
                achievement_sticker = self.sticker_generator.sticker_file_manager.get_bytes_from_path(achievement_sticker_file_path)
                user_description_sticker = self.sticker_generator.generate_description_sticker(description_sticker.engraving_text)
                achievement_user_sticker_file_id = await self.add_user_stickers(stickerset_owner, cited_user_id, cited_user_username, chat_id, chat_name, (achievement_sticker_file_path, achievement_sticker), user_description_sticker, description_sticker.engraving_text, context)

                # update number on chat description sticker
                achievement_description_chat_sticker_file_id = await self.increase_counter_on_chat_description_sticker(stickerset_owner, chat_id, description_sticker.file_id, description_sticker.sticker_set_name, sticker_index + 5, description_sticker.engraving_text, description_sticker.times_achieved, context)

                # Respond in the chat
                #    with the greeting message
                await update.message.reply_text(
                    f'Congrats @{cited_user_username} you just received the achievement from @{invoking_user_name} in \'{chat_name}\' chat for \'{description_sticker.engraving_text}\'')
        
                #    with the achievement sticker from user's sticker set
                await bot.send_sticker(chat_id, achievement_user_sticker_file_id)

                #    with the achievement's description sticker from chat's sticker set (since it indicate the rarity of the given sticker?)
                await bot.send_sticker(chat_id, achievement_description_chat_sticker_file_id)
            elif sticker_type == 'empty':
                await update.message.reply_text("This achievement is not unblocked yet, so you can't give it to someone else!")

        session.commit()
        session.close()

    async def add_chat_stickers(
            self,
            stickers_owner: int,
            chat_id: int,
            chat_name: str,
            achievement_sticker: tuple[str, bytes],
            chat_description_sticker: tuple[str, bytes],
            prompt: str,
            context: CallbackContext) -> str:
        """Adds new achievement stickers to the chat sticker set and returns the file_id of the achievement sticker"""
        bot = context.bot

        # get current stickers for the chat
        (chat_stickers, session) = self.db_manager.get_chat_sticker_set(chat_id)
        # map()
        logger.info(f"Chat stickers found in {chat_name}: {chat_stickers}")

        # update the stickers set with the new stickers
        (chat_sticker_set_name, stickers_to_add, last_achievement_index) = await self.__upload_stickers_to_stickerset(stickers_owner, chat_stickers, "", chat_name, "CHAT", achievement_sticker, chat_description_sticker, (), context)

        # get the updated sticker set from telegram (needed to get file_id and file_unique_id for each sticker)
        sticker_set = await bot.get_sticker_set(chat_sticker_set_name)
        logger.info(f"Fetching updated {chat_sticker_set_name} sticker set")

        # update stickers in the database
        chat_stickers_to_update = []
        for sticker_index, sticker_file in stickers_to_add.items():
            sticker = sticker_set.stickers[sticker_index]
            sticker_type = "empty"
            times_achieved = None
            engraving_text = None
            # each first line of stickers that comes before last achievement are achievements
            if sticker_index % 10 < 5 and sticker_index <= last_achievement_index:
                sticker_type = "achievement"
            # each second line of stickers that comes before last achievement's description are descriptions
            elif sticker_index % 10 >= 5 and sticker_index <= last_achievement_index + 5:
                sticker_type = "description"
                engraving_text = prompt
                times_achieved = 1
            chat_stickers_to_update.append(
                ChatSticker(
                    file_id=sticker.file_id,
                    file_unique_id=sticker.file_unique_id,
                    type=sticker_type,
                    engraving_text = engraving_text,
                    times_achieved=times_achieved,
                    index_in_sticker_set=sticker_index,
                    chat_id=chat_id,
                    sticker_set_name=chat_sticker_set_name,
                    sticker_set_owner_id=stickers_owner,
                    file_path=sticker_file[0]
                )
            )

        # We need to close previously opened session (look at DbManager#get_chat_sticker_set implementation for more details)
        session.commit()
        session.close()

        self.db_manager.create_chat_stickers_or_update_if_exist(chat_stickers_to_update)
        logger.info(f"Newly created stickers {list(map(lambda sticker: sticker[0], stickers_to_add.values()))} were added to the {chat_sticker_set_name} sticker set")

        return sticker_set.stickers[last_achievement_index + 5].file_id

    async def increase_counter_on_chat_description_sticker(self, stickers_owner: int, chat_id: int, old_description_sticker_file_id, chat_sticker_set_name: str, sticker_index: int, description_sticker_engraving: str, times_achieved: int, context: CallbackContext) -> None:
        """Increase counter on the achivement's description sticker by 1"""
        bot = context.bot

        # generate new sticker
        logger.info(f"Increasing number of times achievement {description_sticker_engraving} was achieved to {times_achieved +1}")
        description_sticker = self.sticker_generator.generate_group_chat_description_sticker(description_sticker_engraving, times_achieved + 1)

        # replace the old sticker
        # TODO: once the `replace_sticker_in_set` API become stable we could rewrite the following code with 1 line:
        # await bot.replace_sticker_in_set(stickers_owner, chat_sticker_set_name, old_description_sticker_file_id, InputSticker(description_sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC))
        # However currently the new API is unable to recognise old file ids... (Hours spent on this bug: 2)
        await bot.delete_sticker_from_set(old_description_sticker_file_id)
        logger.info(f"Old description sticker in the {chat_sticker_set_name} sticker set was deleted")
        await bot.add_sticker_to_set(stickers_owner, chat_sticker_set_name, InputSticker(description_sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC))
        logger.info(f"New description sticker was added at the end of {chat_sticker_set_name} sticker set")
        sticker_set = await bot.get_sticker_set(chat_sticker_set_name)
        chat_description_sticker_id = sticker_set.stickers[-1].file_id
        await bot.set_sticker_position_in_set(chat_description_sticker_id, sticker_index)
        logger.info(f"New description sticker was set at the position {sticker_index} in the {chat_sticker_set_name} sticker set")
        
        # get the updated sticker set from telegram (needed to get file_id and file_unique_id for each sticker)
        chat_sticker_set = await bot.get_sticker_set(chat_sticker_set_name)
        logger.info(f"Fetching updated {chat_sticker_set_name} sticker set")

        # update sticker in the database
        # Note: due to the reasons described above, it's better to fetch all new ids now
        sticker = chat_sticker_set.stickers[sticker_index]
        chat_sticker_to_update = ChatSticker(
            file_id=sticker.file_id,
            file_unique_id=sticker.file_unique_id,
            type="description",
            engraving_text = description_sticker_engraving,
            times_achieved=times_achieved + 1,
            index_in_sticker_set=sticker_index,
            chat_id=chat_id,
            sticker_set_name=chat_sticker_set_name,
            sticker_set_owner_id=stickers_owner,
            file_path=description_sticker[0]
        )
        self.db_manager.create_chat_stickers_or_update_if_exist([chat_sticker_to_update])
        logger.info(f"Updated sticker {chat_sticker_to_update} in the {chat_sticker_set_name} sticker set")

        return sticker.file_id

    async def add_user_stickers(self, stickers_owner: int, user_id: int, user_name: str, chat_id: int, chat_name: str, achievement_sticker: tuple[str, bytes], user_description_sticker: tuple[str, bytes], prompt: str, context: CallbackContext) -> None:
        """Adds new achievement stickers to the user sticker pack"""
        bot = context.bot

        # get current stickers for the chat
        (user_stickers, session) = self.db_manager.get_user_sticker_set_for_chat(user_id, chat_id)
        logger.info(f"{user_name}'s stickers in {chat_name}: {user_stickers}")

        # generate user sticker set's default stickers
        user_profile_sticker = await self.__create_profile_sticker(bot, user_id, user_name)
        user_profile_description_sticker  = self.sticker_generator.generate_user_stickerset_description_sticker(user_name, chat_name)

        # update the stickers set with the new stickers
        (user_sticker_set_name, stickers_to_add, last_achievement_index) = await self.__upload_stickers_to_stickerset(stickers_owner, user_stickers, user_name, chat_name, "USER", achievement_sticker, user_description_sticker, (user_profile_sticker, user_profile_description_sticker), context)

        # get the updated sticker set from telegram (needed to get file_id and file_unique_id for each sticker)
        sticker_set = await bot.get_sticker_set(user_sticker_set_name)
        logger.info(f"Fetching updated {user_sticker_set_name} sticker set")

        # update stickers in the database
        user_stickers_to_update = []
        for sticker_index, sticker_file in stickers_to_add.items():
            sticker = sticker_set.stickers[sticker_index]
            sticker_type = "empty"
            engraving_text = None
            # first sticker always profile sticker
            if sticker_index == 0:
                sticker_type = "profile"
            # sixth sticker is always
            elif sticker_index == 5:
                sticker_type = "profile_description"
            # each first line of stickers that comes before last achievement are achievements
            elif sticker_index % 10 < 5 and sticker_index <= last_achievement_index:
                sticker_type = "achievement"
            # each second line of stickers that comes before last achievement's description are descriptions
            elif sticker_index % 10 >= 5 and sticker_index <= last_achievement_index + 5:
                sticker_type = "description"
                engraving_text = prompt
            user_stickers_to_update.append(
                UserSticker(
                    file_id=sticker.file_id,
                    file_unique_id=sticker.file_unique_id,
                    type=sticker_type,
                    engraving_text = engraving_text,
                    index_in_sticker_set=sticker_index,
                    user_id=user_id,
                    chat_id=chat_id,
                    sticker_set_name=user_sticker_set_name,
                    file_path=sticker_file[0]
                )
            )

        # We need to close previously opened session (look at DbManager#get_user_sticker_set implementation for more details)
        session.commit()
        session.close()

        self.db_manager.create_user_stickers_or_update_if_exist(user_stickers_to_update)
        logger.info(f"Newly created stickers {list(map(lambda sticker: sticker[0], stickers_to_add.values()))} were added to the {user_sticker_set_name} sticker set")

        return sticker_set.stickers[last_achievement_index].file_id
    
    async def __determine_stickerset_owner(
            self,
            chat_id: str,
            context: CallbackContext
    ) -> int:
        """
        Function that returns the stickerset owner for the chat, or None if such doesn't exist
        """
        bot = context.bot

        # TODO: if this is a new chat -- determine a sticker user
        # TODO: take sticker admin user id
        # TODO: paste here your username if you have premium account
        return 249427415

    async def __upload_stickers_to_stickerset(
        self,
        stickers_owner: int,
        stickers, # list of either ChatSticker or UserSticker type
        user_name: str, # optional, could be null if used for adding chat stickers
        chat_name: str,
        sticker_set_type: str, #TODO: to make a enum of CHAT and USER
        achievement_sticker: tuple[str, bytes],
        description_sticker: tuple[str, bytes],
        default_stickers_if_sticker_set_is_empty: tuple[tuple[str, bytes]], # could be empty if there is no stickers to be added as the initial ones
        context: CallbackContext
    ) -> tuple[str, list[tuple[str, bytes]], int]:
        """
        Function that adds achievement and description stickers to the sticker set (user/chat) through Telegram API, taking into account the logic of stickers alignment.

        If there is no sticker set, the function will create the sticker set of proper type and with a proper name. 

        Returns sticker set name, actual stickers to be added (including the ones needed for alignment) and the index of the last achievement sticker.
        This function's output could be useful to update custom database"""
        # since the sticker pack was just created, the last achievement id is 0
        last_achievement_index = 0
        stickers_to_add = dict()
        sticker_set_name = ""

        bot = context.bot
        
        if not stickers:
            # define stickers to create: achievement, 4 empty stickers, description, 4 empty stickers
            logger.info(f"Sticker set for chat {chat_name} for {user_name} was not initialized. Trying to initialize it...")
            empty_sticker = self.sticker_generator.get_empty_sticker()
            stickers_to_add = {
                0: achievement_sticker,
                1: empty_sticker,
                2: empty_sticker,
                3: empty_sticker,
                4: empty_sticker,
                5: description_sticker,
                6: empty_sticker,
                7: empty_sticker,
                8: empty_sticker,
                9: empty_sticker
            }

            # if there are any default tickets, add them in front of added ones
            if default_stickers_if_sticker_set_is_empty:
                (default_sticker, default_description_sticker) = default_stickers_if_sticker_set_is_empty
                stickers_to_add[1] = stickers_to_add[0]
                stickers_to_add[0] = default_sticker
                stickers_to_add[6] = stickers_to_add[5]
                stickers_to_add[5] = default_description_sticker
                last_achievement_index += 1

            created_stickers = list(map(lambda sticker: InputSticker(sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC), stickers_to_add.values()))

            # create a new sticker set with previously defined stickers
            sticker_set_name = self.__create_random_sticker_pack_name(sticker_set_type.lower())
            sticker_set_title = f"'{chat_name}"[:62] + "' achievements" if sticker_set_type == "CHAT" else f"{user_name}'s achievements in '{chat_name}"[:62] + "'"
            await bot.create_new_sticker_set(stickers_owner, sticker_set_name, sticker_set_title, created_stickers, StickerFormat.STATIC)
            logger.info(f"New sticker set was created under name {sticker_set_name} and assigned owner {stickers_owner}")
        else:
            sticker_set_name = stickers[0].sticker_set_name
            last_achievement_index = len(list(filter(lambda sticker: sticker.type == "achievement" or sticker.type == "profile", stickers))) - 1
            logger.info(
                f"Sticker set was created under name {sticker_set_name} already existed, the index of the last achievement sticker is {last_achievement_index}")
            # if number of achievements is % 5, we need to create new empty stickers
            if last_achievement_index % 5 == 4:
                logger.info(f"Number of achievement stickers in the {sticker_set_name} sticker set is a multiple of 5. Trying to 10 stickers to the sticker set (including empty ones)")
                empty_sticker = self.sticker_generator.get_empty_sticker()
                last_sticker_index = last_achievement_index + 5
                last_achievement_index = last_achievement_index + 5
                stickers_to_add = {
                    last_sticker_index + 1: achievement_sticker,
                    last_sticker_index + 2: empty_sticker,
                    last_sticker_index + 3: empty_sticker,
                    last_sticker_index + 4: empty_sticker,
                    last_sticker_index + 5: empty_sticker,
                    last_sticker_index + 6: description_sticker,
                    last_sticker_index + 7: empty_sticker,
                    last_sticker_index + 8: empty_sticker,
                    last_sticker_index + 9: empty_sticker,
                    last_sticker_index + 10: empty_sticker
                }

                # add stickers to the stickers
                for i, sticker in stickers_to_add.items():
                    await bot.add_sticker_to_set(stickers_owner, sticker_set_name,  InputSticker(sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC))
                    logger.info(f"Successfully added sticker number {i} to the sticker set {sticker_set_name} located at the path {sticker[0]}")
            else:
                logger.info(
                    f"Number of achievement stickers in the {sticker_set_name} sticker set is NOT a multiple of 5 (It's {last_achievement_index}). Trying to add new stickers in place of others")
                stickers_to_add = {
                    last_achievement_index + 1: achievement_sticker,
                    last_achievement_index + 6: description_sticker
                }
                # delete two empty stickers next to last achievement and description stickers (the last sticker deleted first so indices of earlier stickers won't change)
                await bot.delete_sticker_from_set(stickers[last_achievement_index + 6].file_id)
                await bot.delete_sticker_from_set(stickers[last_achievement_index + 1].file_id)
                logger.info(f"Two empty stickers in the {sticker_set_name} sticker set were deleted")

                # add new stickers to the sticker set
                await bot.add_sticker_to_set(stickers_owner, sticker_set_name,
                                             InputSticker(achievement_sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC))
                await bot.add_sticker_to_set(stickers_owner, sticker_set_name,
                                             InputSticker(description_sticker[1], [self.ACHIEVEMENT_EMOJI],  StickerFormat.STATIC))
                logger.info(f"Two new stickers (located at {achievement_sticker[0]} and {description_sticker[0]}) were added at the end of {sticker_set_name} sticker set")

                # set the achievement stickers next to the previous ones (the first sticker should be added first)
                sticker_set = await bot.get_sticker_set(sticker_set_name)
                achievement_sticker_id = sticker_set.stickers[-2].file_id
                chat_description_sticker_id = sticker_set.stickers[-1].file_id
                await bot.set_sticker_position_in_set(achievement_sticker_id, last_achievement_index + 1)
                await bot.set_sticker_position_in_set(chat_description_sticker_id, last_achievement_index + 6)
                logger.info(f"New stickers were set at the positions {last_achievement_index + 1} and {last_achievement_index + 6} in the {sticker_set_name} sticker set")

            last_achievement_index = last_achievement_index + 1
        # return updated sticker set name, stickers that we need to update and the id of the last achievement sticker
        return sticker_set_name, stickers_to_add, last_achievement_index

    async def __create_profile_sticker(self, bot: BT, user_id: int, user_username: str) -> tuple[str, bytes]:
        # Note: Method not located in sticker_generator since need two additional API calls
        profile_photos = await bot.get_user_profile_photos(user_id, limit=1)
        # In case profile doesn't have any photos or the user doesn't allow ALL other users to see their profile photos - generate description instead
        if not profile_photos.photos:
            return self.sticker_generator.generate_no_profile_picture_sticker(f"@{user_username}")
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
        # default commands
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # admin-only commands
        self.application.add_handler(CommandHandler("ban", self.ban))
        self.application.add_handler(CommandHandler("unban", self.unban))

        # public commands
        self.application.add_handler(CommandHandler("show", self.show_sticker_set))
        self.application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.Regex('выдаю ачивку'), self.on_give))
        self.application.add_handler(MessageHandler(filters.REPLY & filters.Sticker.ALL, self.on_sticker_reply))
        # TODO: implement notification message (if triggered, send a notification to all channels it was send to)

        # Run the bot until the user presses Ctrl-C
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
