import os
import logging
from typing import Optional, Tuple
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
import numpy as np
from scipy.io import wavfile
import librosa
import soundfile as sf
from pydub import AudioSegment
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from ..models import Audio

logger = logging.getLogger(__name__)

class AudioProcessingService:
    """Service for processing audio files and performing various audio operations."""
    
    def __init__(self):
        self.supported_formats = ['wav', 'mp3', 'ogg', 'flac']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.sample_rate = 44100  # Standard sample rate
    
    def validate_audio_file(self, audio_file: InMemoryUploadedFile) -> Tuple[bool, str]:
        """
        Validate the audio file format and size.
        
        Args:
            audio_file: The uploaded audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not audio_file:
            return False, "No audio file provided"
            
        if audio_file.size > self.max_file_size:
            return False, f"File size exceeds maximum limit of {self.max_file_size/1024/1024}MB"
            
        file_extension = os.path.splitext(audio_file.name)[1].lower()[1:]
        if file_extension not in self.supported_formats:
            return False, f"Unsupported audio format. Supported formats: {', '.join(self.supported_formats)}"
            
        return True, ""
    
    def process_audio(self, audio_file: InMemoryUploadedFile) -> Optional[dict]:
        """
        Process the audio file and extract relevant features.
        
        Args:
            audio_file: The uploaded audio file
            
        Returns:
            Dictionary containing processed audio data and features
        """
        try:
            # Validate the audio file first
            is_valid, error_message = self.validate_audio_file(audio_file)
            if not is_valid:
                logger.error(f"Audio validation failed: {error_message}")
                return None
                
            # Save the file temporarily
            temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', audio_file.name)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            with open(temp_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
            
            # Load and process the audio file
            audio_data, sample_rate = librosa.load(temp_path, sr=self.sample_rate)
            
            # Extract basic features
            features = {
                'duration': librosa.get_duration(y=audio_data, sr=sample_rate),
                'sample_rate': sample_rate,
                'channels': 1 if len(audio_data.shape) == 1 else audio_data.shape[1],
                'rms_energy': np.mean(librosa.feature.rms(y=audio_data)),
                'zero_crossing_rate': np.mean(librosa.feature.zero_crossing_rate(y=audio_data)),
                'spectral_centroid': np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)),
            }
            
            # Clean up temporary file
            os.remove(temp_path)
            
            return features
            
        except Exception as e:
            logger.error(f"Error processing audio file: {str(e)}")
            return None
    
    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio data to a target level.
        
        Args:
            audio_data: The audio data to normalize
            
        Returns:
            Normalized audio data
        """
        return librosa.util.normalize(audio_data)
    
    def resample_audio(self, audio_data: np.ndarray, original_sr: int, target_sr: int) -> np.ndarray:
        """
        Resample audio data to a target sample rate.
        
        Args:
            audio_data: The audio data to resample
            original_sr: Original sample rate
            target_sr: Target sample rate
            
        Returns:
            Resampled audio data
        """
        return librosa.resample(audio_data, orig_sr=original_sr, target_sr=target_sr)
    
    def trim_silence(self, audio_data: np.ndarray, top_db: float = 20) -> np.ndarray:
        """
        Trim silence from the beginning and end of audio data.
        
        Args:
            audio_data: The audio data to trim
            top_db: The threshold (in decibels) below reference to consider as silence
            
        Returns:
            Trimmed audio data
        """
        return librosa.effects.trim(audio_data, top_db=top_db)[0]
    
    def compress_audio(self, audio_file, quality=0.5):
        """Compress an audio file with the specified quality (0.0 to 1.0)."""
        if not 0 <= quality <= 1:
            raise ValueError("Quality must be between 0.0 and 1.0")
        
        # Get the file path if it's a Django FileField
        if hasattr(audio_file, 'path'):
            file_path = audio_file.path
        else:
            # If it's a file object, save it temporarily
            temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', audio_file.name)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            with open(temp_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
            file_path = temp_path
        
        try:
            # Load the audio file
            audio = AudioSegment.from_file(file_path)
            
            # Calculate target bitrate based on quality
            # For MP3, typical bitrates are 32kbps to 320kbps
            min_bitrate = 32
            max_bitrate = 320
            target_bitrate = int(min_bitrate + (max_bitrate - min_bitrate) * quality)
            
            # Export with compression
            compressed_path = os.path.splitext(file_path)[0] + '_compressed.mp3'
            audio.export(
                compressed_path,
                format='mp3',
                bitrate=f'{target_bitrate}k'
            )
            
            # Read the compressed file
            with open(compressed_path, 'rb') as f:
                compressed_content = f.read()
            
            return compressed_content
            
        finally:
            # Clean up temporary files
            if not hasattr(audio_file, 'path'):
                os.remove(file_path)
            if os.path.exists(compressed_path):
                os.remove(compressed_path) 