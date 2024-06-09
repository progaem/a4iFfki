"""
This module handles Telegram API management.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, LinkPreviewOptions, StickerSet, Sticker, InputSticker
from telegram._bot import BT
from telegram.ext import CallbackContext
from telegram.constants import ParseMode, StickerFormat
from telegram.ext import filters

from common.common import BaseClass
from common.exceptions import TelegramAPIError

class TelegramAPI(BaseClass):
    """
    This class handles all requests to the Telegram API
    
    Every method of it additionally returns CallbackContext because of the way,
    `python-telegram-bot` library is build. When adding new methods, please follow
    the same approach.
    """

    def __init__(self):
        super().__init__()

    def get_sticker_file_id(
        self,
        update: Update,
        context: CallbackContext
    ) -> (int, CallbackContext):
        """Extracts information about sticker's file id from the message"""
        file_id = update.message.sticker.file_unique_id
        self.logger.debug(f"[TELEGRAM]\tsticker file id\n\tfile_id={file_id}")
        return (file_id, context)

    def get_message(
        self,
        update: Update,
        context: CallbackContext
    ) -> (str, CallbackContext):
        """Extracts information about message text from the message"""
        text = update.message.text
        self.logger.debug(f"[TELEGRAM]\tmessage text\n\ttext={text}")
        return (text, context)

    def get_chat_info(
        self,
        update: Update,
        context: CallbackContext
    ) -> (int, str, str, CallbackContext):
        """Extracts information about the active chat (chat_id, chat_type and chat_name) from the message"""
        chat_id = update.message.chat_id
        chat_type = update.message.chat.type
        chat_name = update.effective_chat.effective_name
        self.logger.debug(
            f"[TELEGRAM]\tchat information\n\tchat_id={chat_id}\n\tchat_type={chat_type}\n\tchat_name={chat_name}"
        )
        return (chat_id, chat_type, chat_name, context)

    def get_from_user_info(
        self,
        update: Update,
        context: CallbackContext
    ) -> (int, str, CallbackContext):
        """Extracts information about the user who sent the mssage (user_id, user_name) from the message"""
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username
        self.logger.debug(
            f"[TELEGRAM]\tfrom user information\n\tuser_id={user_id}\n\tuser_name={user_name}"
        )
        return (user_id, user_name, context)

    def get_to_user_info(
        self,
        update: Update,
        context: CallbackContext
    ) -> (int, str, CallbackContext):
        """
        If the message sent was a reply, the method extracts information about the user who sent the
        quoted message (user_id, user_name). Otherwise it throws `TelegramAPIError`
        """
        if not update.message.reply_to_message:
            raise TelegramAPIError(
                "reply command was used on non reply type message",
                "non-reply-type",
                ""
            )
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.username
        self.logger.debug(f"[TELEGRAM]\tto user information\n\tuser_id={user_id}\n\tuser_name={user_name}")
        return (user_id, user_name, context)

    async def reply_text(
        self,
        message_text: str,
        update: Update,
        context: CallbackContext,
        keyboard: InlineKeyboardMarkup|None = None,
        parse_mode: ParseMode|None = None,
    ) -> CallbackContext:
        """Replies to the sent message with the text {message_text}, keyboard {keyboard} using parse mode {parse_mode}"""
        await update.message.reply_text(
            message_text,
            reply_markup=keyboard,
            parse_mode=parse_mode,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
        self.logger.debug(f"[TELEGRAM]\treply message\n\tmessage={message_text}\n\treply_markup={keyboard}")
        return context

    async def send_message(
        self,
        chat_id: int,
        message_text: str,
        update: Update,
        context: CallbackContext,
        keyboard: InlineKeyboardMarkup|None = None,
        parse_mode: ParseMode|None = None,
    ) -> CallbackContext:
        """
        Sends the message with the text {message_text}, keyboard  {keyboard} using parse mode {parse_mode}
        in the chat with id {chat_id}
        """
        bot: BT = context.bot
        await bot.send_message(
            chat_id,
            message_text,
            reply_markup=keyboard,
            parse_mode=parse_mode,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
        self.logger.debug(f"[TELEGRAM]\tsend message\n\tchat_id={chat_id}\n\tmessage={message_text}\n\treply_markup={keyboard}")
        return context

    async def send_sticker(
        self,
        chat_id: int,
        sticker_file_id: int,
        update: Update,
        context: CallbackContext
    ) -> CallbackContext:
        """
        Sends the sticker with Telegram file id {sticker_file_id} in the chat with id {chat_id}
        """
        bot: BT = context.bot
        await bot.send_sticker(chat_id, sticker_file_id)
        self.logger.debug(f"[TELEGRAM]\tsend sticker\n\tchat_id={chat_id}\n\tfile id={sticker_file_id}")
        return context

    async def get_sticker_set(
        self,
        sticker_set_name: str,
        update: Update,
        context: CallbackContext
    ) -> (StickerSet, CallbackContext):
        """Fetches the content of the sticker set with the name {sticker_set_name}"""
        bot: BT = context.bot
        sticker_set = await bot.get_sticker_set(sticker_set_name)
        self.logger.debug(f"[TELEGRAM]\tget sticker set\n\tsticker_set_name={sticker_set_name}")
        return (sticker_set, context)

    async def add_sticker_into_sticker_set(
        self,
        sticker_set_owner: int,
        sticker_set_name: str,
        sticker_content: bytes,
        sticker_emoji: str,
        update: Update,
        context: CallbackContext
    ) -> CallbackContext:
        """
        Adds the sticker from file {sticker_content} to the sticker set named {sticker_set_name},
        owned by user with user id {sticker_set_owner} aligning it with the emoji {sticker_emoji}
        representation.

        NB: multiple stickers could represent the same emoji and one sticker could represent multiple emojis
        """
        bot: BT = context.bot
        await bot.add_sticker_to_set(
            sticker_set_owner,
            sticker_set_name,
            InputSticker(sticker_content, [sticker_emoji], StickerFormat.STATIC)
        )
        self.logger.debug(f"[TELEGRAM]\tadd sticker\n\tsticker_set_owner={sticker_set_owner}\n\tsticker_set_name={sticker_set_name}")
        return context

    async def delete_sticker_set(
        self,
        sticker_set_name: str,
        update: Update,
        context: CallbackContext
    ) -> CallbackContext:
        """
        Deletes the sticker set named {sticker_set_name}.

        NB: the sticker set should be created by the bot, otherwise the method with throw exception
        """
        bot: BT = context.bot
        await bot.delete_sticker_set(sticker_set_name)
        self.logger.debug(f"[TELEGRAM]\tdelete sticker set\n\tsticker_set_name={sticker_set_name}")
        return context

    async def replace_sticker_in_set(
        self,
        sticker_set_owner: int,
        sticker_set_name: str,
        old_sticker_file_id: int,
        old_sticker_position: int,
        new_sticker_content: bytes,
        new_sticker_emoji: str,
        update: Update,
        context: CallbackContext
    ) -> (Sticker, CallbackContext):
        """
        Replaces the sticker with file_id {old_sticker_file_id} located at the position {old_sticker_position}
        from the sticker set named {sticker_set_name} and owned by the user with user id {sticker_set_owner}
        with the sticker from file {new_sticker_content} aligning it with the emoji {sticker_emoji}
        representation.
        
        Returns the new sticker content, after replacement, including information about the new sticker's
        file id and unique file id provided by Telegram

        NB: multiple stickers could represent the same emoji and one sticker could represent multiple emojis
        """
        bot: BT = context.bot
        
        await bot.delete_sticker_from_set(old_sticker_file_id)
        await bot.add_sticker_to_set(
            sticker_set_owner,
            sticker_set_name,
            InputSticker(new_sticker_content, [new_sticker_emoji], StickerFormat.STATIC)
        )
        sticker_set = await bot.get_sticker_set(sticker_set_name)
        await bot.set_sticker_position_in_set(sticker_set.stickers[-1].file_id, old_sticker_position)
        sticker_set = await bot.get_sticker_set(sticker_set_name)
        sticker = sticker_set.stickers[old_sticker_position]
        
        self.logger.debug(
            (
                f"[TELEGRAM]\t replace sticker\n\tsticker_set_owner={sticker_set_owner}\n\t"
                f"sticker_set_name={sticker_set_name}\n\told_sticker_file_id={old_sticker_file_id}"
                f"\n\told_sticker_position={old_sticker_position}"
            )
        )
        
        return (sticker, context)

    async def create_new_sticker_set(
        self,
        sticker_set_owner: int,
        sticker_set_name: str,
        sticker_set_title: str,
        stickers_content: list[bytes],
        sticker_emoji: str,
        update: Update,
        context: CallbackContext
    ) -> CallbackContext:
        """
        Creates the new sticker set under name {sticker_set_name} titled as {sticker_set_title}
        owned by {sticker_set_owner} filled with stickers from following files content {stickers_content}
        each associated with the following emoji {sticker_emoji}
        """
        bot: BT = context.bot
        
        await bot.create_new_sticker_set(
                sticker_set_owner,
                sticker_set_name,
                sticker_set_title,
                [InputSticker(sticker_content, [sticker_emoji], StickerFormat.STATIC) for sticker_content in stickers_content],
                StickerFormat.STATIC
            )
        self.logger.debug(
            (
                f"[TELEGRAM]\tnew sticker set\n\tsticker_set_owner={sticker_set_owner}\n\t"
                f"sticker_set_name={sticker_set_name}\n\tsticker_set_title={sticker_set_title}"
            )
        )
        return context

    async def get_user_profile_photo(
        self,
        user_id: int,
        update: Update,
        context: CallbackContext
    ) -> (bytes|None, CallbackContext):
        """
        Gets profile photo from the user with user id {user_id}.
        If user doesn't have a profile photo or they restrict the access to it,
        the method will return None
        """
        bot: BT = context.bot
        
        profile_photos = await bot.get_user_profile_photos(user_id, limit=1)
        self.logger.debug(f"[TELEGRAM]\tprofile photos\n\tuser_id={user_id}")
        
        if not profile_photos.photos:
            return (None, context)
        
        prepared_for_download_photo = await bot.get_file(profile_photos.photos[0][0].file_id)
        photo = await prepared_for_download_photo.download_as_bytearray()
        self.logger.debug(f"[TELEGRAM]\tdownload photos\n\tuser_id={user_id}")
        return (bytes(photo), context)

    def get_query_from_user_info(
        self,
        update: Update,
        context: CallbackContext
    ) -> (int, str, CallbackContext):
        """Extracts information about the user who pressed the button (user_id, user_name) from the update"""
        query = update.callback_query
        user_id = query.from_user.id
        user_name = query.from_user.username
        self.logger.debug(f"[TELEGRAM]\tquery from user information\n\tuser_id={user_id}\n\tuser_name={user_name}")
        return (user_id, user_name, context)
    
    def get_query_text(
        self,
        update: Update,
        context: CallbackContext
    ) -> (str, CallbackContext):
        """Extracts the text associated with the pressed button from the update"""
        query = update.callback_query
        self.logger.debug(f"[TELEGRAM]\tquery message text\n\ttext={query.data}")
        return (query.data, context)

    async def wait_for_query_answer(
        self,
        update: Update,
        context: CallbackContext
    ) -> CallbackContext:
        """Waits for query answer. This action is required before fetching any other information from the button update"""
        query = update.callback_query
        await query.answer()
        self.logger.debug(f"[TELEGRAM]\twait query")
        return context

    async def edit_query_message(
        self,
        text: str,
        reply_markup: InlineKeyboardMarkup,
        update: Update,
        context: CallbackContext
    ) -> CallbackContext:
        """
        Edits the message attached to the button pressed by user with the text {text} and keyboard {reply_markup} attached
        """
        query = update.callback_query
        try:
            await query.edit_message_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=reply_markup,
                link_preview_options=LinkPreviewOptions(is_disabled=True))
            self.logger.debug(f"[TELEGRAM]\tedit message\n\tmessage={text}\n\treply_markup={reply_markup}")
        except:
            #  exception is expected if we are replacing the text with the same one
            pass
        finally:
            return context
