"""
Factory classes for generating test data for video processor tests.
"""

from datetime import UTC
from datetime import datetime
from typing import Any

import factory
from factory import Faker


class VideoProcessRequestDataFactory(factory.DictFactory):
    """Factory for creating valid video process request data."""

    video_url = Faker(
        "random_element",
        elements=[
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=test123456",
            "https://youtu.be/abcdef12345",
            "https://www.youtube.com/embed/xyz987654",
            "https://m.youtube.com/watch?v=mobile123",
        ],
    )
    styles = factory.LazyAttribute(
        lambda obj: factory.Faker(
            "random_elements",
            elements=[
                "Summary",
                "Educational",
                "Balanced and Detailed",
                "Narrative Rewriting",
                "Q&A Generation",
            ],
            length=factory.Faker("random_int", min=1, max=3),
            unique=True,
        ).evaluate(None, None, extra={"locale": None}),
    )
    output_language = Faker(
        "random_element",
        elements=["English", "Spanish", "French", "German", "Italian"],
    )


class VideoProcessResponseDataFactory(factory.DictFactory):
    """Factory for creating video process response data."""

    video_url = factory.SubFactory(VideoProcessRequestDataFactory, "video_url")
    video_title = Faker("sentence", nb_words=4)
    processed_at = factory.LazyFunction(lambda: datetime.now(UTC).isoformat())

    results = factory.LazyAttribute(
        lambda obj: {
            "summary": Faker("text", max_nb_chars=500).evaluate(
                None,
                None,
                extra={"locale": None},
            ),
            "educational": Faker("text", max_nb_chars=600).evaluate(
                None,
                None,
                extra={"locale": None},
            ),
            "balanced": Faker("text", max_nb_chars=550).evaluate(
                None,
                None,
                extra={"locale": None},
            ),
        },
    )

    metadata = factory.LazyAttribute(
        lambda obj: {
            "processing_time": factory.Faker(
                "pyfloat",
                left_digits=2,
                right_digits=2,
                positive=True,
                max_value=120.0,
            ).evaluate(None, None, extra={"locale": None}),
            "language": "English",
            "styles_processed": ["Summary", "Educational", "Balanced and Detailed"],
        },
    )


class MinimalVideoProcessRequestDataFactory(factory.DictFactory):
    """Factory for creating minimal valid request data (only required fields)."""

    video_url = "https://www.youtube.com/watch?v=test123456"


class InvalidVideoProcessRequestDataFactory(factory.DictFactory):
    """Factory for creating invalid request data for testing validation."""

    video_url = Faker(
        "random_element",
        elements=[
            "not-a-url",
            "http://example.com",
            "https://vimeo.com/123456",
            "ftp://invalid-protocol.com",
            "",
        ],
    )
    styles = Faker(
        "random_element",
        elements=[
            ["InvalidStyle"],
            ["Summary", "NonExistentStyle"],
            [""],
            [],
        ],
    )


class MockGetOutVideoAPIResponseFactory:
    """Factory for creating mock GetOutVideo API responses."""

    @staticmethod
    def create_output_files(
        temp_dir: str,
        video_title: str = "TestVideo",
        styles: list | None = None,
    ) -> list[str]:
        """Create mock output file paths."""
        if styles is None:
            styles = ["Summary", "Educational", "Balanced_and_Detailed"]

        output_files = []
        for style in styles:
            # Normalize style name for filename
            style_filename = style.replace(" ", "_").replace("&", "and")
            filename = f"{video_title}_{style_filename}.md"
            output_files.append(f"{temp_dir}/{filename}")

        return output_files

    @staticmethod
    def create_available_styles() -> list[str]:
        """Create mock list of available styles."""
        return [
            "Summary",
            "Educational",
            "Balanced and Detailed",
            "Narrative Rewriting",
            "Q&A Generation",
        ]

    @staticmethod
    def create_file_content(style: str) -> str:
        """Create mock file content for a given style."""
        content_templates = {
            "Summary": "# Summary\n\nThis is a test summary of the video content.",
            "Educational": (
                "# Educational Content\n\n"
                "This is educational content extracted from the video."
            ),
            "Balanced and Detailed": (
                "# Balanced and Detailed\n\nThis is a balanced and detailed analysis."
            ),
            "Narrative Rewriting": (
                "# Narrative\n\nThis is a narrative rewrite of the video content."
            ),
            "Q&A Generation": (
                "# Q&A\n\nQ: What is this video about?\nA: This is a test video."
            ),
        }
        return content_templates.get(
            style,
            f"# {style}\n\nGeneric content for {style}.",
        )


class ErrorResponseDataFactory(factory.DictFactory):
    """Factory for creating error response data."""

    status = "error"
    error = Faker("sentence", nb_words=6)
    code = Faker("random_element", elements=[400, 422, 500, 502])


class ThrottleConfigFactory:
    """Factory for creating throttle configuration test data."""

    @staticmethod
    def create_throttle_rates() -> dict[str, str]:
        """Create mock throttle rate configuration."""
        return {
            "anon": "10/min",
            "user": "60/min",
            "burst": "5/sec",
        }


class APITestDataFactory:
    """Factory for creating comprehensive API test scenarios."""

    @staticmethod
    def create_success_scenario() -> dict[str, Any]:
        """Create a complete success test scenario."""
        request_data = VideoProcessRequestDataFactory()
        response_data = VideoProcessResponseDataFactory()
        return {
            "request": request_data,
            "response": response_data,
            "expected_status": 200,
        }

    @staticmethod
    def create_validation_error_scenario() -> dict[str, Any]:
        """Create a validation error test scenario."""
        request_data = InvalidVideoProcessRequestDataFactory()
        return {
            "request": request_data,
            "expected_status": 400,
            "expected_error": "Invalid request data",
        }

    @staticmethod
    def create_authentication_error_scenario() -> dict[str, Any]:
        """Create an authentication error test scenario."""
        request_data = VideoProcessRequestDataFactory()
        return {
            "request": request_data,
            "expected_status": 401,
            "expected_error": "Authentication credentials were not provided",
        }

    @staticmethod
    def create_service_error_scenarios() -> list[dict[str, Any]]:
        """Create various service error test scenarios."""
        base_request = VideoProcessRequestDataFactory()

        return [
            {
                "name": "video_validation_error",
                "request": base_request,
                "exception_type": "VideoValidationError",
                "exception_message": "Invalid video URL",
                "expected_status": 400,
            },
            {
                "name": "processing_timeout_error",
                "request": base_request,
                "exception_type": "ProcessingTimeoutError",
                "exception_message": "Processing timed out",
                "expected_status": 422,
            },
            {
                "name": "configuration_error",
                "request": base_request,
                "exception_type": "ConfigurationError",
                "exception_message": "API key not configured",
                "expected_status": 500,
            },
            {
                "name": "external_service_error",
                "request": base_request,
                "exception_type": "ExternalServiceError",
                "exception_message": "External service unavailable",
                "expected_status": 502,
            },
        ]
