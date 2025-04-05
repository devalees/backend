import logging
import hashlib
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ValidationError
from ..models import Translation, Language
from ..exceptions import TranslationError

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.cache_timeout = getattr(settings, 'TRANSLATION_CACHE_TIMEOUT', 3600)
        self.supported_languages = self._get_supported_languages()
        self._ensure_default_languages()
    
    def _get_supported_languages(self):
        """Get list of supported languages from database"""
        return list(Language.objects.values_list('code', flat=True))
    
    def _ensure_default_languages(self):
        """Ensure default languages exist in the database"""
        default_languages = [
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
            ('ar', 'Arabic')
        ]
        for code, name in default_languages:
            Language.objects.get_or_create(code=code, defaults={'name': name})
        # Refresh supported languages
        self.supported_languages = self._get_supported_languages()
    
    def _validate_language(self, language_code):
        """Validate if language code is supported"""
        if language_code not in self.supported_languages:
            raise ValidationError(f"Unsupported language code: {language_code}")
    
    def _validate_text(self, text):
        """Validate input text"""
        if not text or not text.strip():
            raise ValidationError("Text cannot be empty")
    
    def _get_cache_key(self, text, target_language):
        """Generate cache key for translation"""
        # Create a hash of the text to avoid special characters in cache key
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"trans_{text_hash}_{target_language}"
    
    def _call_translation_api(self, text, target_language):
        """
        Call external translation API
        This is a placeholder - implement with actual API call
        """
        # TODO: Implement actual API call
        # For now, return mock translation
        mock_translations = {
            "es": ("¡Hola, mundo!", 0.95),
            "fr": ("Bonjour le monde!", 0.95),
            "de": ("Hallo Welt!", 0.95),
            "ar": ("مرحبا بالعالم", 0.95)  # Added Arabic translation
        }
        return mock_translations.get(target_language, (text, 0.95))
    
    def _detect_language(self, text):
        """
        Detect language of input text
        """
        # TODO: Implement actual language detection
        # For now, return mock detection
        mock_detections = {
            "Hola": "es",
            "Bonjour": "fr",
            "Hallo": "de",
            "مرحباً": "ar"  # Added Arabic detection
        }
        for word, lang in mock_detections.items():
            if word in text:
                return lang
        return "en"  # Default to English
    
    def detect_language(self, text):
        """
        Public method to detect language of input text
        """
        return self._detect_language(text)
    
    def translate_text(self, text, target_language):
        """
        Translate text to target language
        """
        try:
            # Validate inputs
            self._validate_text(text)
            self._validate_language(target_language)
            
            # Check cache
            cache_key = self._get_cache_key(text, target_language)
            cached_translation = cache.get(cache_key)
            
            if cached_translation:
                logger.debug(f"Cache hit for translation: {cache_key}")
                return Translation.objects.get(id=cached_translation)
            
            # Get translation from API
            translated_text, quality_score = self._call_translation_api(text, target_language)
            
            # Store in database
            translation = Translation.objects.create(
                source_text=text,
                target_text=translated_text,
                source_language=Language.objects.get(code=self._detect_language(text)),
                target_language=Language.objects.get(code=target_language),
                quality_score=quality_score
            )
            
            # Cache the translation ID
            cache.set(cache_key, translation.id, self.cache_timeout)
            
            return translation
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise  # Re-raise ValidationError without wrapping
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise TranslationError(f"Translation failed: {str(e)}")
    
    def get_analytics(self):
        """
        Get translation analytics
        """
        total_translations = Translation.objects.count()
        languages = {}
        
        for lang in self.supported_languages:
            count = Translation.objects.filter(target_language__code=lang).count()
            languages[lang] = count
        
        return {
            'total_translations': total_translations,
            'languages': languages
        } 