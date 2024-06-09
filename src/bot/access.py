"""
This module handles all access restriction logic, including warning processing
"""
from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext

from api.telegram import TelegramAPI
from common.common import BaseClass
from storage.postgres import PostgresDatabase

### HELPER COMMANDS, RESTRICTING VISBILITY TO METHODS ###

# change this id to your telegram user id
LIST_OF_ADMINS = [249427415]

def restricted_to_private_messages(func):
    """Restricts the usage of the command only to private messages"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        (_, chat_type, _, context) = bot.telegram.get_chat_info(update, context)
        if not chat_type == "private":
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped
        

def restricted_to_supergroups(func):
    """Restricts the usage of the command only to supergroups"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        (_, chat_type, _, context) = bot.telegram.get_chat_info(update, context)
        if not chat_type == "supergroup":
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

def restricted_to_admins(func):
    """Restricts the usage of the command to admins of the bot"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        (user_id, _, context) = bot.telegram.get_from_user_info(update, context)
        if user_id not in LIST_OF_ADMINS:
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

def restricted_to_not_banned(func):
    """Restricts the usage of the command to admins of the bot"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        (_, user_name, context) = bot.telegram.get_from_user_info(update, context)
        if bot.database.is_banned(user_name):
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

def restricted_to_stickerset_owners(func):
    """Restricts the usage of the command to stickerset owners"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        (chat_id, _, _, context) = bot.telegram.get_chat_info(update, context)
        (user_id, _, context) = bot.telegram.get_from_user_info(update, context)

        stickerset_owner = bot.database.get_stickerset_owner(chat_id)
        if not stickerset_owner or int(stickerset_owner) != user_id:
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

def restricted_to_undefined_stickerset_chats(func):
    """Restricts the usage of the command to chats without defined stickerset owners"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        (chat_id, _, _, context) = bot.telegram.get_chat_info(update, context)
        if bot.database.is_stickerset_owner_defined_for_chat(chat_id):
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

