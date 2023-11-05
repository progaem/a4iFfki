class PromptDetector:
    def __init__(self):
        pass

    # TODO: do something smarter here, filter out garbage and swearing words, add tokenizer
    def detect(self, message: str) -> str:
        """Returns possible prompt defined in the message"""
        if "за то что" in message:
            return message.split("за то что")[1]
        else:
            return ""
