class ComponentError(Exception):
    def __init__(self, message, component, component_error_type, component_error_message):
        super().__init__(message)
        self.component = component
        self.component_error_type = component_error_type
        self.component_error_message = component_error_message

class StickerGeneratorError(ComponentError):
    def __init__(self, message, component_error_type, component_message):
        super().__init__(message, 'sticker-generator', component_error_type, component_message)

class GoogleAPIError(ComponentError):
    def __init__(self, message, component_error_type, component_message):
        super().__init__(message, 'google-api', component_error_type, component_message)

class DeepAIAPIError(ComponentError):
    def __init__(self, message, component_error_type, component_message):
        super().__init__(message, 'deepai-api', component_error_type, component_message)