def restricted_to_defined_stickerset_chats(func):
    """Restricts the usage of the command to chats only with defined stickerset owners"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        (chat_id, _, _, context) = bot.telegram.get_chat_info(update, context)
        if not bot.database.is_stickerset_owner_defined_for_chat(chat_id):
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

class WarningsProcessor(BaseClass):
    BAN_MESSAGE = (
        "@{user_name} you exceeded the limit of {warnings_limit}, so as we warned previously, "
        "we permanently ban you from utilizing this bot"
    )

    def __init__(self, database: PostgresDatabase, telegram: TelegramAPI):
        super().__init__()
        self.database = database
        self.telegram = telegram

    async def add_show_stickers_warning(
        self,
        update: Update,
        context: CallbackContext
    ) -> bool:
        """Adds a warning for using show command too frequently"""
        max_show_stickers_interractions = 20
        max_warnings_until_ban = 5

        (_, user_name, context) = self.telegram.get_from_user_info(update, context)
        warning_message = (
            f'@{user_name}, we\'ve noticed unusual activity from your account, currently there '
            f'is a limit of {max_show_stickers_interractions} daily /show executions per '
            f'individual. Exceeding this limit will prompt notifications such as this one. '
            f'Accumulating {max_warnings_until_ban} warnings of this nature within a single '
            f'day may result in permanent suspension from utilizing our bot.'
        )
        return await self.__add_warning(
            "show_stickers",
            max_show_stickers_interractions,
            "show_stickers_invocations_exceed",
            max_warnings_until_ban,
            warning_message,
            update,
            context
        )

    async def add_give_achievement_warning(
        self,
        update: Update,
        context: CallbackContext
    ) -> bool:
        """Adds a warning for invoking achievement giving command too frequently"""
        max_give_achievement_interractions = 2
        max_warnings_until_ban = 10

        (_, user_name, context) = self.telegram.get_from_user_info(update, context)
        warning_message = (
            f'Achievements are like rare jewels scattered throughout our lives, precious and '
            f'unique. It\'s crucial to cherish their scarcity and significance. That\'s why '
            f'we\'ve imposed a limit of {max_give_achievement_interractions} daily executions '
            f'per individual. Exceeding this limit will prompt notifications such as this one. '
            f'Accumulating {max_warnings_until_ban} warnings of this nature within a single day '
            f'may result in permanent suspension from utilizing our bot. @{user_name}, we kindly '
            f'ask for your cooperation in adhering to these guidelines.'
        )
        return await self.__add_warning(
            "new_achievement",
            max_give_achievement_interractions,
            "new_achievement_invocations_exceed",
            max_warnings_until_ban,
            warning_message,
            update,
            context
        )

    async def add_message_format_warning(
        self,
        update: Update,
        context: CallbackContext
    ) -> bool:
        """Adds a warning for use of inappropriate language in the achievement message"""
        max_message_format_interractions = 10
        max_warnings_until_ban = 20

        (_, user_name, context) = self.telegram.get_from_user_info(update, context)
        warning_message = (
            f"Sorry, @{user_name}, your request couldn't be processed due to the length of "
            f"your message or the characters you used. Currently, the bot supports prompts "
            f"up to 90 alphanumeric characters and words no longer than 20 characters. We "
            f"are working to extend these limits. For now, please keep your messages within "
            f"these parameters to ensure the bot operates smoothly. Repeatedly sending long "
            f"messages will lead to further warnings.\n\nIf you exceed "
            f"{max_message_format_interractions} such warnings in a day, they may count "
            f"towards a potential ban, as it suggests an attempt to disrupt the bot's "
            f"functions. Accumulating {max_warnings_until_ban} warnings within a single "
            f"day may result in permanent suspension from utilizing our bot."
        )
        return await self.__add_warning(
            "phrase_wrong_achievement_message",
            max_message_format_interractions,
            "incorrect_message_format",
            max_warnings_until_ban,
            warning_message,
            update,
            context
        )

    async def add_inappropriate_language_warning(
        self,
        update: Update,
        context: CallbackContext
    ) -> bool:
        """Adds a warning for use of inappropriate language in the achievement message"""
        max_warnings_until_ban = 20

        (_, user_name, context) = self.telegram.get_from_user_info(update, context)
        warning_message = (
            f'@{user_name}, this bot relies on external APIs that also perform profanity checks. '
            f'Frequent triggers of these checks could result in the suspension of the accounts '
            f'powering our services. We kindly request that you refrain from using inappropriate '
            f'language when interacting with the bot. Continued use of such language will result in '
            f'similar warnings. Accumulating {max_warnings_until_ban} warnings within a single day '
            f'may result in permanent suspension from utilizing our bot.'
        )
        return await self.__add_warning(
            "phrase_achievement_message",
            -1,
            "inappropriate_language_in_achievement_message",
            max_warnings_until_ban,
            warning_message,
            update,
            context
        )

    async def __add_warning(
        self,
        interraction_type: str,
        max_interractions: int,
        warning_type: str,
        warnings_limit: int,
        warning_message: str,
        update: Update,
        context: CallbackContext
    ) -> bool:
        (user_id, user_name, context) = self.telegram.get_from_user_info(update, context)
        (chat_id, _, _, context) = self.telegram.get_chat_info(update, context)

        warnings = 0
        if user_id not in LIST_OF_ADMINS:
            warnings = self.database.add_warning(
                user_id,
                chat_id,
                interraction_type,
                max_interractions,
                warning_type
            )

        if warnings > warnings_limit:
            self.database.ban(user_name)
            context = await self.telegram.reply_text(
                self.BAN_MESSAGE.format(user_name=user_name, warnings_limit=warnings_limit),
                update,
                context
            )
            return True

        if warnings > 0:
            context = await self.telegram.reply_text(warning_message, update, context)
            return True

        return False
