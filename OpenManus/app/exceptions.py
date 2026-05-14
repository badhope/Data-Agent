class ToolError(Exception):
    """Raised when a tool encounters an error."""

    def __init__(self, message):
        self.message = message


class DataAIError(Exception):
    """Base exception for all DataAI errors"""


class TokenLimitExceeded(DataAIError):
    """Exception raised when the token limit is exceeded"""
