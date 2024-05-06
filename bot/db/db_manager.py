import os
import logging

from sqlalchemy.orm import Session, declarative_base, aliased
from sqlalchemy import create_engine, text, Column, Integer, String, BigInteger, Text, func

# Enable logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Base = declarative_base()


class ChatSticker(Base):
    __tablename__ = 'chat_achievements'

    id = Column(Integer, primary_key=True)
    file_id = Column(Text, comment="Telegram sticker id (not a primary since two different stickers might have the same id in telegram)")
    file_unique_id = Column(Text, comment="Telegram internal file id")
    type = Column(String, nullable=False, comment="(\'achievement\', \'description\' or \'empty\')")
    times_achieved = Column(Integer, comment="Number of times this achievement was taken (NULL if stickers type is not achievement)")
    index_in_sticker_set = Column(Integer, nullable=False, comment="The index of sticker in sticker set")
    chat_id = Column(BigInteger, nullable=False, comment="The chat ID")
    sticker_set_name = Column(Text, nullable=False, comment="The name of the sticker set")
    sticker_set_owner_id = Column(Integer, nullable=False, comment="The user ID of owner of sticker set")
    file_path = Column(Text, nullable=False, comment="Path to the sticker file source")

    def __repr__(self):
        return f"ChatSticker(\n\tid={self.id},\n\tfile_id={self.file_id},\n\tfile_unique_id={self.file_unique_id},\n\ttype={self.type},\n\ttimes_achieved={self.times_achieved},\n\tindex_in_sticker_set={self.index_in_sticker_set},\n\tchat_id={self.chat_id},\n\tsticker_set_name={self.sticker_set_name},\n\tsticker_set_owner_id={self.sticker_set_owner_id},\n\tfile_path={self.file_path}\n)"

class UserSticker(Base):
    __tablename__ = 'user_achievements'

    id = Column(Integer, primary_key=True)
    file_id = Column(Text, comment="Telegram sticker id (not a primary since two different stickers might have the same id in telegram)")
    file_unique_id = Column(Text, comment="Telegram internal file id")
    type = Column(String, nullable=False, comment="(\'achievement\', \'description\', \'profile\', \'profile_description\' or \'empty\')")
    index_in_sticker_set = Column(Integer, nullable=False, comment="The index of sticker in sticker set")
    user_id = Column(BigInteger, nullable=False, comment="The user ID")
    chat_id = Column(BigInteger, nullable=False, comment="The chat ID")
    sticker_set_name = Column(Text, nullable=False, comment="The name of the sticker set")
    file_path = Column(Text, nullable=False, comment="Path to the sticker file source")

    def __repr__(self):
        return f"UserSticker(\n\tid={self.id},\n\tfile_id={self.file_id},\n\tfile_unique_id={self.file_unique_id},\n\ttype={self.type},\n\tindex_in_sticker_set={self.index_in_sticker_set},\n\tuser_id={self.user_id},\n\tchat_id={self.chat_id},\n\tsticker_set_name={self.sticker_set_name},\n\tfile_path={self.file_path}\n)"

