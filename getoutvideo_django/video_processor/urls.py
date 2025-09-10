"""
URL routing for the video_processor app.
"""

from django.urls import path

from . import views

app_name = "video_processor"

urlpatterns = [
    path(
        "api/v1/video/process/",
        views.VideoProcessAPIView.as_view(),
        name="process-video",
    ),
]
