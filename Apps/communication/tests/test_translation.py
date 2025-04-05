import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from Apps.communication.models import Translation, Language
from Apps.communication.services.translation import TranslationService
from Apps.communication.exceptions import TranslationError
from unittest.mock import Mock, patch
from django.core.cache import cache

class TestTranslationService(TestCase):
    def setUp(self):
        self.service = TranslationService()
        self.source_text = "Hello, world!"
        self.target_language = Language.objects.get_or_create(code="es", name="Spanish")[0]
        self.source_language = "en"
        self.target_text = "¡Hola, mundo!"
        self.quality_score = 0.95
        # Clear cache before each test
        cache.clear()

    def test_translate_text(self):
        # Arrange
        with patch('Apps.communication.services.translation.TranslationService._call_translation_api') as mock_translate:
            mock_translate.return_value = (self.target_text, self.quality_score)

            # Act
            result = self.service.translate_text(self.source_text, self.target_language.code)

            # Assert
            self.assertEqual(result.target_text, self.target_text)
            self.assertEqual(result.quality_score, self.quality_score)
            mock_translate.assert_called_once_with(self.source_text, self.target_language.code)

    def test_empty_text(self):
        with self.assertRaises(ValidationError):
            self.service.translate_text("", self.target_language.code)

    def test_invalid_language_code(self):
        with self.assertRaises(ValidationError):
            self.service.translate_text(self.source_text, "invalid")

    def test_translate_to_arabic(self):
        # Arrange
        arabic_language = Language.objects.get_or_create(code="ar", name="Arabic")[0]
        arabic_text = "مرحبا بالعالم"

        with patch('Apps.communication.services.translation.TranslationService._call_translation_api') as mock_translate:
            mock_translate.return_value = (arabic_text, self.quality_score)

            # Act
            result = self.service.translate_text(self.source_text, arabic_language.code)

            # Assert
            self.assertEqual(result.target_text, arabic_text)
            self.assertEqual(result.quality_score, self.quality_score)
            mock_translate.assert_called_once_with(self.source_text, arabic_language.code)

    def test_translation_analytics(self):
        # Arrange
        with patch('Apps.communication.services.translation.TranslationService._call_translation_api') as mock_translate:
            mock_translate.return_value = (self.target_text, self.quality_score)

            # Act
            result = self.service.translate_text(self.source_text, self.target_language.code)

            # Assert
            translation = Translation.objects.get(source_text=self.source_text)
            self.assertEqual(translation.quality_score, self.quality_score)
            self.assertEqual(translation.target_language, self.target_language)

    def test_translation_caching(self):
        # Arrange
        with patch('Apps.communication.services.translation.TranslationService._call_translation_api') as mock_translate:
            mock_translate.return_value = (self.target_text, self.quality_score)

            # Act
            # First call should hit the API
            result1 = self.service.translate_text(self.source_text, self.target_language.code)

            # Second call should use cache
            result2 = self.service.translate_text(self.source_text, self.target_language.code)

            # Assert
            self.assertEqual(result1.target_text, result2.target_text)
            self.assertEqual(result1.id, result2.id)
            mock_translate.assert_called_once()

    def test_detect_language(self):
        # Arrange
        text = "Hello, world!"
        expected_language = "en"

        with patch('Apps.communication.services.translation.TranslationService._detect_language') as mock_detect:
            mock_detect.return_value = expected_language

            # Act
            detected_language = self.service.detect_language(text)

            # Assert
            self.assertEqual(detected_language, expected_language)
            mock_detect.assert_called_once_with(text)

    def test_detect_arabic_language(self):
        # Arrange
        text = "مرحبا بالعالم"
        expected_language = "ar"

        with patch('Apps.communication.services.translation.TranslationService._detect_language') as mock_detect:
            mock_detect.return_value = expected_language

            # Act
            detected_language = self.service.detect_language(text)

            # Assert
            self.assertEqual(detected_language, expected_language)
            mock_detect.assert_called_once_with(text)

class TestTranslationModel(TestCase):
    def setUp(self):
        self.language = Language.objects.get_or_create(code="es", name="Spanish")[0]
        self.translation = Translation.objects.create(
            source_text="Hello",
            target_text="Hola",
            source_language="en",
            target_language=self.language,
            quality_score=0.95
        )

    def test_translation_creation(self):
        self.assertEqual(self.translation.source_text, "Hello")
        self.assertEqual(self.translation.target_text, "Hola")
        self.assertEqual(self.translation.source_language, "en")
        self.assertEqual(self.translation.target_language, self.language)
        self.assertEqual(self.translation.quality_score, 0.95)

    def test_translation_str(self):
        expected = "Translation from en to es: Hello -> Hola"
        self.assertEqual(str(self.translation), expected)

    def test_language_str(self):
        expected = "Spanish (es)"
        self.assertEqual(str(self.language), expected)

    def test_arabic_translation_creation(self):
        arabic = Language.objects.get_or_create(code="ar", name="Arabic")[0]
        translation = Translation.objects.create(
            source_text="Hello",
            target_text="مرحبا",
            source_language="en",
            target_language=arabic,
            quality_score=0.95
        )
        self.assertEqual(translation.target_text, "مرحبا")
        self.assertEqual(translation.target_language.code, "ar")

    def test_arabic_translation_str(self):
        arabic = Language.objects.get_or_create(code="ar", name="Arabic")[0]
        translation = Translation.objects.create(
            source_text="Hello",
            target_text="مرحبا",
            source_language="en",
            target_language=arabic,
            quality_score=0.95
        )
        expected = "Translation from en to ar: Hello -> مرحبا"
        self.assertEqual(str(translation), expected) 