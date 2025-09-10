"""
Tests for video processing services.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from getoutvideo_django.video_processor.exceptions import ConfigurationError
from getoutvideo_django.video_processor.exceptions import ExternalServiceError
from getoutvideo_django.video_processor.exceptions import ProcessingTimeoutError
from getoutvideo_django.video_processor.exceptions import VideoValidationError
from getoutvideo_django.video_processor.services import VideoProcessingService


class TestVideoProcessingService:
    """Test VideoProcessingService functionality."""

    @pytest.fixture
    def service(self):
        """Create a VideoProcessingService instance for testing."""
        return VideoProcessingService()

    @pytest.fixture
    def mock_api(self):
        """Create a mock GetOutVideoAPI instance."""
        return Mock()

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    def test_init_with_valid_config(self, mock_getoutvideo_class, service):
        """Test initialization with valid configuration."""
        mock_instance = Mock()
        mock_getoutvideo_class.return_value = mock_instance

        # Re-initialize service to trigger API creation
        new_service = VideoProcessingService()
        assert new_service.api is not None

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    @patch("django.conf.settings")
    def test_init_missing_config(self, mock_settings, mock_getoutvideo_class):
        """Test initialization with missing configuration."""
        mock_settings.GETOUTVIDEO_CONFIG = {}

        with pytest.raises(
            ConfigurationError,
            match="GetOutVideo configuration is missing API key",
        ):
            VideoProcessingService()

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    def test_process_video_success(self, mock_getoutvideo_class, service):
        """Test successful video processing."""
        mock_api = Mock()
        mock_getoutvideo_class.return_value = mock_api
        mock_api.get_available_styles.return_value = ["Summary"]

        # Create test files in a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "TestVideo_Summary.md"
            test_file.write_text("Test summary content", encoding="utf-8")

            mock_api.process.return_value = [str(test_file)]

            # Re-initialize service with mocked API
            service.api = mock_api

            result = service.process_video(
                video_url="https://youtube.com/watch?v=test123",
                styles=["Summary"],
                output_language="English",
            )

            assert result["video_url"] == "https://youtube.com/watch?v=test123"
            assert result["video_title"] == "TestVideo"
            assert "processed_at" in result
            assert result["results"]["summary"] == "Test summary content"
            assert result["metadata"]["language"] == "English"
            assert result["metadata"]["styles_processed"] == ["Summary"]

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    def test_process_video_invalid_styles(self, mock_getoutvideo_class, service):
        """Test processing with invalid styles."""
        mock_api = Mock()
        mock_getoutvideo_class.return_value = mock_api
        mock_api.get_available_styles.return_value = ["Summary", "Educational"]

        service.api = mock_api

        with pytest.raises(
            VideoValidationError,
            match="Invalid styles: \\['InvalidStyle'\\]. Available styles:",
        ):
            service.process_video(
                video_url="https://youtube.com/watch?v=test123",
                styles=["InvalidStyle"],
            )

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    def test_process_video_api_error(self, mock_getoutvideo_class, service):
        """Test processing with API errors."""
        mock_api = Mock()
        mock_getoutvideo_class.return_value = mock_api
        mock_api.get_available_styles.return_value = ["Summary"]
        mock_api.process.side_effect = Exception("API Error")

        service.api = mock_api

        with pytest.raises(ExternalServiceError, match="External service error"):
            service.process_video(
                video_url="https://youtube.com/watch?v=test123",
                styles=["Summary"],
            )

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    def test_process_video_timeout_error(self, mock_getoutvideo_class, service):
        """Test processing with timeout errors."""
        mock_api = Mock()
        mock_getoutvideo_class.return_value = mock_api
        mock_api.get_available_styles.return_value = ["Summary"]
        mock_api.process.side_effect = Exception("Timeout occurred")

        service.api = mock_api

        with pytest.raises(ProcessingTimeoutError, match="Video processing timed out"):
            service.process_video(
                video_url="https://youtube.com/watch?v=test123",
                styles=["Summary"],
            )

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    def test_process_video_authentication_error(self, mock_getoutvideo_class, service):
        """Test processing with authentication errors."""
        mock_api = Mock()
        mock_getoutvideo_class.return_value = mock_api
        mock_api.get_available_styles.return_value = ["Summary"]
        mock_api.process.side_effect = Exception("401 Unauthorized")

        service.api = mock_api

        with pytest.raises(ConfigurationError, match="API authentication failed"):
            service.process_video(
                video_url="https://youtube.com/watch?v=test123",
                styles=["Summary"],
            )

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    def test_process_video_invalid_url_error(self, mock_getoutvideo_class, service):
        """Test processing with invalid URL errors."""
        mock_api = Mock()
        mock_getoutvideo_class.return_value = mock_api
        mock_api.get_available_styles.return_value = ["Summary"]
        mock_api.process.side_effect = Exception("Invalid URL provided")

        service.api = mock_api

        with pytest.raises(
            VideoValidationError,
            match="Invalid or inaccessible video URL",
        ):
            service.process_video(
                video_url="https://youtube.com/watch?v=invalid",
                styles=["Summary"],
            )

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    @patch("getoutvideo_django.video_processor.services.tempfile.TemporaryDirectory")
    def test_process_video_with_temp_directory_success(
        self,
        mock_temp_dir,
        mock_getoutvideo_class,
        service,
    ):
        """Test video processing uses temporary directory correctly."""
        # Setup mocks
        mock_api = Mock()
        mock_getoutvideo_class.return_value = mock_api
        mock_api.get_available_styles.return_value = ["Summary"]

        # Create a real temporary directory for this test
        with tempfile.TemporaryDirectory() as real_temp_dir:
            mock_temp_dir_instance = Mock()
            mock_temp_dir_instance.__enter__.return_value = real_temp_dir
            mock_temp_dir_instance.__exit__.return_value = None
            mock_temp_dir.return_value = mock_temp_dir_instance

            # Create test file in the directory
            temp_path = Path(real_temp_dir)
            test_file = temp_path / "TestVideo_Summary.md"
            test_file.write_text("Test content", encoding="utf-8")

            mock_api.process.return_value = [str(test_file)]
            service.api = mock_api

            result = service.process_video(
                video_url="https://youtube.com/watch?v=test123",
                styles=["Summary"],
            )

            # Verify temporary directory was used
            mock_temp_dir.assert_called_once()
            assert result["video_title"] == "TestVideo"
            assert result["results"]["summary"] == "Test content"

    @patch("getoutvideo_django.video_processor.services.GetOutVideoAPI")
    def test_process_video_default_parameters(self, mock_getoutvideo_class, service):
        """Test processing with default parameters."""
        mock_api = Mock()
        mock_getoutvideo_class.return_value = mock_api
        mock_api.get_available_styles.return_value = [
            "Summary",
            "Educational",
            "Balanced and Detailed",
        ]

        # Create test files for all default styles
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            files = []
            for style in ["Summary", "Educational", "Balanced_and_Detailed"]:
                test_file = temp_path / f"TestVideo_{style}.md"
                test_file.write_text(f"{style} content", encoding="utf-8")
                files.append(str(test_file))

            mock_api.process.return_value = files
            service.api = mock_api

            # Call without styles parameter to test default behavior
            result = service.process_video(
                video_url="https://youtube.com/watch?v=test123",
            )

            # Verify all default styles were processed
            expected_result_count = 3
            assert len(result["results"]) == expected_result_count
            assert "summary" in result["results"]
            assert "educational" in result["results"]
            assert "balanced" in result["results"]
            assert result["metadata"]["language"] == "English"  # Default language
