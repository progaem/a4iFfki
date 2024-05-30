"""
This module handles all interractions with PostgreSQL database
"""
import os
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, declarative_base, aliased
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Text, DateTime, func

from common.common import BaseClass

Base = declarative_base()

class AchievementMessage(Base):
    __tablename__ = 'achievement_messages'

    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, nullable=False, comment="The chat Id")
    invoking_user_id = Column(
        BigInteger,
        nullable=False,
        comment="The user ID of a peron who invoked give achievement command")
    target_user_id = Column(
        BigInteger,
        nullable=False,
        comment="The user ID of a person who was targeted for an achievement")
    message_text = Column(Text, nullable=False, comment="The message text")
    prompt_text = Column(
        Text,
        nullable=False,
        comment="Detected prompt text (null if the prompt was unknown)")
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the message")

    def __repr__(self):
        return (
                f"AchievementMessage(\n\tid={self.id},\n\tchat_id={self.chat_id},\n"
                f"\tinvoking_user_id={self.invoking_user_id},\n\ttarget_user_id={self.target_user_id},\n"
                f"\tmessage_text={self.message_text},\n\tprompt_text={self.prompt_text},\n"
                f"\ttimestamp={self.timestamp})")

class ChatSticker(Base):
    __tablename__ = 'chat_achievements'

    id = Column(Integer, primary_key=True)
    file_id = Column(
        Text,
        comment="Telegram sticker id (not a primary since two different stickers might have the same id in telegram)")
    file_unique_id = Column(Text, comment="Telegram internal file id")
    type = Column(
        String,
        nullable=False,
        comment="(\'achievement\', \'description\' or \'empty\')")
    engraving_text = Column(
        Text,
        comment="Engraving on a sticker (empty for every sticker not of description type)")
    times_achieved = Column(
        Integer,
        comment="Number of times this achievement was taken (NULL if stickers type is not description)")
    index_in_sticker_set = Column(Integer, nullable=False, comment="The index of sticker in sticker set")
    chat_id = Column(BigInteger, nullable=False, comment="The chat ID")
    sticker_set_name = Column(Text, nullable=False, comment="The name of the sticker set")
    sticker_set_owner_id = Column(Integer, nullable=False, comment="The user ID of owner of sticker set")
    file_path = Column(Text, nullable=False, comment="Path to the sticker file source")

    def __repr__(self):
        return (
                f"ChatSticker(\n\tid={self.id},\n\tfile_id={self.file_id},\n"
                f"\tfile_unique_id={self.file_unique_id},\n\ttype={self.type},\n"
                f"\ttimes_achieved={self.times_achieved},\n\tindex_in_sticker_set={self.index_in_sticker_set},\n"
                f"\tchat_id={self.chat_id},\n\tsticker_set_name={self.sticker_set_name},\n"
                f"\tsticker_set_owner_id={self.sticker_set_owner_id},\n\tfile_path={self.file_path}\n)")

class UserSticker(Base):
    __tablename__ = 'user_achievements'

    id = Column(Integer, primary_key=True)
    file_id = Column(
        Text,
        comment="Telegram sticker id (not a primary since two different stickers might have the same id in telegram)")
    file_unique_id = Column(Text, comment="Telegram internal file id")
    type = Column(
        String,
        nullable=False,
        comment="(\'achievement\', \'description\', \'profile\', \'profile_description\' or \'empty\')")
    engraving_text = Column(Text, comment="Engraving on a sticker (empty for every sticker not of description type)")
    index_in_sticker_set = Column(Integer, nullable=False, comment="The index of sticker in sticker set")
    user_id = Column(BigInteger, nullable=False, comment="The user ID")
    chat_id = Column(BigInteger, nullable=False, comment="The chat ID")
    sticker_set_name = Column(Text, nullable=False, comment="The name of the sticker set")
    file_path = Column(Text, nullable=False, comment="Path to the sticker file source")

    def __repr__(self):
        return (
                f"UserSticker(\n\tid={self.id},\n\tfile_id={self.file_id},\n"
                f"\tfile_unique_id={self.file_unique_id},\n\ttype={self.type},\n"
                f"\tindex_in_sticker_set={self.index_in_sticker_set},\n\tuser_id={self.user_id},\n"
                f"\tchat_id={self.chat_id},\n\tsticker_set_name={self.sticker_set_name},\n"
                f"\tfile_path={self.file_path}\n)")

class WarningMessage(Base):
    
    __tablename__ = 'warnings'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, comment="The user ID of a peron who received warning")
    chat_id = Column(BigInteger, nullable=False, comment="The chat ID")
    interraction_type = Column(Text, nullable=True, comment="The type of interraction user had with the bot")
    warning_type = Column(
        Text,
        nullable=True,
        comment="The type of warnings that was given to the user (If null - the entry means just an invocation)")
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the warning")

    def __repr__(self):
        return (
                f"WarningMessage(\n\tid={self.id},\n\tuser_id={self.user_id},\n"
                f"\tchat_id={self.chat_id},\n\tinterraction_type={self.interraction_type},\n"
                f"\twarning_type={self.warning_type},\n\ttimestamp={self.timestamp})")

