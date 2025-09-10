"""
Business logic layer for video processing operations.
"""

import tempfile
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings
from getoutvideo import GetOutVideoAPI

from .exceptions import ConfigurationError
from .exceptions import ExternalServiceError
from .exceptions import ProcessingTimeoutError
from .exceptions import VideoValidationError


class VideoProcessingService:
    """Service class for handling video processing operations."""

    def __init__(self):
        """Initialize the service with GetOutVideo API."""
        api_key = settings.GETOUTVIDEO_CONFIG.get("OPENAI_API_KEY")
        if not api_key:
            msg = "OPENAI_API_KEY not configured"
            raise ConfigurationError(msg)

        try:
            self.api = GetOutVideoAPI(openai_api_key=api_key)
        except Exception as e:
            msg = f"Failed to initialize GetOutVideo API: {e}"
            raise ConfigurationError(msg) from e

    def get_available_styles(self) -> list[str]:
        """Get list of available processing styles from the API."""
        try:
            return self.api.get_available_styles()
        except Exception as e:
            msg = f"Failed to get available styles: {e}"
            raise ExternalServiceError(msg) from e

    def _validate_styles(self, styles: list[str]) -> None:
        """Validate styles against available ones."""
        available_styles = self.get_available_styles()
        invalid_styles = [s for s in styles if s not in available_styles]
        if invalid_styles:
            msg = (
                f"Invalid styles: {invalid_styles}. "
                f"Available styles: {available_styles}"
            )
            raise VideoValidationError(msg)

    def _parse_output_files(
        self,
        output_files: list[str],
    ) -> tuple[dict[str, str], str]:
        """Parse output files and extract results and video title."""
        results = {}
        video_title = "Unknown Title"

        style_mapping = {
            "Balanced and Detailed": "balanced",
            "Summary": "summary",
            "Educational": "educational",
            "Narrative Rewriting": "narrative",
            "Q&A Generation": "qa_generation",
        }

        for file_path_str in output_files:
            file_path = Path(file_path_str)
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                filename = file_path.stem

                if "_" in filename:
                    parts = filename.split("_")
                    min_parts = 2
                    if len(parts) >= min_parts:
                        video_title = parts[0]
                        style = "_".join(parts[1:])

                        # Find matching style (case-insensitive)
                        result_key = None
                        for api_style, result_style in style_mapping.items():
                            if api_style.lower().replace(
                                " ",
                                "_",
                            ) in style.lower().replace(" ", "_"):
                                result_key = result_style
                                break

                        if result_key:
                            results[result_key] = content
                        else:
                            # Fallback: use cleaned style name as key
                            result_key = (
                                style.lower().replace(" ", "_").replace("&", "and")
                            )
                            results[result_key] = content

        return results, video_title

    def _handle_processing_error(self, e: Exception, video_url: str) -> None:
        """Handle different types of processing errors."""
        error_msg = str(e).lower()
        if (
            "invalid url" in error_msg
            or "not found" in error_msg
            or "unavailable" in error_msg
        ):
            msg = f"Invalid or inaccessible video URL: {video_url}"
            raise VideoValidationError(msg) from e
        if "timeout" in error_msg:
            msg = "Video processing timed out"
            raise ProcessingTimeoutError(msg) from e
        if "api key" in error_msg or "authentication" in error_msg:
            msg = "API authentication failed"
            raise ConfigurationError(msg) from e
        msg = f"External service error: {e}"
        raise ExternalServiceError(msg) from e

    def process_video(
        self,
        video_url: str,
        styles: list[str] | None = None,
        output_language: str = "English",
    ) -> dict[str, Any]:
        """
        Process a YouTube video and return structured results.

        Args:
            video_url: YouTube video URL
            styles: List of processing styles (if None, uses all available)
            output_language: Output language for results

        Returns:
            Dict containing processed video data

        Raises:
            VideoValidationError: If video URL is invalid
            ExternalServiceError: If external service fails
            ProcessingTimeoutError: If processing times out
        """
        start_time = time.time()

        try:
            # If no styles specified, use all available styles
            if styles is None:
                styles = self.get_available_styles()

            self._validate_styles(styles)

            # Create temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                # Process the video using GetOutVideo API
                output_files = self.api.process_youtube_url(
                    url=video_url,
                    output_dir=temp_dir,
                    styles=styles,
                    output_language=output_language,
                )

                results, video_title = self._parse_output_files(output_files)
                processing_time = time.time() - start_time

                return {
                    "video_url": video_url,
                    "video_title": video_title.replace("_", " "),
                    "processed_at": datetime.now(UTC).isoformat(),
                    "results": results,
                    "metadata": {
                        "processing_time": round(processing_time, 2),
                        "language": output_language,
                        "styles_processed": styles,
                    },
                }

        except VideoValidationError:
            raise
        except (ExternalServiceError, ProcessingTimeoutError, ConfigurationError):
            raise
        except Exception as e:  # noqa: BLE001
            # Broad exception handling is intentional here to catch and categorize
            # various external API errors that might not have specific types
            self._handle_processing_error(e, video_url)
