import os
import tempfile
import numpy as np
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from ..services.audio import AudioProcessingService
from django.conf import settings

class TestAudioPlayback(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.audio_service = AudioProcessingService()
        
        # Ensure media/temp directory exists
        self.temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Use process-specific filename to avoid conflicts in parallel testing
        pid = os.getpid()
        self.test_wav_path = os.path.join(self.temp_dir, f'test_{pid}.wav')
        
        # Create a simple test WAV file
        sample_rate = 44100
        duration = 1.0  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Save as WAV file
        import scipy.io.wavfile as wav
        wav.write(self.test_wav_path, sample_rate, audio_data)
        
    def tearDown(self):
        # Clean up test file
        if os.path.exists(self.test_wav_path):
            os.remove(self.test_wav_path)
    
    def test_audio_playback_endpoint(self):
        """Test that the audio playback endpoint returns a valid response."""
        # Upload test audio file
        with open(self.test_wav_path, 'rb') as f:
            response = self.client.post(
                reverse('communication:audio-upload'),
                {'audio_file': f},
                format='multipart'
            )
        self.assertEqual(response.status_code, 201)
        audio_id = response.json()['id']
        
        # Test playback endpoint
        response = self.client.get(
            reverse('communication:audio-playback', kwargs={'audio_id': audio_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'audio/wav')
        self.assertTrue(int(response['Content-Length']) > 0)
    
    def test_audio_playback_with_range(self):
        """Test that the audio playback endpoint supports range requests."""
        # Upload test audio file
        with open(self.test_wav_path, 'rb') as f:
            response = self.client.post(
                reverse('communication:audio-upload'),
                {'audio_file': f},
                format='multipart'
            )
        self.assertEqual(response.status_code, 201)
        audio_id = response.json()['id']
        
        # Test range request
        headers = {'Range': 'bytes=0-1024'}
        response = self.client.get(
            reverse('communication:audio-playback', kwargs={'audio_id': audio_id}),
            HTTP_RANGE='bytes=0-1024'
        )
        self.assertEqual(response.status_code, 206)
        self.assertTrue('Content-Range' in response)
        self.assertEqual(response['Content-Type'], 'audio/wav')
    
    def test_audio_playback_invalid_range(self):
        """Test that the audio playback endpoint handles invalid range requests."""
        # Upload test audio file
        with open(self.test_wav_path, 'rb') as f:
            response = self.client.post(
                reverse('communication:audio-upload'),
                {'audio_file': f},
                format='multipart'
            )
        self.assertEqual(response.status_code, 201)
        audio_id = response.json()['id']
        
        # Test invalid range request
        response = self.client.get(
            reverse('communication:audio-playback', kwargs={'audio_id': audio_id}),
            HTTP_RANGE='bytes=invalid'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_audio_playback_nonexistent_file(self):
        """Test that the audio playback endpoint handles nonexistent files."""
        response = self.client.get(
            reverse('communication:audio-playback', kwargs={'audio_id': 999999})  # Non-existent ID
        )
        self.assertEqual(response.status_code, 404)
    
    def test_audio_playback_unsupported_format(self):
        """Test that the audio playback endpoint handles unsupported formats."""
        # Create an unsupported audio file
        unsupported_path = os.path.join(tempfile.gettempdir(), 'test.txt')
        with open(unsupported_path, 'w') as f:
            f.write('Not an audio file')
        
        # Upload unsupported file
        with open(unsupported_path, 'rb') as f:
            response = self.client.post(
                reverse('communication:audio-upload'),
                {'audio_file': f},
                format='multipart'
            )
        self.assertEqual(response.status_code, 400)
        
        # Clean up
        os.remove(unsupported_path) 