"""
API views for video processing operations.
"""

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from .exceptions import ConfigurationError
from .exceptions import ExternalServiceError
from .exceptions import ProcessingTimeoutError
from .exceptions import VideoValidationError
from .serializers import ErrorResponseSerializer
from .serializers import VideoProcessRequestSerializer
from .serializers import VideoProcessResponseSerializer
from .services import VideoProcessingService

logger = logging.getLogger(__name__)


class VideoProcessAPIView(APIView):
    """
    API endpoint for processing YouTube videos.

    Accepts POST requests with YouTube video URLs and processing parameters,
    returns processed video content in multiple styles.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        """
        Process a YouTube video and return structured results.

        Expected request format:
        {
            "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
            "styles": ["Summary", "Educational"],  # optional
            "output_language": "English"  # optional, defaults to English
        }

        Returns:
        - 200: Successfully processed video with results
        - 400: Invalid request data or video URL
        - 422: Processing timeout
        - 500: Configuration error
        - 502: External service error
        """
        logger.info(
            "Processing video request from user %s",
            request.user.username if request.user.is_authenticated else "anonymous",
        )

        # Validate request data
        request_serializer = VideoProcessRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            logger.warning(
                "Invalid request data: %s",
                request_serializer.errors,
            )
            return Response(
                {
                    "status": "error",
                    "error": "Invalid request data",
                    "details": request_serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self._process_video(request_serializer.validated_data)

    def _process_video(self, validated_data):
        """Process the video with validated data."""
        video_url = validated_data["video_url"]
        styles = validated_data.get("styles")
        output_language = validated_data.get("output_language", "English")

        try:
            # Initialize the video processing service
            service = VideoProcessingService()

            # Process the video
            logger.info("Starting video processing for URL: %s", video_url)
            result_data = service.process_video(
                video_url=video_url,
                styles=styles,
                output_language=output_language,
            )

            # Format and return successful response
            return self._create_success_response(result_data, video_url)

        except (VideoValidationError, ProcessingTimeoutError) as e:
            log_level = logger.warning
            log_level("Processing error: %s", e.message)
            return self._error_response(e.message, e.status_code)

        except (ConfigurationError, ExternalServiceError) as e:
            logger.exception("Service error: %s", e.message)
            return self._error_response(e.message, e.status_code)

        except Exception:
            logger.exception("Unexpected error during video processing")
            return self._error_response(
                "An unexpected error occurred during video processing",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _create_success_response(self, result_data, video_url):
        """Create and validate a success response."""
        response_data = {
            "status": "success",
            "data": result_data,
        }

        # Validate response format
        response_serializer = VideoProcessResponseSerializer(data=response_data)
        if response_serializer.is_valid():
            logger.info(
                "Video processing completed successfully for URL: %s",
                video_url,
            )
            return Response(
                response_serializer.validated_data,
                status=status.HTTP_200_OK,
            )

        logger.error(
            "Response serialization failed: %s",
            response_serializer.errors,
        )
        return self._error_response(
            "Response formatting error",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def _error_response(self, message: str, status_code: int) -> Response:
        """
        Create a standardized error response.

        Args:
            message: Error message to return
            status_code: HTTP status code

        Returns:
            Response: Formatted error response
        """
        error_data = {
            "status": "error",
            "error": message,
            "code": status_code,
        }

        # Validate error response format
        error_serializer = ErrorResponseSerializer(data=error_data)
        if error_serializer.is_valid():
            return Response(error_serializer.validated_data, status=status_code)
        # Fallback if error serializer fails
        return Response(
            {"status": "error", "error": message},
            status=status_code,
        )
