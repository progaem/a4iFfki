"""This module handles sticker management in Telegram"""
import os

from telegram import InputSticker, Update
from telegram._bot import BT
from telegram.constants import StickerFormat
from telegram.ext import CallbackContext

from api.telegram import TelegramAPI
from bot.commons import generate_sticker_set_name_and_title
from common.common import BaseClass
from sticker.artist import StickerArtist
from storage.postgres import ChatSticker, PostgresDatabase, UserSticker

class StickerManager(BaseClass):
    ACHIEVEMENT_EMOJI = "🥇"
    TELEGRAM_STICKERS_LINE_COUNT = 5

    def __init__(self, database: PostgresDatabase, telegram: TelegramAPI, sticker_artist: StickerArtist):
        super().__init__()
        self.telgram_bot_name = os.environ['TELEGRAM_BOT_NAME']
        
        self.telegram = telegram

        self.database = database
        self.sticker_artist = sticker_artist

    async def add_chat_stickers(
        self,
        stickers_owner: int,
        chat_id: int,
        chat_name: str,
        achievement_sticker: tuple[str, bytes],
        chat_description_sticker: tuple[str, bytes],
        prompt: str,
        update: Update,
        context: CallbackContext) -> str:
        """Adds new stickers to the chat's achievements sticker set and returns file_id of the last description sticker"""
        (chat_stickers, session) = self.database.get_chat_sticker_set(chat_id)

        (chat_sticker_set_name, stickers_to_add, last_achievement_index, context) = await self.__upload_stickers_to_stickerset(
            stickers_owner,
            chat_stickers,
            "",
            chat_name,
            "CHAT",
            achievement_sticker,
            chat_description_sticker,
            (),
            update,
            context
        )
        (sticker_set, context) = await self.telegram.get_sticker_set(chat_sticker_set_name, update, context)

        # update stickers in the database according to chat stickerset layout
        chat_stickers_to_update = []
        for sticker_index, sticker_file in stickers_to_add.items():
            sticker = sticker_set.stickers[sticker_index]
            sticker_type = "empty"
            times_achieved = None
            engraving_text = None
            if (sticker_index % (self.TELEGRAM_STICKERS_LINE_COUNT*2) < self.TELEGRAM_STICKERS_LINE_COUNT
                    and sticker_index <= last_achievement_index):
                sticker_type = "achievement"
            elif (sticker_index % (self.TELEGRAM_STICKERS_LINE_COUNT*2) >= self.TELEGRAM_STICKERS_LINE_COUNT
                    and sticker_index <= last_achievement_index + self.TELEGRAM_STICKERS_LINE_COUNT):
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

        # We need to close previously opened session (look at PostgresDatabase#get_chat_sticker_set implementation for more details)
        session.commit()
        session.close()
        self.database.create_chat_stickers_or_update_if_exist(chat_stickers_to_update)

        return sticker_set.stickers[last_achievement_index + self.TELEGRAM_STICKERS_LINE_COUNT].file_id

    async def increase_counter_on_chat_description_sticker(
        self,
        stickers_owner: int,
        chat_id: int,
        old_description_sticker_file_id,
        chat_sticker_set_name: str,
        sticker_index: int,
        description_sticker_engraving: str,
        times_achieved: int,
        update: Update,
        context: CallbackContext
    ) -> str:
        """Increases counter on the achivement's description sticker by 1 and returns updated sticker's file_id"""
        description_sticker = self.sticker_artist.draw_chat_description_sticker(description_sticker_engraving, times_achieved + 1)

        # replace old sticker with new one
        (sticker, context) = await self.telegram.replace_sticker_in_set(
            stickers_owner,
            chat_sticker_set_name,
            old_description_sticker_file_id,
            sticker_index,
            description_sticker[1],
            self.ACHIEVEMENT_EMOJI,
            update,
            context
        )

        # update sticker in the database
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
        self.database.create_chat_stickers_or_update_if_exist([chat_sticker_to_update])

        return sticker.file_id

    async def add_user_stickers(
        self,
        stickers_owner: int,
        user_id: int,
        user_name: str,
        chat_id: int,
        chat_name: str,
        achievement_sticker: tuple[str, bytes],
        user_description_sticker: tuple[str, bytes],
        prompt: str,
        update: Update,
        context: CallbackContext
    ) -> str:
        """Adds new stickers to the user's personal achievements sticker set and returns file_id of last achievement sticker"""
        (user_stickers, session) = self.database.get_user_sticker_set_for_chat(user_id, chat_id)

        user_profile_sticker = await self.__create_profile_sticker(user_id, user_name, update, context)
        user_profile_description_sticker  = self.sticker_artist.draw_persons_stickerset_description_sticker(user_name, chat_name)
        (user_sticker_set_name, stickers_to_add, last_achievement_index, context) = await self.__upload_stickers_to_stickerset(
            stickers_owner,
            user_stickers,
            user_name,
            chat_name,
            "USER",
            achievement_sticker,
            user_description_sticker,
            (user_profile_sticker, user_profile_description_sticker),
            update,
            context
        )

        # get the updated sticker set from telegram (needed to get file_id and file_unique_id for each sticker)
        (sticker_set, context) = await self.telegram.get_sticker_set(
            user_sticker_set_name,
            update,
            context
        )

        # update stickers in the database according to users stickerset layout
        user_stickers_to_update = []
        for sticker_index, sticker_file in stickers_to_add.items():
            sticker = sticker_set.stickers[sticker_index]
            sticker_type = "empty"
            engraving_text = None
            if sticker_index == 0:
                sticker_type = "profile"
            elif sticker_index == self.TELEGRAM_STICKERS_LINE_COUNT:
                sticker_type = "profile_description"
            elif (sticker_index % (self.TELEGRAM_STICKERS_LINE_COUNT*2) < self.TELEGRAM_STICKERS_LINE_COUNT
                    and sticker_index <= last_achievement_index):
                sticker_type = "achievement"
            elif (sticker_index % (self.TELEGRAM_STICKERS_LINE_COUNT*2) >= self.TELEGRAM_STICKERS_LINE_COUNT
                    and sticker_index <= last_achievement_index + self.TELEGRAM_STICKERS_LINE_COUNT):
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

        self.database.create_user_stickers_or_update_if_exist(user_stickers_to_update)

        return sticker_set.stickers[last_achievement_index].file_id

    async def find_existing_sticker(self, chat_id: int, prompt: str) -> str:
        """Checks if a sticker already exists for a provided prompt. Returns file_unique_id if exists, null otherwise."""
        file_unique_id = self.database.get_sticker_by_prompt(chat_id, prompt)
        
        return file_unique_id # file_unique_id would be null if there is no existing sticker for the prompt

    async def __upload_stickers_to_stickerset(
        self,
        stickers_owner: int,
        stickers: list[ChatSticker] | list[UserSticker],
        user_name: str, # optional, could be null if used for adding chat stickers
        chat_name: str,
        sticker_set_type: str, # "CHAT" or "USER"
        achievement_sticker: tuple[str, bytes],
        description_sticker: tuple[str, bytes],
        default_stickers_if_sticker_set_is_empty: tuple[tuple[str, bytes]], # could be empty if there is no stickers to be added as the initial ones
        update: Update,
        context: CallbackContext
    ) -> tuple[str, list[tuple[str, bytes]], int, CallbackContext]:
        """
        Function that adds achievement and description stickers to the sticker set (user/chat) through Telegram API, taking into account the logic of stickers alignment.

        If there is no sticker set, the function will create the sticker set of proper type and with a proper name. 

        Returns sticker set name, actual stickers to be added (including the ones needed for alignment) and the index of the last achievement sticker.
        This function's output could be useful to update custom database"""
        last_achievement_index = 0
        stickers_to_add = {}

        if not stickers:
            # define stickers to create: achievement, 4 empty stickers, description, 4 empty stickers
            empty_sticker = self.sticker_artist.get_empty_sticker()
            stickers_to_add = {i: empty_sticker for i in range(self.TELEGRAM_STICKERS_LINE_COUNT * 2)}
            stickers_to_add[0] = achievement_sticker
            stickers_to_add[self.TELEGRAM_STICKERS_LINE_COUNT] = description_sticker

            if default_stickers_if_sticker_set_is_empty:
                stickers_to_add[1] = stickers_to_add[0]
                stickers_to_add[0] = default_stickers_if_sticker_set_is_empty[0]
                stickers_to_add[self.TELEGRAM_STICKERS_LINE_COUNT + 1] = stickers_to_add[self.TELEGRAM_STICKERS_LINE_COUNT]
                stickers_to_add[self.TELEGRAM_STICKERS_LINE_COUNT] = default_stickers_if_sticker_set_is_empty[1]
                last_achievement_index += 1

            # create a new sticker set with previously defined stickers
            (sticker_set_name, sticker_set_title) = generate_sticker_set_name_and_title(sticker_set_type, self.telgram_bot_name, user_name, chat_name)
            context = await self.telegram.create_new_sticker_set(
                stickers_owner,
                sticker_set_name,
                sticker_set_title,
                [sticker[1] for sticker in stickers_to_add.values()],
                self.ACHIEVEMENT_EMOJI,
                update,
                context
            )
        else:
            sticker_set_name = stickers[0].sticker_set_name
            last_achievement_index = max(sticker.index_in_sticker_set for sticker in stickers if sticker.type in {"achievement", "profile"})
            
            # if number of achievements is % 5, we need to create new empty stickers
            if (last_achievement_index + 1) % self.TELEGRAM_STICKERS_LINE_COUNT == 0:
                empty_sticker = self.sticker_artist.get_empty_sticker()
                last_sticker_index = last_achievement_index + self.TELEGRAM_STICKERS_LINE_COUNT
                last_achievement_index = last_achievement_index + self.TELEGRAM_STICKERS_LINE_COUNT
                stickers_to_add = {last_sticker_index + i + 1: empty_sticker for i in range(self.TELEGRAM_STICKERS_LINE_COUNT * 2)}
                stickers_to_add[last_sticker_index + 1] = achievement_sticker
                stickers_to_add[last_sticker_index + self.TELEGRAM_STICKERS_LINE_COUNT + 1] = description_sticker

                # add stickers to the stickerset
                for sticker in stickers_to_add.values():
                    context = await self.telegram.add_sticker_into_sticker_set(
                        stickers_owner,
                        sticker_set_name,
                        sticker[1],
                        self.ACHIEVEMENT_EMOJI,
                        update,
                        context
                    )
            else:
                stickers_to_add = {
                    last_achievement_index + 1: achievement_sticker,
                    last_achievement_index + self.TELEGRAM_STICKERS_LINE_COUNT + 1: description_sticker
                }

                # replace two empty stickers next to last achievement and description stickers with the new ones
                (_, context) = await self.telegram.replace_sticker_in_set(
                    stickers_owner,
                    sticker_set_name,
                    stickers[last_achievement_index + self.TELEGRAM_STICKERS_LINE_COUNT + 1].file_id,
                    last_achievement_index + self.TELEGRAM_STICKERS_LINE_COUNT + 1,
                    description_sticker[1],
                    self.ACHIEVEMENT_EMOJI,
                    update,
                    context
                )
                (_, context) = await self.telegram.replace_sticker_in_set(
                    stickers_owner,
                    sticker_set_name,
                    stickers[last_achievement_index + 1].file_id,
                    last_achievement_index + 1,
                    achievement_sticker[1],
                    self.ACHIEVEMENT_EMOJI,
                    update,
                    context
                )

            last_achievement_index = last_achievement_index + 1
        return sticker_set_name, stickers_to_add, last_achievement_index, context

    async def __create_profile_sticker(
        self,
        user_id: int,
        user_username: str,
        update: Update,
        context: CallbackContext
    ) -> tuple[str, bytes]:
        (profile_photo, context) = await self.telegram.get_user_profile_photo(
            user_id,
            update,
            context
        )

        # In case profile doesn't have any photos or the user doesn't allow ALL other users to see their profile photos - generate description instead
        if not profile_photo:
            return self.sticker_artist.draw_sticker_from_username(f"@{user_username}")

        return self.sticker_artist.draw_sticker_from_profile_picture(profile_photo)