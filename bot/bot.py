#!/usr/bin/env python
import logging
from html import escape
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, token, db_session):
        self.application = Application.builder().token(token).build()
        self.db_session = db_session

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        await update.message.reply_text("Hi!")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text("Help!")

    async def inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the inline query. This is run when you type: @botusername <query>"""

        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        user_message = update.message.text

        # Insert the message into the database
        self.db_session.execute(
            "INSERT INTO messages(chat_id, user_id, message_text, timestamp) VALUES (:id, :chat_id, :user_id, :message_text, NOW())",
            {"id": chat_id, "chat_id": chat_id, "user_id": user_id, "message_text": user_message})

        query = update.inline_query.query

        if not query:  # empty query should not be handled
            return

        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Caps",
                input_message_content=InputTextMessageContent(query.upper()),
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Bold",
                input_message_content=InputTextMessageContent(
                    f"<b>{escape(query)}</b>", parse_mode=ParseMode.HTML
                ),
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Italic",
                input_message_content=InputTextMessageContent(
                    f"<i>{escape(query)}</i>", parse_mode=ParseMode.HTML
                ),
            ),
        ]

        await update.inline_query.answer(results)

    def run(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # on inline queries - show corresponding inline results
        self.application.add_handler(InlineQueryHandler(self.inline_query))

        # Run the bot until the user presses Ctrl-C
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
