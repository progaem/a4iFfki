import os
import logging
import psycopg2
import boto3
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

class Bot:
    def __init__(self):
        self.updater = Updater(token=os.environ["TELEGRAM_BOT_TOKEN"], use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.init_handlers()
        self.db = psycopg2.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"]
        )
        self.s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["S3_ENDPOINT"],
            aws_access_key_id=os.environ["S3_ACCESS_KEY"],
            aws_secret_access_key=os.environ["S3_SECRET_KEY"]
        )

    def init_handlers(self):
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text, self.save_message))
        self.dispatcher.add_handler(MessageHandler(Filters.photo, self.save_photo))

    def start(self, update: Update, context: CallbackContext):
        update.message.reply_text("Hello! I'm your Telegram bot.")

    def save_message(self, update: Update, context: CallbackContext):
        message_text = update.message.text
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id

        with self.db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO messages (chat_id, user_id, message_text) VALUES (%s, %s, %s)",
                (chat_id, user_id, message_text)
            )
        self.db.commit()

    def save_photo(self, update: Update, context: CallbackContext):
        # Save the photo to S3
        chat_id = update.message.chat_id
        photo = update.message.photo[-1].get_file()
        file_id = photo.file_id
        file_path = file_id + ".jpg"
        photo.download(file_path)
        self.s3.upload_file(file_path, "your-s3-bucket", file_path)
        os.remove(file_path)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
