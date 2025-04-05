import os
import tempfile
import numpy as np
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from ..services.audio import AudioProcessingService

class TestAudioCompression(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.audio_service = AudioProcessingService()
        self.test_wav_path = os.path.join(tempfile.gettempdir(), 'test.wav')
        
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
    
    def test_audio_compression_endpoint(self):
        """Test that the audio compression endpoint returns a valid response."""
        # Upload test audio file
        with open(self.test_wav_path, 'rb') as f:
            response = self.client.post(
                reverse('communication:audio-upload'),
                {'audio_file': f},
                format='multipart'
            )
        self.assertEqual(response.status_code, 201)
        audio_id = response.json()['id']
        
        # Test compression endpoint
        response = self.client.post(
            reverse('communication:audio-compress', kwargs={'audio_id': audio_id}),
            {'quality': 0.5}  # 50% quality
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue('compressed_file' in response.json())
        self.assertTrue('original_size' in response.json())
        self.assertTrue('compressed_size' in response.json())
        
        # Verify compression ratio
        original_size = response.json()['original_size']
        compressed_size = response.json()['compressed_size']
        self.assertLess(compressed_size, original_size)
    
    def test_audio_compression_invalid_quality(self):
        """Test that the audio compression endpoint handles invalid quality values."""
        # Upload test audio file
        with open(self.test_wav_path, 'rb') as f:
            response = self.client.post(
                reverse('communication:audio-upload'),
                {'audio_file': f},
                format='multipart'
            )
        self.assertEqual(response.status_code, 201)
        audio_id = response.json()['id']
        
        # Test with invalid quality value
        response = self.client.post(
            reverse('communication:audio-compress', kwargs={'audio_id': audio_id}),
            {'quality': 1.5}  # Invalid quality > 1.0
        )
        self.assertEqual(response.status_code, 400)
        
        # Test with negative quality value
        response = self.client.post(
            reverse('communication:audio-compress', kwargs={'audio_id': audio_id}),
            {'quality': -0.5}  # Invalid quality < 0
        )
        self.assertEqual(response.status_code, 400)
    
    def test_audio_compression_nonexistent_file(self):
        """Test that the audio compression endpoint handles nonexistent files."""
        response = self.client.post(
            reverse('communication:audio-compress', kwargs={'audio_id': 999999}),
            {'quality': 0.5}
        )
        self.assertEqual(response.status_code, 404)
    
    def test_audio_compression_unsupported_format(self):
        """Test that the audio compression endpoint handles unsupported formats."""
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