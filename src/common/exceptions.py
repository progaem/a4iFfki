"""
This module declares classes for more specific exceptions to be used in other classes
"""
class ComponentError(Exception):
    """Global exception providing deeper insight in component specifics of the error"""
    def __init__(self, message, component, component_error_type, component_error_message):
        super().__init__(message)
        self.component = component
        self.component_error_type = component_error_type
        self.component_error_message = component_error_message

class LanguageFilterError(ComponentError):
    """Global LanguageFilter component exception"""
    def __init__(self, message, component_error_type, component_message):
        super().__init__(message, 'language-filter', component_error_type, component_message)

class StickerGeneratorError(ComponentError):
    """Global StickerGenerator component exception"""
    def __init__(self, message, component_error_type, component_message):
        super().__init__(message, 'sticker-generator', component_error_type, component_message)

class GoogleAPIError(ComponentError):
    """Global GoogleAPI component exception"""
    def __init__(self, message, component_error_type, component_message):
        super().__init__(message, 'google-api', component_error_type, component_message)

class DeepAIAPIError(ComponentError):
    """Global DeepAIAPI component exception"""
    def __init__(self, message, component_error_type, component_message):
        super().__init__(message, 'deepai-api', component_error_type, component_message)

class ImageS3StorageError(ComponentError):
    """Global ImageS3Storage component exception"""
    def __init__(self, message, component_error_type, component_message):
        super().__init__(message, 'image-storage', component_error_type, component_message)