"""
Django REST Framework serializers for the video_processor app.
"""

import re

from rest_framework import serializers


class VideoProcessRequestSerializer(serializers.Serializer):
    """Serializer for video processing request data."""

    video_url = serializers.URLField(
        required=True,
        help_text="YouTube video URL to process",
    )
    styles = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        help_text="List of processing styles to apply",
    )
    output_language = serializers.CharField(
        max_length=50,
        default="English",
        required=False,
        help_text="Output language for the processed content",
    )

    def validate_video_url(self, value: str) -> str:
        """
        Validate that the URL is a valid YouTube URL.

        Args:
            value: The URL to validate

        Returns:
            The validated URL

        Raises:
            serializers.ValidationError: If URL is not a valid YouTube URL
        """
        youtube_patterns = [
            r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]+",
            r"^https?://(www\.)?youtube\.com/watch\?.*v=[\w-]+",
            r"^https?://youtu\.be/[\w-]+",
            r"^https?://(www\.)?youtube\.com/embed/[\w-]+",
            r"^https?://(www\.)?youtube\.com/v/[\w-]+",
        ]

        if not any(re.match(pattern, value) for pattern in youtube_patterns):
            msg = "Invalid YouTube URL. Please provide a valid YouTube video URL."
            raise serializers.ValidationError(msg)

        return value

    def validate_styles(self, value: list) -> list:
        """
        Validate the styles list.

        Args:
            value: List of styles to validate

        Returns:
            The validated styles list

        Raises:
            serializers.ValidationError: If styles are invalid
        """
        if value is None:
            return []

        valid_styles = [
            "Summary",
            "Educational",
            "Balanced",
            "QA Generation",
            "Narrative",
        ]

        for style in value:
            if style not in valid_styles:
                error_msg = (
                    f"Invalid style '{style}'. "
                    f"Valid styles are: {', '.join(valid_styles)}"
                )
                raise serializers.ValidationError(error_msg)

        return value


class VideoMetadataSerializer(serializers.Serializer):
    """Serializer for video metadata in the response."""

    processing_time = serializers.FloatField(help_text="Processing time in seconds")
    language = serializers.CharField(help_text="Output language")
    styles_processed = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of styles that were processed",
    )


class VideoResultsSerializer(serializers.Serializer):
    """Serializer for video processing results."""

    summary = serializers.CharField(required=False, allow_blank=True)
    educational = serializers.CharField(required=False, allow_blank=True)
    balanced = serializers.CharField(required=False, allow_blank=True)
    qa_generation = serializers.CharField(required=False, allow_blank=True)
    narrative = serializers.CharField(required=False, allow_blank=True)


class VideoDataSerializer(serializers.Serializer):
    """Serializer for video data in the response."""

    video_url = serializers.URLField(help_text="Original YouTube video URL")
    video_title = serializers.CharField(help_text="Video title from YouTube")
    processed_at = serializers.DateTimeField(help_text="ISO-8601 timestamp")
    results = VideoResultsSerializer(help_text="Processed content by style")
    metadata = VideoMetadataSerializer(help_text="Processing metadata")


class VideoProcessResponseSerializer(serializers.Serializer):
    """Serializer for video processing response data."""

    status = serializers.CharField(help_text="Processing status")
    data = VideoDataSerializer(help_text="Video processing data")


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""

    status = serializers.CharField(help_text="Error status")
    error = serializers.CharField(help_text="Error message")
    code = serializers.CharField(required=False, help_text="Error code")
