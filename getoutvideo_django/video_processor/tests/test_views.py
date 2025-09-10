"""
Tests for VideoProcessAPIView API endpoint.
"""

import json
from http import HTTPStatus
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APIClient

from getoutvideo_django.users.tests.factories import UserFactory
from getoutvideo_django.video_processor.exceptions import ConfigurationError
from getoutvideo_django.video_processor.exceptions import ExternalServiceError
from getoutvideo_django.video_processor.exceptions import ProcessingTimeoutError
from getoutvideo_django.video_processor.exceptions import VideoValidationError
from getoutvideo_django.video_processor.views import VideoProcessAPIView

pytestmark = pytest.mark.django_db


class TestVideoProcessAPIView:
    """Tests for VideoProcessAPIView endpoint."""

    @pytest.fixture
    def api_client(self):
        """Create API client for testing."""
        return APIClient()

    @pytest.fixture
    def user(self):
        """Create test user."""
        return UserFactory()

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """Create authenticated API client."""
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def valid_request_data(self):
        """Valid request data for testing."""
        return {
            "video_url": "https://www.youtube.com/watch?v=test123",
            "styles": ["Summary", "Educational"],
            "output_language": "English",
        }

    @pytest.fixture
    def mock_service_success_response(self):
        """Mock successful service response."""
        return {
            "video_url": "https://www.youtube.com/watch?v=test123",
            "video_title": "Test Video",
            "processed_at": "2024-01-01T12:00:00Z",
            "results": {
                "summary": "Test summary content",
                "educational": "Test educational content",
            },
            "metadata": {
                "processing_time": 25.5,
                "language": "English",
                "styles_processed": ["Summary", "Educational"],
            },
        }

    @pytest.fixture
    def rf(self):
        """Request factory for creating test requests."""
        return RequestFactory()

    def test_post_success(
        self,
        authenticated_client,
        valid_request_data,
        mock_service_success_response,
    ):
        """Test successful video processing request."""
        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.return_value = mock_service_success_response

            response = authenticated_client.post(
                reverse("video_processor:process-video"),
                data=valid_request_data,
                format="json",
            )

        assert response.status_code == HTTPStatus.OK
        response_data = response.json()

        assert response_data["status"] == "success"
        assert (
            response_data["data"]["video_url"]
            == "https://www.youtube.com/watch?v=test123"
        )
        assert response_data["data"]["video_title"] == "Test Video"
        assert "results" in response_data["data"]
        assert "metadata" in response_data["data"]

        # Verify service was called with correct parameters
        mock_service.process_video.assert_called_once_with(
            video_url="https://www.youtube.com/watch?v=test123",
            styles=["Summary", "Educational"],
            output_language="English",
        )

    def test_post_unauthenticated(self, api_client, valid_request_data):
        """Test request without authentication."""
        response = api_client.post(
            reverse("video_processor:process-video"),
            data=valid_request_data,
            format="json",
        )

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post_invalid_request_data(self, authenticated_client):
        """Test request with invalid data."""
        invalid_data = {
            "video_url": "not-a-valid-url",
            "styles": ["InvalidStyle"],
        }

        response = authenticated_client.post(
            reverse("video_processor:process-video"),
            data=invalid_data,
            format="json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        response_data = response.json()
        assert response_data["status"] == "error"
        assert response_data["error"] == "Invalid request data"
        assert "details" in response_data

    def test_post_missing_required_field(self, authenticated_client):
        """Test request with missing required video_url field."""
        incomplete_data = {
            "styles": ["Summary"],
            "output_language": "English",
        }

        response = authenticated_client.post(
            reverse("video_processor:process-video"),
            data=incomplete_data,
            format="json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        response_data = response.json()
        assert response_data["status"] == "error"
        assert "video_url" in response_data["details"]

    def test_post_video_validation_error(
        self,
        authenticated_client,
        valid_request_data,
    ):
        """Test handling of VideoValidationError."""
        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.side_effect = VideoValidationError(
                "Invalid video URL",
            )

            response = authenticated_client.post(
                reverse("video_processor:process-video"),
                data=valid_request_data,
                format="json",
            )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        response_data = response.json()
        assert response_data["status"] == "error"
        assert response_data["error"] == "Invalid video URL"

    def test_post_processing_timeout_error(
        self,
        authenticated_client,
        valid_request_data,
    ):
        """Test handling of ProcessingTimeoutError."""
        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.side_effect = ProcessingTimeoutError(
                "Processing timed out",
            )

            response = authenticated_client.post(
                reverse("video_processor:process-video"),
                data=valid_request_data,
                format="json",
            )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        response_data = response.json()
        assert response_data["status"] == "error"
        assert response_data["error"] == "Processing timed out"

    def test_post_configuration_error(self, authenticated_client, valid_request_data):
        """Test handling of ConfigurationError."""
        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.side_effect = ConfigurationError(
                "API key not configured",
            )

            response = authenticated_client.post(
                reverse("video_processor:process-video"),
                data=valid_request_data,
                format="json",
            )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        response_data = response.json()
        assert response_data["status"] == "error"
        assert response_data["error"] == "API key not configured"

    def test_post_external_service_error(
        self,
        authenticated_client,
        valid_request_data,
    ):
        """Test handling of ExternalServiceError."""
        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.side_effect = ExternalServiceError(
                "External service unavailable",
            )

            response = authenticated_client.post(
                reverse("video_processor:process-video"),
                data=valid_request_data,
                format="json",
            )

        assert response.status_code == HTTPStatus.BAD_GATEWAY
        response_data = response.json()
        assert response_data["status"] == "error"
        assert response_data["error"] == "External service unavailable"

    def test_post_unexpected_error(self, authenticated_client, valid_request_data):
        """Test handling of unexpected exceptions."""
        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.side_effect = Exception("Unexpected error")

            response = authenticated_client.post(
                reverse("video_processor:process-video"),
                data=valid_request_data,
                format="json",
            )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        response_data = response.json()
        assert response_data["status"] == "error"
        assert (
            response_data["error"]
            == "An unexpected error occurred during video processing"
        )

    def test_post_optional_fields(
        self,
        authenticated_client,
        mock_service_success_response,
    ):
        """Test request with only required fields (optional fields omitted)."""
        minimal_data = {
            "video_url": "https://www.youtube.com/watch?v=test123",
        }

        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.return_value = mock_service_success_response

            response = authenticated_client.post(
                reverse("video_processor:process-video"),
                data=minimal_data,
                format="json",
            )

        assert response.status_code == HTTPStatus.OK

        # Verify service was called with defaults
        mock_service.process_video.assert_called_once_with(
            video_url="https://www.youtube.com/watch?v=test123",
            styles=None,  # Should be None when not provided
            output_language="English",  # Default value
        )

    def test_response_serialization_error(
        self,
        authenticated_client,
        valid_request_data,
    ):
        """Test handling when response serialization fails."""
        invalid_service_response = {
            "invalid_structure": "This doesn't match expected response format",
        }

        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.return_value = invalid_service_response

            response = authenticated_client.post(
                reverse("video_processor:process-video"),
                data=valid_request_data,
                format="json",
            )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        response_data = response.json()
        assert response_data["status"] == "error"
        assert response_data["error"] == "Response formatting error"

    def test_error_response_serialization_fallback(
        self,
        authenticated_client,
        valid_request_data,
    ):
        """Test fallback when error response serialization also fails."""
        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.side_effect = Exception("Test error")

            # Also patch the error serializer to fail
            with patch(
                "getoutvideo_django.video_processor.views.ErrorResponseSerializer",
            ) as mock_error_serializer:
                mock_error_serializer.return_value.is_valid.return_value = False

                response = authenticated_client.post(
                    reverse("video_processor:process-video"),
                    data=valid_request_data,
                    format="json",
                )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        response_data = response.json()
        assert response_data["status"] == "error"
        assert (
            response_data["error"]
            == "An unexpected error occurred during video processing"
        )

    def test_get_method_not_allowed(self, authenticated_client):
        """Test that GET requests are not allowed."""
        response = authenticated_client.get(reverse("video_processor:process-video"))
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_put_method_not_allowed(self, authenticated_client):
        """Test that PUT requests are not allowed."""
        response = authenticated_client.put(
            reverse("video_processor:process-video"),
            data={"test": "data"},
            format="json",
        )
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_delete_method_not_allowed(self, authenticated_client):
        """Test that DELETE requests are not allowed."""
        response = authenticated_client.delete(reverse("video_processor:process-video"))
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_throttling_configuration(self, rf, user):
        """Test that throttling is properly configured on the view."""
        view = VideoProcessAPIView()
        request = rf.post("/fake-url/")
        request.user = user

        # Check that throttling classes are configured
        assert hasattr(view, "throttle_classes")
        throttle_class_names = [cls.__name__ for cls in view.throttle_classes]
        assert "AnonRateThrottle" in throttle_class_names
        assert "UserRateThrottle" in throttle_class_names

    def test_permission_classes(self, rf, user):
        """Test that authentication is required."""
        view = VideoProcessAPIView()
        request = rf.post("/fake-url/")
        request.user = user

        # Check that IsAuthenticated permission is configured
        assert hasattr(view, "permission_classes")
        permission_class_names = [cls.__name__ for cls in view.permission_classes]
        assert "IsAuthenticated" in permission_class_names

    def test_logging_on_request(
        self,
        authenticated_client,
        valid_request_data,
        mock_service_success_response,
    ):
        """Test that appropriate logging occurs during request processing."""
        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.return_value = mock_service_success_response

            with patch(
                "getoutvideo_django.video_processor.views.logger",
            ) as mock_logger:
                authenticated_client.post(
                    reverse("video_processor:process-video"),
                    data=valid_request_data,
                    format="json",
                )

                # Verify logging calls
                mock_logger.info.assert_any_call(
                    "Processing video request from user %s",
                    "testuser",
                )
                mock_logger.info.assert_any_call(
                    "Starting video processing for URL: %s",
                    "https://www.youtube.com/watch?v=test123",
                )
                mock_logger.info.assert_any_call(
                    "Video processing completed successfully for URL: %s",
                    "https://www.youtube.com/watch?v=test123",
                )

    def test_logging_on_validation_error(self, authenticated_client):
        """Test logging for validation errors."""
        invalid_data = {"invalid": "data"}

        with patch("getoutvideo_django.video_processor.views.logger") as mock_logger:
            authenticated_client.post(
                reverse("video_processor:process-video"),
                data=invalid_data,
                format="json",
            )

            # Verify warning log for invalid request data
            mock_logger.warning.assert_called()
            log_call_args = mock_logger.warning.call_args[0]
            assert "Invalid request data" in log_call_args[0]

    def test_content_type_json_required(
        self,
        authenticated_client,
        valid_request_data,
        mock_service_success_response,
    ):
        """Test that JSON content type is properly handled."""
        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.return_value = mock_service_success_response

            # Test with JSON content type
            response = authenticated_client.post(
                reverse("video_processor:process-video"),
                data=json.dumps(valid_request_data),
                content_type="application/json",
            )

        assert response.status_code == HTTPStatus.OK

    def test_different_youtube_url_formats(
        self,
        authenticated_client,
        mock_service_success_response,
    ):
        """Test different valid YouTube URL formats."""
        youtube_urls = [
            "https://www.youtube.com/watch?v=test123",
            "https://youtube.com/watch?v=test123",
            "https://youtu.be/test123",
            "https://www.youtube.com/embed/test123",
            "https://www.youtube.com/v/test123",
        ]

        with patch(
            "getoutvideo_django.video_processor.views.VideoProcessingService",
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.process_video.return_value = mock_service_success_response

            for url in youtube_urls:
                response = authenticated_client.post(
                    reverse("video_processor:process-video"),
                    data={"video_url": url},
                    format="json",
                )

                assert response.status_code == HTTPStatus.OK, f"Failed for URL: {url}"
