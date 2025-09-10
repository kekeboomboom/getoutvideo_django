"""
Custom exception classes for the video_processor app.
"""

from rest_framework import status
from rest_framework.views import exception_handler


class VideoProcessorError(Exception):
    """Base exception class for video processor app."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class VideoValidationError(VideoProcessorError):
    """Raised when video URL validation fails."""

    def __init__(self, message: str = "Invalid video URL"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class ExternalServiceError(VideoProcessorError):
    """Raised when external service (GetOutVideo API) fails."""

    def __init__(self, message: str = "External service error"):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY)


class ProcessingTimeoutError(VideoProcessorError):
    """Raised when video processing times out."""

    def __init__(self, message: str = "Processing timeout"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class ConfigurationError(VideoProcessorError):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


def custom_exception_handler(exc, context):
    """Custom exception handler for video processor exceptions."""

    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Handle our custom exceptions
    if isinstance(exc, VideoProcessorError):
        custom_response_data = {
            "error": exc.message,
            "status_code": exc.status_code,
        }
        response.data = custom_response_data
        response.status_code = exc.status_code

    return response