class DbManager:
    def __init__(self):
        db_user = os.environ['POSTGRES_USER']
        db_password = os.environ['POSTGRES_PASSWORD']
        db_name = os.environ['POSTGRES_DB']

        # SQLAlchemy setup
        self.engine = create_engine(f'postgresql://{db_user}:{db_password}@127.0.0.1:5432/{db_name}')
        base = declarative_base()
        base.metadata.create_all(self.engine)

        logger.info("Connected to PostgresQL postgresql://%s:%s@127.0.0.1:5432/%s", masked_print(db_user),
                    masked_print(db_password), db_name)

    # TODO: protect from SQL injections
    def save_prompt_message(self, chat_id, user_id, replied_user_id, message_text, prompt) -> None:
        session = Session(self.engine)
        session.execute(text(
            f"INSERT INTO achievement_messages(chat_id, invoking_user_id, target_user_id, message_text, prompt_text, timestamp) VALUES ('{chat_id}', '{user_id}', '{replied_user_id}', '{message_text}', '{prompt}', NOW())"))
        session.commit()
        session.close()

    def get_chat_sticker_set(self, chat_id: int) -> tuple[list[ChatSticker], Session]:
        session = Session(self.engine)
        result = (
            session.query(ChatSticker)
                .filter(ChatSticker.chat_id == chat_id)
                .order_by(ChatSticker.index_in_sticker_set)
                .all()
        )

        # We are forced to return session from here to allow manipulations over ChatSticker objects
        return result, session
    
    def get_user_sticker_set_for_chat(self, user_id: int, chat_id: int) -> tuple[list[UserSticker], Session]:
        session = Session(self.engine)
        result = (
            session.query(UserSticker)
                .filter(UserSticker.user_id == user_id)
                .filter(UserSticker.chat_id == chat_id)
                .order_by(UserSticker.index_in_sticker_set)
                .all()
        )

        # We are forced to return session from here to allow manipulations over UserSticker objects
        return result, session

    def get_chat_sticker_pack_name(self, chat_id: int) -> str:
        session = Session(self.engine)
        result = (
            session.query(ChatSticker.sticker_set_name)
                .filter(ChatSticker.chat_id == chat_id)
                .limit(1)
                .scalar()
        )
        session.commit()
        session.close()

        return result

    def create_chat_stickers_or_update_if_exist(self, chat_stickers_to_update: list[ChatSticker]):
        session = Session(self.engine)
        for sticker in chat_stickers_to_update:
            alias = aliased(ChatSticker)

            existing_sticker = (
                session.query(ChatSticker)
                    .filter(ChatSticker.chat_id == sticker.chat_id)
                    .filter(ChatSticker.index_in_sticker_set == sticker.index_in_sticker_set)
                    .first()
            )

            # If a matching record exists, update it; otherwise, create a new record
            if existing_sticker:
                existing_sticker.file_id = sticker.file_id
                existing_sticker.file_unique_id = sticker.file_unique_id
                existing_sticker.type = sticker.type
                existing_sticker.times_achieved = sticker.times_achieved
                existing_sticker.sticker_set_name = sticker.sticker_set_name
                existing_sticker.sticker_set_owner_id = sticker.sticker_set_owner_id
                existing_sticker.file_path = sticker.file_path
                session.merge(existing_sticker)
            else:
                session.add(sticker)

        session.commit()
        session.close()
    
    def create_user_stickers_or_update_if_exist(self, user_stickers_to_update: list[UserSticker]):
        session = Session(self.engine)
        for sticker in user_stickers_to_update:
            alias = aliased(UserSticker)

            existing_sticker = (
                session.query(UserSticker)
                    .filter(UserSticker.user_id == sticker.user_id)
                    .filter(UserSticker.chat_id == sticker.chat_id)
                    .filter(UserSticker.index_in_sticker_set == sticker.index_in_sticker_set)
                    .first()
            )

            # If a matching record exists, update it; otherwise, create a new record
            if existing_sticker:
                existing_sticker.file_id = sticker.file_id
                existing_sticker.file_unique_id = sticker.file_unique_id
                existing_sticker.type = sticker.type
                existing_sticker.sticker_set_name = sticker.sticker_set_name
                existing_sticker.file_path = sticker.file_path
                session.merge(existing_sticker)
            else:
                session.add(sticker)

        session.commit()
        session.close()

    def get_latest_achievement_index(self, chat_id: int) -> int:
        session = Session(self.engine)
        result = (
            session.query(func.max(ChatSticker.index_in_sticker_set))
                .filter(ChatSticker.type == 'achievement')
                .filter(ChatSticker.chat_id == chat_id)
                .scalar()
        )
        session.commit()
        session.close()
        return result

def masked_print(value: str) -> str:
    symbols_to_mask = int(0.8 * len(value))
    return value[:-symbols_to_mask] + 'X' * symbols_to_mask
