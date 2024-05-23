import logging
import os

from telegram import InputSticker
from telegram._bot import BT
from telegram.constants import StickerFormat
from telegram.ext import CallbackContext

from bot.commons import generate_sticker_set_name
from sticker.artist import StickerArtist
from storage.postgres import ChatSticker, PostgresDatabase, UserSticker

class StickerManager:
    ACHIEVEMENT_EMOJI = "🥇"
    
    def __init__(self, database: PostgresDatabase, sticker_artist: StickerArtist):
        self.telgram_bot_name = os.environ['TELEGRAM_BOT_NAME']

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
        context: CallbackContext) -> str:
        """Adds new achievement stickers to the chat sticker set and returns the file_id of the achievement sticker"""
        bot: BT = context.bot
        # get current stickers for the chat
        (chat_stickers, session) = self.database.get_chat_sticker_set(chat_id)
        # update the stickers set with the new stickers
        (chat_sticker_set_name, stickers_to_add, last_achievement_index) = await self.__upload_stickers_to_stickerset(stickers_owner, chat_stickers, "", chat_name, "CHAT", achievement_sticker, chat_description_sticker, (), context)
        # get the updated sticker set from telegram (needed to get file_id and file_unique_id for each sticker)
        sticker_set = await bot.get_sticker_set(chat_sticker_set_name)
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

        # We need to close previously opened session (look at PostgresDatabase#get_chat_sticker_set implementation for more details)
        session.commit()
        session.close()
        self.database.create_chat_stickers_or_update_if_exist(chat_stickers_to_update)
        
        return sticker_set.stickers[last_achievement_index + 5].file_id
        
    async def increase_counter_on_chat_description_sticker(self, stickers_owner: int, chat_id: int, old_description_sticker_file_id, chat_sticker_set_name: str, sticker_index: int, description_sticker_engraving: str, times_achieved: int, context: CallbackContext) -> str:
        """Increase counter on the achivement's description sticker by 1"""
        bot: BT = context.bot
        # generate new sticker
        description_sticker = self.sticker_artist.generate_group_chat_description_sticker(description_sticker_engraving, times_achieved + 1)

        # replace old sticker with new one
        # TODO: once the `replace_sticker_in_set` API become stable we could rewrite the following code with 1 line:
        # await bot.replace_sticker_in_set(stickers_owner, chat_sticker_set_name, old_description_sticker_file_id, InputSticker(description_sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC))
        # However currently the new API is unable to recognise old file ids... (Hours spent on this bug: 2)
        await bot.delete_sticker_from_set(old_description_sticker_file_id)
        await bot.add_sticker_to_set(stickers_owner, chat_sticker_set_name, InputSticker(description_sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC))
        sticker_set = await bot.get_sticker_set(chat_sticker_set_name)
        new_sticker_id = sticker_set.stickers[-1].file_id
        await bot.set_sticker_position_in_set(new_sticker_id, sticker_index)
            
        # get the updated sticker set from telegram (needed to get file_id and file_unique_id for each sticker)
        chat_sticker_set = await bot.get_sticker_set(chat_sticker_set_name)
        
        # update sticker in the database
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
        self.database.create_chat_stickers_or_update_if_exist([chat_sticker_to_update])

        return sticker.file_id

    async def add_user_stickers(self, stickers_owner: int, user_id: int, user_name: str, chat_id: int, chat_name: str, achievement_sticker: tuple[str, bytes], user_description_sticker: tuple[str, bytes], prompt: str, context: CallbackContext) -> str:
        """Adds new achievement stickers to the user sticker pack"""
        bot: BT = context.bot
        # get current stickers for the chat
        (user_stickers, session) = self.database.get_user_sticker_set_for_chat(user_id, chat_id)

        # generate user sticker set's default stickers
        user_profile_sticker = await self.__create_profile_sticker(context, user_id, user_name)
        user_profile_description_sticker  = self.sticker_artist.generate_user_stickerset_description_sticker(user_name, chat_name)

        # update the stickers set with the new stickers
        (user_sticker_set_name, stickers_to_add, last_achievement_index) = await self.__upload_stickers_to_stickerset(stickers_owner, user_stickers, user_name, chat_name, "USER", achievement_sticker, user_description_sticker, (user_profile_sticker, user_profile_description_sticker), context)

        # get the updated sticker set from telegram (needed to get file_id and file_unique_id for each sticker)
        sticker_set = await bot.get_sticker_set(user_sticker_set_name)
        
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

        self.database.create_user_stickers_or_update_if_exist(user_stickers_to_update)

        return sticker_set.stickers[last_achievement_index].file_id

    async def __upload_stickers_to_stickerset(
        self,
        stickers_owner: int,
        stickers: list[ChatSticker] | list[UserSticker],
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
        bot: BT = context.bot
        
        # since the sticker pack was just created, the last achievement id is 0
        last_achievement_index = 0
        stickers_to_add = dict()
        sticker_set_name = ""
        
        if not stickers:
            # define stickers to create: achievement, 4 empty stickers, description, 4 empty stickers
            empty_sticker = self.sticker_artist.get_empty_sticker()
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
            sticker_set_name = generate_sticker_set_name(sticker_set_type.lower(), self.telgram_bot_name)
            sticker_set_title = f"'{chat_name}"[:62] + "' achievements" if sticker_set_type == "CHAT" else f"{user_name}'s achievements in '{chat_name}"[:62] + "'"
            # TODO: handle timeout
            await bot.create_new_sticker_set(stickers_owner, sticker_set_name, sticker_set_title, created_stickers, StickerFormat.STATIC)
        else:
            sticker_set_name = stickers[0].sticker_set_name
            last_achievement_index = max(sticker.index_in_sticker_set for sticker in stickers if sticker.type in {"achievement", "profile"})
            # if number of achievements is % 5, we need to create new empty stickers
            if last_achievement_index % 5 == 4:
                empty_sticker = self.sticker_artist.get_empty_sticker()
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

                # add stickers to the stickerset
                for i, sticker in stickers_to_add.items():
                    await bot.add_sticker_to_set(stickers_owner, sticker_set_name, InputSticker(sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC))
            else:
                stickers_to_add = {
                    last_achievement_index + 1: achievement_sticker,
                    last_achievement_index + 6: description_sticker
                }
                # delete two empty stickers next to last achievement and description stickers (the last sticker deleted first so indices of earlier stickers won't change)
                await bot.delete_sticker_from_set(stickers[last_achievement_index + 6].file_id)
                await bot.delete_sticker_from_set(stickers[last_achievement_index + 1].file_id)

                # add new stickers to the sticker set
                await bot.add_sticker_to_set(stickers_owner, sticker_set_name, InputSticker(achievement_sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC))
                await bot.add_sticker_to_set(stickers_owner, sticker_set_name, InputSticker(description_sticker[1], [self.ACHIEVEMENT_EMOJI], StickerFormat.STATIC))

                # set the achievement stickers next to the previous ones (the first sticker should be added first)
                sticker_set = await bot.get_sticker_set(sticker_set_name)
                achievement_sticker_id = sticker_set.stickers[-2].file_id
                chat_description_sticker_id = sticker_set.stickers[-1].file_id
                await bot.set_sticker_position_in_set(achievement_sticker_id, last_achievement_index + 1)
                await bot.set_sticker_position_in_set(chat_description_sticker_id, last_achievement_index + 6)

            last_achievement_index = last_achievement_index + 1
        return sticker_set_name, stickers_to_add, last_achievement_index

    async def __create_profile_sticker(self, context: CallbackContext, user_id: int, user_username: str) -> tuple[str, bytes]:
        bot: BT = context.bot
        profile_photos = await bot.get_user_profile_photos(user_id, limit=1)
        # In case profile doesn't have any photos or the user doesn't allow ALL other users to see their profile photos - generate description instead
        if not profile_photos.photos:
            return self.sticker_artist.generate_no_profile_picture_sticker(f"@{user_username}")
        profile_photo_id = profile_photos.photos[0][0].file_id

        prepared_for_download_photo = await bot.get_file(profile_photo_id)
        photo = await prepared_for_download_photo.download_as_bytearray()
        return self.sticker_artist.generate_sticker_with_profile_picture(bytes(photo))