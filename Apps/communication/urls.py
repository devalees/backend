from django.urls import path
from .views import upload_audio, play_audio, compress_audio

app_name = 'communication'

urlpatterns = [
    path('audio/upload/', upload_audio, name='audio-upload'),
    path('audio/play/<int:audio_id>/', play_audio, name='audio-playback'),
    path('audio/compress/<int:audio_id>/', compress_audio, name='audio-compress'),
] 