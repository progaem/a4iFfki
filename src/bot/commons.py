import random
import string

def generate_sticker_set_name_and_title(stickerset_type: str, bot_name: str, username: str, chat_name: str) -> tuple[str, str]:
    """Creates a pair of name and title for user or chat stickerset"""
    assert stickerset_type in ("CHAT", "USER")
    
    sticker_set_name = generate_sticker_set_name(stickerset_type.lower(), bot_name)
    sticker_set_title = f"'{chat_name}"[:62] + "' achievements" if stickerset_type == "CHAT" else f"{username}'s achievements in '{chat_name}"[:62] + "'"
    
    return (sticker_set_name, sticker_set_title)

def generate_sticker_set_name(prefix_name: str, bot_name: str):
    """Creates a name for sticker set according to Telegram API restrictions:
    https://docs.python-telegram-bot.org/en/v20.6/telegram.bot.html#telegram.Bot.create_new_sticker_set
    """
    if not prefix_name or not prefix_name[0].isalpha():
        raise ValueError('Sticker pack should start with letter')
    sticker_pack_name_length = 16
    sticker_pack_name_to_generate = sticker_pack_name_length - len(prefix_name)
    sticker_pack_prefix = ''.join(
        random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=sticker_pack_name_to_generate))
    return f"{prefix_name}{sticker_pack_prefix}_by_{bot_name}"