import os
import logging

from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import create_engine, text
from typing import Optional

# Enable logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChatSticker:
    def __init__(self, file_id: str, file_unique_id: str, type: str, times_achieved: Optional[int], index_in_sticker_pack: int, chat_id: int, chat_sticker_pack_name: str, sticker_pack_owner_id: int, file_path: str):
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.type = type
        self.times_achieved = times_achieved
        self.index_in_sticker_pack = index_in_sticker_pack
        self.chat_id = chat_id
        self.chat_sticker_pack_name = chat_sticker_pack_name
        self.sticker_pack_owner_id = sticker_pack_owner_id
        self.file_path = file_path


# TODO: protect from SQL injections
class DbManager:
    def __init__(self):
        db_user = os.environ['POSTGRES_USER']
        db_password = os.environ['POSTGRES_PASSWORD']
        db_name = os.environ['POSTGRES_DB']

        # SQLAlchemy setup
        self.engine = create_engine(f'postgresql://{db_user}:{db_password}@0.0.0.0/{db_name}')
        base = declarative_base()
        base.metadata.create_all(self.engine)

        logger.info("Connected to PostgresQL postgresql://%s:%s@localhost/%s", masked_print(db_user),
                    masked_print(db_password), db_name)

    def save_prompt_message(self, chat_id, user_id, replied_user_id, message_text, prompt) -> None:
        session = Session(self.engine)
        session.execute(text(
            f"INSERT INTO achievement_messages(chat_id, invoking_user_id, target_user_id, message_text, prompt_text, timestamp) VALUES ('{chat_id}', '{user_id}', '{replied_user_id}', '{message_text}', '{prompt}', NOW())"))
        session.commit()
        session.close()

    def get_chat_sticker_pack_name(self, chat_id: int) -> str:
        pass

    def get_user_sticker_pack_name(self, user_id: int, chat_id: int) -> str:
        pass

    def create_stickers(self, chat_stickers_to_update: list[ChatSticker]):
        pass


def masked_print(value: str) -> str:
    symbols_to_mask = int(0.8 * len(value))
    return value[:-symbols_to_mask] + 'X' * symbols_to_mask
