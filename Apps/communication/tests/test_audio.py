import os
import tempfile
import numpy as np
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ..services.audio import AudioProcessingService

class TestAudioProcessingService(TestCase):
    def setUp(self):
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
    
    def test_validate_audio_file(self):
        # Test valid WAV file
        with open(self.test_wav_path, 'rb') as f:
            valid_file = SimpleUploadedFile(
                'test.wav',
                f.read(),
                content_type='audio/wav'
            )
        is_valid, message = self.audio_service.validate_audio_file(valid_file)
        self.assertTrue(is_valid)
        self.assertEqual(message, "")
        
        # Test invalid file format
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'not an audio file',
            content_type='text/plain'
        )
        is_valid, message = self.audio_service.validate_audio_file(invalid_file)
        self.assertFalse(is_valid)
        self.assertIn("Unsupported audio format", message)
        
        # Test file size limit
        large_file = SimpleUploadedFile(
            'test.wav',
            b'0' * (self.audio_service.max_file_size + 1),
            content_type='audio/wav'
        )
        is_valid, message = self.audio_service.validate_audio_file(large_file)
        self.assertFalse(is_valid)
        self.assertIn("File size exceeds", message)
    
    def test_process_audio(self):
        with open(self.test_wav_path, 'rb') as f:
            audio_file = SimpleUploadedFile(
                'test.wav',
                f.read(),
                content_type='audio/wav'
            )
        
        features = self.audio_service.process_audio(audio_file)
        self.assertIsNotNone(features)
        self.assertIn('duration', features)
        self.assertIn('sample_rate', features)
        self.assertIn('channels', features)
        self.assertIn('rms_energy', features)
        self.assertIn('zero_crossing_rate', features)
        self.assertIn('spectral_centroid', features)
        
        # Verify specific values
        self.assertEqual(features['sample_rate'], 44100)
        self.assertEqual(features['channels'], 1)
        self.assertAlmostEqual(features['duration'], 1.0, places=1)
    
    def test_normalize_audio(self):
        # Create test audio data
        audio_data = np.array([0.1, 0.5, -0.3, 0.8, -0.9])
        normalized = self.audio_service.normalize_audio(audio_data)
        
        # Check if normalized
        self.assertTrue(np.all(np.abs(normalized) <= 1.0))
        self.assertTrue(np.any(np.abs(normalized) == 1.0))
    
    def test_resample_audio(self):
        # Create test audio data
        original_sr = 44100
        target_sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(original_sr * duration), False)
        audio_data = np.sin(2 * np.pi * 440 * t)
        
        resampled = self.audio_service.resample_audio(audio_data, original_sr, target_sr)
        
        # Check if resampled correctly
        self.assertEqual(len(resampled), int(target_sr * duration))
    
    def test_trim_silence(self):
        # Create test audio data with more obvious silence at beginning and end
        audio_data = np.concatenate([
            np.zeros(22050),  # 0.5 seconds of silence at beginning
            np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100)),  # 1 second of tone
            np.zeros(22050)   # 0.5 seconds of silence at end
        ])
        
        trimmed = self.audio_service.trim_silence(audio_data, top_db=10)  # Lower threshold to detect silence
        
        # Check if silence was trimmed
        self.assertLess(len(trimmed), len(audio_data))
        self.assertTrue(np.any(trimmed != 0))  # Should still have the tone 