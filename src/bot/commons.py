import random
import string

def generate_sticker_set_name(prefix_name: str, bot_name: str):
    # Note: As per telegram API documentation https://docs.python-telegram-bot.org/en/v20.6/telegram.bot.html#telegram.Bot.create_new_sticker_set:
    # Stickerpack name can contain only english letters, digits and underscores.
    # Must begin with a letter, can’t contain consecutive underscores and must end in “_by_<bot username>”. <bot_username> is case insensitive.
    # 1 - 64 characters.
    if not prefix_name or not prefix_name[0].isalpha():
        raise ValueError('Sticker pack should start with letter')
    sticker_pack_name_length = 16
    sticker_pack_name_to_generate = sticker_pack_name_length - len(prefix_name)
    sticker_pack_prefix = ''.join(
        random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=sticker_pack_name_to_generate))
    return f"{prefix_name}{sticker_pack_prefix}_by_{bot_name}"