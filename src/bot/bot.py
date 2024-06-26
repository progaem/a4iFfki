"""
This module handles Telegram bot commands implementation
"""
import json
import html
import os
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, LinkPreviewOptions
from telegram._bot import BT
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.ext import filters

from api.telegram import TelegramAPI

from bot.access import LIST_OF_ADMINS, WarningsProcessor, restricted_to_admins, restricted_to_not_banned, restricted_to_stickerset_owners, restricted_to_supergroups, restricted_to_undefined_stickerset_chats, restricted_to_defined_stickerset_chats
from bot.stickers import StickerManager

from common.common import BaseClass
from common.utils import masked_print

from message.filter import LanguageFilter
from storage.s3 import ImageS3Storage
from sticker.artist import StickerArtist
from storage.postgres import PostgresDatabase, ChatSticker


class Bot(BaseClass):
    # pylint: disable=all
    DOCUMENTATION = [
        ("What is it?", "This is the Achievements Bot\.\nEver wanted to show appreciation for someone's _achievements_ in a chat? With this bot, you can create unique stickers representing their achievements and assign them directly\. Each chat will also have a sticker set to keep track of all the achievements awarded\."),
        ("Where are the stickers stored?", "Stickers are stored in specific Telegram sticker sets\. There's one sticker set for each person to track individual achievements, and another for the entire chat to monitor collective achievements\.\n\nTo manage these sets, one chat member must become the sticker set owner by sending /own\_stickers in the chat\.\n\nRemember, if you're the owner, DO NOT modify these stickers as it could disrupt the bot's functionality\."),
        ("How to give a new achievement?", "To award a new achievement, reply to a message in the chat, using a specific keyword to activate the bot\. The bot will recognize the keyword, process the achievement, and post stickers representing it—one from the individual's set and another from the chat's collective set\.\nThe stickers are AI\-generated based on the achievement's description\.\n\nCurrently, you can use phrases like `выдаю ачивку за \(текст достижения\)` or `drop an achievement for \(achievement message\)` to trigger the bot\.  \([Full list of key phrases](https://github.com/progaem/a4iFfki/blob/master/resources/key.txt)\)"),
        ("How to give an existing achievement?", "Simply reply to a message with an achievement sticker from the chat's collective sticker set\. Every time you award the same achievement to a new person, the count under each description sticker increases\."),
        ("FAQ", """>Why did I receive a warning for excessive bot usage?
    To operate within a limited budget, there are usage caps: you can only grant two achievements per person per day\. Exceeding this limit can lead to an automatic ban\.

>What if something goes wrong?
    If the bot malfunctions, please create a ticket in our GitHub repository detailing the steps to replicate the issue\. Your contributions to improving the bot are also welcome\! Link: https://github\.com/progaem/a4iFfki

>I see that order of stickers is messed up in the stickerset, what else could I do to fix it?
    Sorry to hear that, we are working on making the bot more resilient to errors in the updates\.\n\nFor now the only solution is to run /reset command \(_it's only available to stickerset owners_\) that would reset all the information about your stickers of your chat and start over :\(

>Is there a way I can support this project? ;\)
    Absolutely, and thanks for asking\! We recently set up a  [Buy Me a Coffee account](https://buymeacoffee.com/progaem), where you can support our project if you choose to\. Any support is entirely optional but greatly appreciated\! <3""")
    ]
    # pylint: enable=all
    
    DOCUMENTATION_BUTTON_PREFIX = "documentation"
    ASSIGN_CHAT_STICKERSET_BUTTON_PREFIX = "assign_chat"

    def __init__(
        self,
        database: PostgresDatabase,
        sticker_file_manager: ImageS3Storage,
        telegram: TelegramAPI,
        language_filter: LanguageFilter,
        warnings_processor: WarningsProcessor,
        sticker_artist: StickerArtist,
        sticker_manager: StickerManager
    ):
        super().__init__()
        self.telgram_bot_name = os.environ['TELEGRAM_BOT_NAME']

        self.database = database
        self.sticker_file_manager = sticker_file_manager
        
        self.telegram = telegram

        self.language_filter = language_filter

        self.warnings_processor = warnings_processor

        self.sticker_artist = sticker_artist
        self.sticker_manager = sticker_manager

        telegram_token = os.environ['TELEGRAM_BOT_TOKEN']
        self.application = Application.builder().token(telegram_token).build()
        self.logger.info("Telegram application was started with %s", masked_print(telegram_token))

    ### COMMANDS AVAILABLE ONLY TO ADMINS ###

    @restricted_to_supergroups
    @restricted_to_admins
    async def ban(self, update: Update, context: CallbackContext) -> None:
        """Bans a person from invoking a bot forever"""
        self.logger.info("[BOT] ban command was invoked")
        (message_text, context) = self.telegram.get_message(update, context)
        if '@' in message_text:
            user_name = message_text.split('@')[1]
            self.database.ban(user_name)
            context = await self.telegram.reply_text(
                f"@{user_name}, the admin has restricted your access to the bot",
                update,
                context
            )
        else:
            context = await self.telegram.reply_text(
                "In order to ban a user, invoke /ban command with the mention of the user that you intend to ban (e.g. /ban @username)",
                update,
                context
            )

    @restricted_to_supergroups
    @restricted_to_admins
    async def unban(self, update: Update, context: CallbackContext) -> None:
        """Unbans a person, lifting the restriction to invoke a bot"""
        self.logger.info("[BOT] unban command was invoked")
        (message_text, context) = self.telegram.get_message(update, context)
        if '@' in message_text:
            user_name = message_text.split('@')[1]
            self.database.unban(user_name)
            context = await self.telegram.reply_text(
                f"@{user_name}, the admin has lifted the restriction on your access to the bot",
                update,
                context
            )
        else:
            context = await self.telegram.reply_text(
                "In order to unban a user, invoke /unban command with the mention of the user that you intend to ban (e.g. /unban @username)",
                update,
                context
            )

    ### COMMANDS AVAILABLE ONLY TO STICKERSET OWNERS ###

    @restricted_to_supergroups
    @restricted_to_stickerset_owners
    async def reset(self, update: Update, context: CallbackContext) -> None:
        """Resets the achievements progress in the chat and deletes stickerset from the user"""
        (chat_id, _, _, context) = self.telegram.get_chat_info(update, context)
        (_, user_name, context) = self.telegram.get_from_user_info(update, context)

        self.logger.info(f"[BOT] reset command was invoked in the {chat_id} chat by user {user_name}")

        sticker_sets_to_remove = self.database.all_stickerset_names(chat_id)
        for sticker_set_name in sticker_sets_to_remove:
            context = await self.telegram.delete_sticker_set(sticker_set_name, update, context)

        files_to_remove = self.database.all_sticker_file_paths(chat_id)
        (_, _, _) = self.database.remove_all(chat_id)
        self.sticker_file_manager.remove_all(files_to_remove)
        
        context = await self.telegram.reply_text(
            f"@{user_name}, as per your request, all stickers for this chat were reset and sticker sets deleted. "
            f"Also you've been unassigned from sticker set owner role in this chat.\n\nAll bot features now "
            f"are unavailable again, until new sticker set owner would be chosen by /own_stickers command",
            update,
            context
        )

    @restricted_to_supergroups
    @restricted_to_stickerset_owners
    async def transfer(self, update: Update, context: CallbackContext) -> None:
        """Transfers sticker set to another person and makes them new stickerset owner"""
        pass

    ### COMMANDS AVAILABLE ONLY TO ALL USERS, ALL CHATS ###

    @restricted_to_not_banned
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Sends a greeting message with an interractive documentation message"""
        
        (chat_id, chat_type, _, context) = self.telegram.get_chat_info(update, context)
        (user_id, _, context) = self.telegram.get_from_user_info(update, context)

        self.logger.info(f"[BOT] start command was invoked in the {chat_id} chat by user {user_id} (chat type is {chat_type})")

        match chat_type:
            case "private":
                self.logger.info(f"[BOT] this start command appeared in the private chat")
                chats = self.database.get_chats_with_requested_stickerset_ownership(user_id)
                keyboard = [
                    [
                        InlineKeyboardButton(chat_name, callback_data=f"{self.ASSIGN_CHAT_STICKERSET_BUTTON_PREFIX}{chat_id}") for chat_name, chat_id in chats
                    ]
                ]
                context = await self.telegram.reply_text(
                    (
                        "Hello! Thank you for using our bot!\n\nThis bot is designed "
                        "for group chats only. However, in private messages, it helps "
                        "determine sticker ownership for the group chats where you have "
                        "requested stickerset ownership.\n\nHere is the list of chats "
                        "where you requested stickerset ownership within the last 24 hours."
                    ),
                    update,
                    context,
                    InlineKeyboardMarkup(keyboard),
                )
            
            case _:
                self.logger.info(f"[BOT] this start command appeared in the group chat")
                context = await self.telegram.reply_text(
                    (
                        "Hi there! Thank you for using our bot!\nHere's the "
                        "small documentation what it does and how it's working"
                    ),
                    update,
                    context
                )
                await self.__documentation_message(update, context)
                if not self.database.is_stickerset_owner_defined_for_chat(chat_id):
                    context = await self.telegram.send_message(
                        chat_id,
                        (
                            "*Reminder:*\n\nTo access additional features of the "
                            "bot beyond the /start and /help commands, _please "
                            "designate a sticker set owner for this chat_ by "
                            "using the /own\_stickers command"
                        ),
                        update,
                        context,
                        parse_mode=ParseMode.MARKDOWN_V2
                    )

    @restricted_to_supergroups
    @restricted_to_not_banned
    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Sends an interractive documentation message"""

        (user_id, _, context) = self.telegram.get_from_user_info(update, context)
        (chat_id, _, _, context) = self.telegram.get_chat_info(update, context)

        self.logger.info(f"[BOT] help command was invoked in the {chat_id} chat by user {user_id}")

        await self.__documentation_message(update, context)
        
        if not self.database.is_stickerset_owner_defined_for_chat(chat_id):
            context = await self.telegram.send_message(
                chat_id,
                (
                    "*Reminder:*\n\nTo access additional features of the bot beyond the /start and /help commands, "
                    "_please designate a sticker set owner for this chat_ by using the /own\_stickers command"
                ),
                update,
                context,
                parse_mode=ParseMode.MARKDOWN_V2
            )

    async def handle_button_updates(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles button updates:
        - For assign chat stickerset buttons:
        Attempts to assign user a role of stickerset owner for chosen chat
        
        - For documentation buttons:
        Modifies content of interractive documentation message when the user clicked selected different subtopic by pressing a button
        """
        context = await self.telegram.wait_for_query_answer(update, context)

        (query_text, context) = self.telegram.get_query_text(update, context)
        match query_text:
            case str(s) if self.DOCUMENTATION_BUTTON_PREFIX in s:
                keyboard = [[InlineKeyboardButton(content[0], callback_data=f"{self.DOCUMENTATION_BUTTON_PREFIX}{i}") for i, content in enumerate(self.DOCUMENTATION)]]
                context = await self.telegram.edit_query_message(
                    self.__format_documentation_page(int(s.split(self.DOCUMENTATION_BUTTON_PREFIX)[1])),
                    InlineKeyboardMarkup(keyboard),
                    update,
                    context
                )
            
            case str(s) if self.ASSIGN_CHAT_STICKERSET_BUTTON_PREFIX in s:
                chat_id = int(s.split(self.ASSIGN_CHAT_STICKERSET_BUTTON_PREFIX)[1])
                (user_id, user_name, context) = self.telegram.get_query_from_user_info(update, context)
                if self.database.assign_stickerset_owner(user_id, chat_id):
                    context = await self.telegram.send_message(
                        user_id,
                        "Congrats! Now you're the owner of this chat's stickerset!",
                        update,
                        context,
                        InlineKeyboardMarkup([])
                    )
                    context = await self.telegram.send_message(
                        chat_id,
                        (
                            f"Congrats, @{user_name} you've been assigned as a stickerset owner for this chat."
                            f"\n\nNow all other functions of the bot have been unblocked for this chat. "
                            f"For more information check /help command"
                        ),
                        update,
                        context
                    )
                else:
                    context = await self.telegram.send_message(
                        user_id,
                        (
                            "Sorry, but it turns out that the owner for this chat was already chosen. "
                            "Run /start command again to see your updated pending requests"
                        ),
                        update,
                        context,
                        InlineKeyboardMarkup([])
                    )
           
    ### COMMANDS AVAILABLE ONLY TO CHATS WITH UNDEFINED STICKERSET OWNERS ###

    @restricted_to_supergroups
    @restricted_to_not_banned
    @restricted_to_undefined_stickerset_chats
    async def own_stickers(self, update: Update, context: CallbackContext) -> None:
        """Makes a user invoking the command the owner of stickerset in the chat """
        (user_id, user_name, context) = self.telegram.get_from_user_info(update, context)
        (chat_id, _, chat_name, context) = self.telegram.get_chat_info(update, context)

        self.logger.info(f"[BOT] own_stickers command was invoked in the {chat_id} chat by user {user_id}")

        self.database.add_stickerset_owner_candidate(user_id, chat_id, chat_name)
        context = await self.telegram.reply_text(
            (
                f"@{user_name} you've send a request to become a stickerset owner for this chat."
                f"\n\nTo proceed, please send /start message to this bot in DM "
             ),
            update,
            context)

    ### COMMANDS AVAILABLE ONLY TO CHATS WITH DEFINED STICKERSET OWNERS AND UNBANNED USERS ###

    @restricted_to_supergroups
    @restricted_to_defined_stickerset_chats
    @restricted_to_not_banned
    async def show_sticker_set(self, update: Update, context: CallbackContext) -> None:
        """Sends a link to the sticker set of the user and the sticker set of this chat"""
        (user_id, user_name, context) = self.telegram.get_from_user_info(update, context)
        (chat_id, _, chat_name, context) = self.telegram.get_chat_info(update, context)

        self.logger.info(f"[BOT] show command was invoked in the {chat_id} chat by user {user_id}")

        if await self.warnings_processor.add_show_stickers_warning(update, context):
            return

        chat_stickerset_name = self.database.get_chat_sticker_set_name(chat_id)
        user_stickerset_name = self.database.get_user_sticker_set_name(user_id, chat_id)

        response = ""
        if chat_stickerset_name:
            response = f'Link to \'{chat_name}\'achievements: https://t.me/addstickers/{chat_stickerset_name}\n'
            if user_stickerset_name:
                response += f'Link to @{user_name}\'s achievements in the chat \'{chat_name}\': https://t.me/addstickers/{user_stickerset_name}'
            else:
                response += f'@{user_name} doesn\'t have any achievements in the chat \'{chat_name}\''
        else:
            response = f'Nobody in the chat \'{chat_name}\' has received an achievement yet'

        context = await self.telegram.reply_text(response, update, context)

    @restricted_to_supergroups
    @restricted_to_defined_stickerset_chats
    @restricted_to_not_banned
    async def on_give(self, update: Update, context: CallbackContext) -> None:
        """Gives an achievement to a person in reply message"""
        message_text = update.message.text
        (message_text, context) = self.telegram.get_message(update, context)
        (from_user_id, from_user_name, context) = self.telegram.get_from_user_info(update, context)
        (to_user_id, to_user_name, context) = self.telegram.get_to_user_info(update, context)
        (chat_id, _, chat_name, context) = self.telegram.get_chat_info(update, context)
        self.logger.info(f"[BOT] {from_user_id} in {chat_id} mentioned key word replying to {to_user_id} message: {message_text}")

        prompt = self.language_filter.detect_prompt(message_text)
        if not prompt:
            context = await self.telegram.reply_text(
                (
                    f"User @{from_user_name} mentioned one of the achievement granting key words in their reply "
                    f"to @{to_user_name}! But prompt was not identified :("
                ),
                update,
                context
            )
            return

        if self.language_filter.check_for_inappropriate_language(prompt):
            await self.warnings_processor.add_inappropriate_language_warning(update)
            return

        if self.language_filter.check_for_message_format(prompt):
            await self.warnings_processor.add_message_format_warning(update, context)
            return

        if await self.warnings_processor.add_give_achievement_warning(update, context):
            return

        self.database.save_prompt_message(chat_id, from_user_id, to_user_id, message_text, prompt)

        # if sticker already exists we want to use it (not create another one)
        achievement_sticker_info, description_sticker_info, session = await self.sticker_manager.find_existing_sticker(chat_id, prompt)
        if achievement_sticker_info: # would be null if there is no such sticker
            await self.__give_user_existing_achievement(
                to_user_id, to_user_name, chat_id, from_user_name, chat_name, 
                achievement_sticker_info, description_sticker_info, update, context
            )
            session.commit()
            session.close()
            return
        session.commit()
        session.close()

        # fetch the sticker owner for this chat
        stickers_owner_id = self.database.get_stickerset_owner(chat_id)

        # generate all needed stickers
        achievement_sticker = await self.sticker_artist.draw_sticker_from_prompt(prompt)
        chat_description_sticker = self.sticker_artist.draw_chat_description_sticker(prompt, 1)
        user_description_sticker = self.sticker_artist.draw_description_sticker(prompt)

        # update sticker sets
        achievement_description_chat_sticker_file_id = await self.sticker_manager.add_chat_stickers(
            stickers_owner_id,
            chat_id, chat_name,
            achievement_sticker,
            chat_description_sticker,
            prompt,
            update,
            context)
        achievement_user_sticker_file_id = await self.sticker_manager.add_user_stickers(
            stickers_owner_id,
            to_user_id,
            to_user_name,
            chat_id,
            chat_name,
            achievement_sticker,
            user_description_sticker,
            prompt,
            update,
            context)

        await self.__respond_with_achievement_stickers(
            update,
            context,
            from_user_name,
            to_user_name,
            chat_name,
            chat_id,
            prompt,
            achievement_user_sticker_file_id,
            achievement_description_chat_sticker_file_id)

    @restricted_to_supergroups
    @restricted_to_defined_stickerset_chats
    @restricted_to_not_banned
    async def on_sticker_reply(self, update: Update, context: CallbackContext) -> None:
        """Gives an existing achievement to a person in reply message"""
        (sticker_file_id, context) = self.telegram.get_sticker_file_id(update, context)
        (_, from_user_name, context) = self.telegram.get_from_user_info(update, context)
        (to_user_id, to_user_name, context) = self.telegram.get_to_user_info(update, context)
        (chat_id, _, chat_name, context) = self.telegram.get_chat_info(update, context)

        self.logger.info(f"[BOT] on_reply command was invoked in the {chat_id} chat by user {from_user_name}")

        (chat_sticker_set_info, session) = self.database.get_chat_sticker_set(chat_id)
        stickers_to_types = {s.file_unique_id: (s.type, s.index_in_sticker_set) for s in chat_sticker_set_info}

        # check if the sticker was from the chat stickerset
        if sticker_file_id in stickers_to_types:
            (sticker_type, sticker_index) = stickers_to_types[sticker_file_id]
            
            if sticker_type == 'achievement':
                if await self.warnings_processor.add_give_achievement_warning(update, context):
                    session.close()
                    return

                # retrieve mentioned achievement and it's description stickers
                index_based_lookup = {s.index_in_sticker_set: s for s in chat_sticker_set_info}
                achievement_sticker_info = index_based_lookup[sticker_index]
                description_sticker_info = index_based_lookup[sticker_index + 5]

                await self.__give_user_existing_achievement(
                    to_user_id, to_user_name, chat_id, from_user_name, chat_name, 
                    achievement_sticker_info, description_sticker_info, update, context
                )
            elif sticker_type == 'empty':
                context = await self.telegram.reply_text(
                    "This achievement is not unblocked yet, so you can't give it to someone else!",
                    update,
                    context
                )

        session.commit()
        session.close()

    async def __give_user_existing_achievement(
        self,
        to_user_id: int, 
        to_user_name: str,
        chat_id: int, 
        from_user_name: str, 
        chat_name: str, 
        achievement_sticker_info: ChatSticker, 
        description_sticker_info: ChatSticker, 
        update: Update, 
        context: CallbackContext
    ):
        """
        Gives an existing achievement to a person.
        Used in 2 scenarios: 
            - (1) in on_give method if there is existing sticker with the same prompt
            - (2) in on_sticker_reply method if a user replies with an existing achievement sticker
        """
        achievement_sticker = self.sticker_file_manager.get_bytes_from_path(achievement_sticker_info.file_path)
        user_description_sticker = self.sticker_artist.draw_description_sticker(description_sticker_info.engraving_text)
        # add and update stickers
        achievement_user_sticker_file_id = await self.sticker_manager.add_user_stickers(
            description_sticker_info.sticker_set_owner_id,
            to_user_id,
            to_user_name,
            chat_id,
            chat_name,
            (achievement_sticker_info.file_path, achievement_sticker),
            user_description_sticker,
            description_sticker_info.engraving_text,
            update,
            context
        )
        achievement_description_chat_sticker_file_id = await self.sticker_manager.increase_counter_on_chat_description_sticker(
            description_sticker_info.sticker_set_owner_id,
            chat_id,
            description_sticker_info.file_id,
            description_sticker_info.sticker_set_name,
            description_sticker_info.index_in_sticker_set,
            description_sticker_info.engraving_text,
            description_sticker_info.times_achieved,
            update,
            context
        )
        await self.__respond_with_achievement_stickers(update, context, from_user_name, to_user_name, chat_name, chat_id, description_sticker_info.engraving_text, achievement_user_sticker_file_id, achievement_description_chat_sticker_file_id)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Global error handler for all errors that appear in the application"""
        self.logger.error("Exception while handling an update:", exc_info=context.error)

        # pylint: disable=fixme
        # TODO: track error causes
        
        # pylint: disable=fixme
        # TODO: try rolling back the commited changes to snapshot done before the command

        # as last resort notify developers about the failure
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            "An exception was raised while handling an update\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
            "</pre>\n\n"
            f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
            f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
            f"<pre>{html.escape(tb_string)}</pre>"
        )
        for admin_chat_id in LIST_OF_ADMINS:
            context = await self.telegram.send_message(
                admin_chat_id,
                message,
                update,
                context,
                parse_mode=ParseMode.HTML
            )

    def __format_documentation_page(self, documentation_page_num: int) -> str:
        return f"*{self.DOCUMENTATION[documentation_page_num][0]}*\n\n{self.DOCUMENTATION[documentation_page_num][1]}"

    async def __documentation_message(self, update: Update, context: CallbackContext) -> None:
        keyboard = [[InlineKeyboardButton(content[0], callback_data=f"{self.DOCUMENTATION_BUTTON_PREFIX}{i}") for i, content in enumerate(self.DOCUMENTATION)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context = await self.telegram.reply_text(
            self.__format_documentation_page(0),
            update,
            context,
            keyboard=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def __respond_with_achievement_stickers(
        self,
        update: Update,
        context: CallbackContext,
        user_from_username: str,
        user_to_username: str,
        chat_name: str,
        chat_id: int,
        prompt: str,
        achievement_user_sticker_file_id: str,
        achievement_description_chat_sticker_file_id: str
    ) -> None:
        context = await self.telegram.reply_text(
            f'Congrats @{user_to_username} you just received an achievement from @{user_from_username} in \'{chat_name}\' chat for \'{prompt}\'',
            update,
            context
        )
        context = await self.telegram.send_sticker(
            chat_id,
            achievement_user_sticker_file_id,
            update,
            context
        )
        context = await self.telegram.send_sticker(
            chat_id,
            achievement_description_chat_sticker_file_id,
            update,
            context
        )

    def run(self):
        """Handles bot initialization, binding all commands to their implementations and starting the Telegram bot"""
        # admin-only commands
        self.application.add_handler(CommandHandler("ban", self.ban))
        self.application.add_handler(CommandHandler("unban", self.unban))

        # sticker set owners-only commands
        self.application.add_handler(CommandHandler("reset", self.reset))
        
        # default commands
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_button_updates))

        # undefined stickerset chat commands
        self.application.add_handler(CommandHandler("own_stickers", self.own_stickers))

        # public commands
        self.application.add_handler(CommandHandler("show", self.show_sticker_set))
        self.application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & (self.language_filter.construct_message_filter()), self.on_give))
        self.application.add_handler(MessageHandler(filters.REPLY & filters.Sticker.ALL, self.on_sticker_reply))

        # error handling
        self.application.add_error_handler(self.error_handler)

        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
