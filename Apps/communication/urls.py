from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import upload_audio, play_audio, compress_audio, transcribe_audio
from Apps.communication.views import (
    EmailTemplateViewSet,
    EmailTrackingViewSet,
    EmailAnalyticsViewSet
)

app_name = 'communication'

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'email-templates', EmailTemplateViewSet)
router.register(r'email-tracking', EmailTrackingViewSet)
router.register(r'email-analytics', EmailAnalyticsViewSet)

urlpatterns = [
    # Audio-related URLs
    path('audio/upload/', upload_audio, name='audio-upload'),
    path('audio/play/<int:audio_id>/', play_audio, name='audio-playback'),
    path('audio/compress/<int:audio_id>/', compress_audio, name='audio-compress'),
    path('transcribe/', transcribe_audio, name='transcribe-audio'),
    
    # Email-related URLs
    path('', include(router.urls)),
] 