import os
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ..services.transcription import TranscriptionService
from ..models import Audio

class TestTranscriptionService(TestCase):
    def setUp(self):
        # Mock environment variable
        self.env_patcher = patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
        self.env_patcher.start()
        
        # Create test user and audio file
        self.user = self.create_user()
        self.audio = self.create_audio_file()
        
        # Initialize service
        self.transcription_service = TranscriptionService()

    def tearDown(self):
        self.env_patcher.stop()

    def create_user(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )

    def create_audio_file(self):
        content = b'test audio content'
        file = SimpleUploadedFile(
            name='test_audio.wav',
            content=content,
            content_type='audio/wav'
        )
        audio = Audio.objects.create(
            file=file,
            duration=10.0,
            sample_rate=44100,
            channels=2
        )
        audio.file.content_type = 'audio/wav'  # Ensure content_type is set on the file
        return audio

    @patch('openai.Audio.transcribe')
    def test_transcribe_audio_success_english(self, mock_transcribe):
        # Mock successful English transcription
        mock_response = {
            'text': 'Hello world',
            'language': 'en'
        }
        mock_transcribe.return_value = mock_response
        
        result = self.transcription_service.transcribe_audio(self.audio.file, language='en')
        
        self.assertEqual(result['text'], 'Hello world')
        self.assertEqual(result['language'], 'en')
        mock_transcribe.assert_called_once()

    @patch('openai.Audio.transcribe')
    def test_transcribe_audio_success_arabic(self, mock_transcribe):
        # Mock successful Arabic transcription
        mock_response = {
            'text': 'مرحبا بالعالم',
            'language': 'ar'
        }
        mock_transcribe.return_value = mock_response
        
        result = self.transcription_service.transcribe_audio(self.audio.file, language='ar')
        
        self.assertEqual(result['text'], 'مرحبا بالعالم')
        self.assertEqual(result['language'], 'ar')
        mock_transcribe.assert_called_once()

    @patch('openai.Audio.transcribe')
    def test_transcribe_audio_with_auto_detect(self, mock_transcribe):
        # Mock auto-detection (returns Arabic)
        mock_response = {
            'text': 'مرحبا',
            'language': 'ar'
        }
        mock_transcribe.return_value = mock_response
        
        result = self.transcription_service.transcribe_audio(self.audio.file, language='auto')
        
        self.assertEqual(result['text'], 'مرحبا')
        self.assertEqual(result['language'], 'ar')
        mock_transcribe.assert_called_once()

    @patch('openai.Audio.transcribe')
    def test_transcribe_audio_with_different_locales(self, mock_transcribe):
        """Test transcription with different locales."""
        locales = ['ar-SA', 'en-US']

        for locale in locales:
            mock_response = {'text': 'Test text', 'language': locale}
            mock_transcribe.return_value = mock_response

            result = self.transcription_service.transcribe_audio(self.audio.file, locale)
            self.assertEqual(result['text'], 'Test text')
            self.assertEqual(result['language'], locale)  # Compare with full locale instead of just language code

    @patch('openai.Audio.transcribe')
    def test_transcribe_audio_with_api_error(self, mock_transcribe):
        """Test transcription with API error."""
        mock_transcribe.side_effect = Exception("Transcription failed")
        
        with self.assertRaises(Exception) as context:
            self.transcription_service.transcribe_audio(self.audio.file, language='en')
        
        self.assertTrue('Transcription failed' in str(context.exception))

    def test_transcribe_audio_with_invalid_file(self):
        # Test with invalid file type
        invalid_file = SimpleUploadedFile('test.txt', b'invalid content', content_type='text/plain')
        
        with self.assertRaises(ValueError) as context:
            self.transcription_service.transcribe_audio(invalid_file)
        
        self.assertTrue('Invalid file type' in str(context.exception))

    def test_validate_audio_file(self):
        # Test file size validation
        large_content = b'x' * (25 * 1024 * 1024 + 1)  # Slightly over 25MB
        large_file = SimpleUploadedFile('large.mp3', large_content, content_type='audio/mpeg')
        large_file.size = len(large_content)  # Explicitly set the size attribute
        
        with self.assertRaises(ValueError) as context:
            self.transcription_service._validate_audio_file(large_file)
        
        self.assertTrue('File size exceeds 25MB limit' in str(context.exception)) 