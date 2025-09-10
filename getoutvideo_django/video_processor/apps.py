import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VideoProcessorConfig(AppConfig):
    name = "getoutvideo_django.video_processor"
    verbose_name = _("Video Processor")

    def ready(self):
        with contextlib.suppress(ImportError):
            import getoutvideo_django.video_processor.signals  # noqa: F401, PLC0415