class BannedUser(Base):
    __tablename__ = 'banned_users'

    username = Column(Text, nullable=False, primary_key=True, comment="the username")
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="The timestamp of the ban")

    def __repr__(self):
        return f"BannedUser(\n\tusername={self.username},\n\ttimestamp={self.timestamp})"

class StickersetOwner(Base):
    __tablename__ = 'stickerset_owners'

    user_id = Column(Text, nullable=False, comment="the stickerset owner ID")
    chat_id = Column(BigInteger, nullable=False, primary_key=True, comment="The chat ID")

    def __repr__(self):
        return f"StickersetOwner(\n\tuser_id={self.user_id},\n\tchat_id={self.chat_id})"

class PostgresDatabase(BaseClass):
    def __init__(self):
        db_user = os.environ['POSTGRES_USER']
        db_password = os.environ['POSTGRES_PASSWORD']
        db_name = os.environ['POSTGRES_DB']

        self.engine = create_engine(f'postgresql://{db_user}:{db_password}@postgres/{db_name}')
        Base.metadata.create_all(self.engine)

        self.logger.info("Connected to Postgres")

    def save_prompt_message(
        self,
        chat_id,
        user_id,
        replied_user_id,
        message_text,
        prompt
    ) -> None:
        """Adds the text to the list of achievement messages"""
        session = Session(self.engine)
        achievement = AchievementMessage(
            chat_id = chat_id,
            invoking_user_id = user_id,
            target_user_id = replied_user_id,
            message_text = message_text,
            prompt_text = prompt)
        session.add(achievement)
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

        # We are forced to return session from here
        #   to allow manipulations over ChatSticker objects
        return result, session

    def get_user_sticker_set_for_chat(self, user_id: int, chat_id: int) -> tuple[list[UserSticker], Session]:
        """"Gets ordered list of user's stickers for the chat"""
        session = Session(self.engine)
        result = (
            session.query(UserSticker)
                .filter(UserSticker.user_id == user_id)
                .filter(UserSticker.chat_id == chat_id)
                .order_by(UserSticker.index_in_sticker_set)
                .all()
        )

        # We are forced to return session from here
        #   to allow manipulations over UserSticker objects
        return result, session

    def get_chat_sticker_set_name(self, chat_id: int) -> str:
        """Gets stickerset owner from chat's sticker"""
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

    def get_user_sticker_set_name(self, user_id: int, chat_id: int) -> str:
        """Gets stickerset name from user's sticker for this chat"""
        session = Session(self.engine)
        result = (
            session.query(UserSticker.sticker_set_name)
                .filter(UserSticker.user_id == user_id)
                .filter(UserSticker.chat_id == chat_id)
                .limit(1)
                .scalar()
        )
        session.commit()
        session.close()

        return result

    def create_chat_stickers_or_update_if_exist(self, chat_stickers_to_update: list[ChatSticker]):
        """Adds stickers to the list of chat stickers"""
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
                existing_sticker.engraving_text = sticker.engraving_text
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
        """Adds stickers to the list of user stickers"""
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
                existing_sticker.engraving_text = sticker.engraving_text
                existing_sticker.sticker_set_name = sticker.sticker_set_name
                existing_sticker.file_path = sticker.file_path
                session.merge(existing_sticker)
            else:
                session.add(sticker)

        session.commit()
        session.close()

    def get_latest_achievement_index(self, chat_id: int) -> int:
        """Gets the maximum of sticker set indices across chat stickers with type achievement"""
        session = Session(self.engine)
        result = (
            session.query(func.max(ChatSticker.index_in_sticker_set))
                .filter(ChatSticker.type == 'achievement')
                .filter(ChatSticker.chat_id == chat_id)
                .scalar()
        )
        session.commit()
        session.close()
        return int(result)
    
    def get_stickerset_owner(self, chat_id: int) -> int | None:
        """Gets sticker set owner's id for the chat"""
        session = Session(self.engine)
        stickerset_owner_id = (
            session.query(StickersetOwner.user_id)
                .filter(StickersetOwner.chat_id == chat_id)
                .limit(1)
                .scalar()
        )
        session.commit()
        session.close()
        return stickerset_owner_id

    def define_stickerset_owner(self, user_id: int, chat_id: int) -> None:
        """Adds user to the list of sticker set owners for the chat"""
        session = Session(self.engine)
        session.add(StickersetOwner(user_id=user_id, chat_id=chat_id))
        session.commit()
        session.close()
        return

    def is_stickerset_owner_defined_for_chat(self, chat_id: int) -> bool:
        """Returns boolean whether there is any sticker set owner for this chat"""
        session = Session(self.engine)
        stickerset_owner_rows = (
            session.query(StickersetOwner.user_id)
                .filter(StickersetOwner.chat_id == chat_id)
                .count()
        )
        session.commit()
        session.close()
        return stickerset_owner_rows != 0

    def all_stickerset_names(self, chat_id: int) -> list[str]:
        """Returns the list of all sticker set names related to this chat"""
        session = Session(self.engine)
        chat_sticker_set_names = [
            result[0] for result in (
                session.query(ChatSticker.sticker_set_name)
                    .distinct()
                    .filter(ChatSticker.chat_id == chat_id)
                    .all()
            )
        ]
        user_sticker_set_names = [
            result[0] for result in (
                session.query(UserSticker.sticker_set_name)
                    .distinct()
                    .filter(UserSticker.chat_id == chat_id)
                    .all()
            )
        ]
        session.commit()
        session.close()

        return chat_sticker_set_names + user_sticker_set_names

    def all_sticker_file_paths(self, chat_id: int) -> list[str]:
        """Returns the list of S3 files related to the chat"""
        session = Session(self.engine)

        chat_stickerset_files = [
            result[0] for result in (
                session.query(ChatSticker.file_path)
                    .filter(ChatSticker.chat_id == chat_id)
                    .all()
            )
        ]
        user_stickerset_files = [
            result[0] for result in (
                session.query(UserSticker.file_path)
                    .filter(UserSticker.chat_id == chat_id)
                    .all()
            )
        ]

        session.commit()
        session.close()

        return chat_stickerset_files + user_stickerset_files

    def remove_all(self, chat_id: int) -> tuple[str, str, str]:
        """Removes all data related to the chat"""
        session = Session(self.engine)

        deleted_chat_stickers = (
            session.query(ChatSticker)
                .filter(ChatSticker.chat_id == chat_id)
                .delete()
        )
        deleted_user_stickers = (
            session.query(UserSticker)
                .filter(UserSticker.chat_id == chat_id)
                .delete()
        )
        deleted_sticker_set_owners = (
            session.query(StickersetOwner)
                .filter(StickersetOwner.chat_id == chat_id)
                .delete()
        )

        session.commit()
        session.close()
        return (deleted_chat_stickers, deleted_user_stickers, deleted_sticker_set_owners)

    def add_warning(
        self,
        user_id: int,
        chat_id: int,
        interraction_type: str,
        max_attempts: int,
        warning_type: str) -> int:
        """Counts how many invocations of the type {interraction_type} user had with the bot.

        if it exceeded {max_attempts}, the warning of the type {warning_type} will be added
            to the user
        """
        session = Session(self.engine)

        twenty_four_hours_ago = datetime.now() - timedelta(days=1)

        entries_count_without_warning_type = (
            session.query(WarningMessage)
                .filter(WarningMessage.user_id == user_id)
                .filter(WarningMessage.interraction_type == interraction_type)
                .filter(WarningMessage.timestamp >= twenty_four_hours_ago)
                .filter(WarningMessage.warning_type == None).count()
        )

        count_entries = 0

        if entries_count_without_warning_type >= max_attempts:
            session.add(
                WarningMessage(
                    user_id=user_id,
                    chat_id=chat_id,
                    interraction_type=interraction_type,
                    warning_type=warning_type))
            session.commit()
            count_entries = (
                session.query(WarningMessage)
                    .filter(WarningMessage.user_id == user_id)
                    .filter(WarningMessage.interraction_type == interraction_type)
                    .filter(WarningMessage.timestamp >= twenty_four_hours_ago) 
                    .filter(WarningMessage.warning_type == warning_type).count()
            )
        session.add(
            WarningMessage(
                user_id=user_id,
                chat_id=chat_id,
                interraction_type=interraction_type
        ))

        session.commit()
        session.close()

        return count_entries

    def ban(self, username: str) -> None:
        """Adds user to the list of banned users"""
        session = Session(self.engine)
        session.add(BannedUser(username=username))
        session.commit()
        session.close()

    def unban(self, username: str) -> bool:
        """Removes user from the list of banned users"""
        session = Session(self.engine)
        deleted_count = (
            session.query(BannedUser)
                .filter(BannedUser.username == username)
                .delete())
        session.commit()
        session.close()
        return deleted_count != 0

    def is_banned(self, username: str) -> Optional[datetime]:
        """Returns the timestamp of the user's ban or None if they were not banned"""
        session = Session(self.engine)
        ban_timestamp = (
            session.query(BannedUser.timestamp)
                .filter(BannedUser.username == username)
                .first()
        )
        session.commit()
        session.close()
        return ban_timestamp
