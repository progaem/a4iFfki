import logging

from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext

from storage.postgres import PostgresDatabase

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

### HELPER COMMANDS, RESTRICTING VISBILITY TO METHODS ###

# TODO: add Misha
LIST_OF_ADMINS = [249427415]

def restricted_to_admins(func):
    """Restricts the usage of the command to admins of the bot"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.message.from_user.id
        if user_id not in LIST_OF_ADMINS:
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

def restricted_to_not_banned(func):
    """Restricts the usage of the command to admins of the bot"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        user_name = update.message.from_user.username
        if bot.database.is_banned(user_name):
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

def restricted_to_stickerset_owners(func):
    """Restricts the usage of the command to stickerset owners"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        if bot.database.get_stickerset_owner(chat_id) != user_id:
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

def restricted_to_undefined_stickerset_chats(func):
    """Restricts the usage of the command to chats without defined stickerset owners"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        chat_id = update.message.chat_id
        if bot.database.is_stickerset_owner_defined_for_chat(chat_id):
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

def restricted_to_defined_stickerset_chats(func):
    """Restricts the usage of the command to chats only with defined stickerset owners"""
    @wraps(func)
    async def wrapped(bot, update: Update, context: CallbackContext, *args, **kwargs):
        chat_id = update.message.chat_id
        if not bot.database.is_stickerset_owner_defined_for_chat(chat_id):
            return
        return await func(bot, update, context, *args, **kwargs)
    return wrapped

class WarningsProcessor:
    BAN_MESSAGE = "@{user_name} you exceeded the limit of {warnings_limit}, so as we warned previously, we permanently ban you from utilizing this bot"
    
    def __init__(self, database: PostgresDatabase):
        self.database = database
    
    async def add_show_stickers_warning(self, update: Update) -> bool:
        max_show_stickers_interractions = 20
        max_warnings_until_ban = 5
        
        username = update.message.from_user.username 
        warning_message = f'@{username}, we\'ve noticed unusual activity from your account, currently there is a limit of {max_show_stickers_interractions} daily /show executions per individual. Exceeding this limit will prompt notifications such as this one. Accumulating {max_warnings_until_ban} warnings of this nature within a single day may result in permanent suspension from utilizing our bot.'
        return await self.__add_warning(update, "show_stickers", max_show_stickers_interractions, "show_stickers_invocations_exceed", max_warnings_until_ban, warning_message)
    
    async def add_give_achievement_warning(self, update: Update) -> bool:
        max_give_achievement_interractions = 2
        max_warnings_until_ban = 5
        
        username = update.message.from_user.username 
        warning_message = f'Achievements are like rare jewels scattered throughout our lives, precious and unique. It\'s crucial to cherish their scarcity and significance. That\'s why we\'ve imposed a limit of {max_give_achievement_interractions} daily executions per individual. Exceeding this limit will prompt notifications such as this one. Accumulating {max_warnings_until_ban} warnings of this nature within a single day may result in permanent suspension from utilizing our bot. @{username}, we kindly ask for your cooperation in adhering to these guidelines.'
        return await self.__add_warning(update, "new_achievement", max_give_achievement_interractions, "new_achievement_invocations_exceed", max_warnings_until_ban, warning_message)
        
    async def __add_warning(self, update: Update, interraction_type: str, max_interractions: int, warning_type: str, warnings_limit: int, warning_message: str) -> bool:
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username

        warnings = 0
        if user_id not in LIST_OF_ADMINS:
            warnings = self.database.add_warning(user_id, chat_id, interraction_type, max_interractions, warning_type)

        if warnings > warnings_limit:
            self.database.ban(user_name)
            await update.message.reply_text(self.BAN_MESSAGE.format(user_name=user_name, warnings_limit=warnings_limit))
            return True
        elif warnings > 0:
            await update.message.reply_text(warning_message)
            return True
        else:
            return False