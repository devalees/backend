import openai
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import File
from typing import Dict, Optional, Union
import os
import mimetypes

class TranscriptionService:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        openai.api_key = self.api_key

        # Supported languages and their locales
        self.supported_languages = {
            'ar': ['ar-SA', 'ar-EG', 'ar-AE', 'ar-MA', 'ar-TN'],  # Arabic locales
            'en': ['en-US', 'en-GB', 'en-AU', 'en-CA']  # English locales
        }

    def transcribe_audio(self, audio_file: Union[UploadedFile, File], language: str = 'auto') -> Dict[str, str]:
        """
        Transcribe an audio file using OpenAI's Whisper model.
        
        Args:
            audio_file: The audio file to transcribe (can be UploadedFile or FieldFile)
            language: The language code or locale (default: 'auto' for auto-detection)
                    Supported values:
                    - 'auto': Auto-detect language
                    - 'ar': Arabic (default locale)
                    - 'en': English (default locale)
                    - Specific locales (e.g., 'ar-SA', 'en-US')
            
        Returns:
            Dict containing the transcribed text and detected language
        """
        self._validate_audio_file(audio_file)
        self._validate_language(language)
        
        try:
            # Prepare parameters for OpenAI API
            params = {
                "model": "whisper-1",
                "file": audio_file
            }
            
            # Only add language parameter if not auto-detection
            if language != 'auto':
                params["language"] = language
            
            response = openai.Audio.transcribe(**params)
            
            # Get the detected language if auto-detection was used
            detected_language = language if language != 'auto' else response.get('language', 'unknown')
            
            return {
                "text": response.get('text', ''),
                "language": detected_language
            }
        except Exception as e:
            raise Exception(f"API Error: {str(e)}")

    def _validate_audio_file(self, audio_file):
        """Validate the audio file."""
        allowed_types = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/webm']
        
        # Get content type from the file object
        content_type = getattr(audio_file, 'content_type', None)
        
        # If content_type is not available, try to get it from the file name
        if not content_type and hasattr(audio_file, 'name'):
            content_type = mimetypes.guess_type(audio_file.name)[0]
        
        if not content_type or content_type not in allowed_types:
            raise ValueError(f"Invalid file type. Allowed types: {', '.join(allowed_types)}")

        # Check file size (25MB limit)
        if hasattr(audio_file, 'size') and audio_file.size > 25 * 1024 * 1024:
            raise ValueError("File size exceeds 25MB limit")

    def _validate_language(self, language: str) -> bool:
        """
        Validate the language parameter.
        
        Args:
            language: The language code or locale to validate
            
        Returns:
            bool: True if language is valid
            
        Raises:
            ValueError: If language is invalid
        """
        if language == 'auto':
            return True
            
        # Check if it's a base language code
        if language in self.supported_languages:
            return True
            
        # Check if it's a specific locale
        for locales in self.supported_languages.values():
            if language in locales:
                return True
                
        raise ValueError(
            f"Unsupported language. Supported values: 'auto', 'ar', 'en', or specific locales like "
            f"{', '.join([loc for locales in self.supported_languages.values() for loc in locales])}"
        ) 