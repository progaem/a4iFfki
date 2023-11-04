class Message:
    def __init__(self, id, chat_id, user_id, message_text, timestamp):
        self.id = id
        self.chat_id = chat_id
        self.user_id = user_id
        self.message_text = message_text
        self.timestamp = timestamp
