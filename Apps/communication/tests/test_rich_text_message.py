import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from Apps.communication.models import Thread, RichTextMessage
from bs4 import BeautifulSoup
from django.test import TestCase
from Apps.communication.serializers import RichTextMessageSerializer
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.fixture
def user1(transactional_db):
    return User.objects.create_user(
        username='user1',
        email='user1@example.com',
        password='testpass123'
    )

@pytest.fixture
def user2(transactional_db):
    return User.objects.create_user(
        username='user2',
        email='user2@example.com',
        password='testpass123'
    )

@pytest.fixture
def thread(transactional_db, user1, user2):
    thread = Thread.objects.create(
        title='Test Thread',
        created_by=user1
    )
    thread.participants.add(user1, user2)
    return thread

def normalize_html(html):
    """Normalize HTML string for comparison."""
    soup = BeautifulSoup(html, 'html.parser')
    return str(soup).strip()

@pytest.mark.django_db(transaction=True)
def test_create_rich_text_message(user1, thread):
    """Test creating a rich text message with basic formatting"""
    content = '<p>Hello <strong>World</strong>!</p>'
    message = RichTextMessage.objects.create(
        content=content,
        sender=user1,
        thread=thread
    )
    assert normalize_html(message.content) == normalize_html(content)
    assert message.sender == user1
    assert message.thread == thread

@pytest.mark.django_db(transaction=True)
def test_rich_text_message_formatting(user1, thread):
    """Test various rich text formatting options"""
    test_cases = [
        ('<p>Bold: <strong>text</strong></p>', 'Bold text'),
        ('<p>Italic: <em>text</em></p>', 'Italic text'),
        ('<p>Underline: <u>text</u></p>', 'Underline text'),
        ('<p>Strikethrough: text</p>', 'Strikethrough text'),
        ('<p>Link: <a href="https://example.com">text</a></p>', 'Link text'),
        ('<p>Code: <code>print("hello")</code></p>', 'Code print("hello")')
    ]
    
    for html, expected_text in test_cases:
        message = RichTextMessage.objects.create(
            content=html,
            sender=user1,
            thread=thread
        )
        assert normalize_html(message.content) == normalize_html(html)
        assert message.get_preview() == expected_text

@pytest.mark.django_db(transaction=True)
def test_list_formatting(user1, thread):
    """Test list formatting specifically"""
    content = '''
    <p>List:</p>
    <ul>
        <li>item1</li>
        <li>item2</li>
    </ul>
    '''
    message = RichTextMessage.objects.create(
        content=content,
        sender=user1,
        thread=thread
    )
    
    soup = BeautifulSoup(message.content, 'html.parser')
    assert soup.find('p').text.strip() == 'List:'
    assert len(soup.find('ul').find_all('li')) == 2
    assert [li.text.strip() for li in soup.find('ul').find_all('li')] == ['item1', 'item2']

@pytest.mark.django_db(transaction=True)
def test_media_embedding(user1, thread):
    """Test embedding media in rich text messages"""
    content = '''
    <p>Here's an image:</p>
    <img src="https://example.com/image.jpg" alt="Test Image">
    <p>And a video:</p>
    <iframe src="https://example.com/video.mp4"></iframe>
    '''
    
    message = RichTextMessage.objects.create(
        content=content,
        sender=user1,
        thread=thread
    )
    
    soup = BeautifulSoup(message.content, 'html.parser')
    img = soup.find('img')
    iframe = soup.find('iframe')
    
    assert img is not None
    assert img['src'] == 'https://example.com/image.jpg'
    assert img['alt'] == 'Test Image'
    assert iframe is not None
    assert iframe['src'] == 'https://example.com/video.mp4'

@pytest.mark.django_db(transaction=True)
def test_content_validation(user1, thread):
    """Test content validation for rich text messages"""
    # Test valid HTML content
    valid_content = '<p>Valid content</p>'
    message = RichTextMessage.objects.create(
        content=valid_content,
        sender=user1,
        thread=thread
    )
    assert normalize_html(message.content) == normalize_html(valid_content)

    # Test script tags
    with pytest.raises(ValidationError, match='Script tags are not allowed'):
        RichTextMessage.objects.create(
            content='<script>alert("xss")</script>',
            sender=user1,
            thread=thread
        )

@pytest.mark.django_db(transaction=True)
def test_html_sanitization(user1, thread):
    """Test that HTML content is properly sanitized"""
    # Test script tags
    with pytest.raises(ValidationError, match='Script tags are not allowed'):
        RichTextMessage.objects.create(
            content='<p>Safe content</p><script>alert("unsafe")</script>',
            sender=user1,
            thread=thread
        )

    # Test javascript: URLs in img tags
    with pytest.raises(ValidationError, match='JavaScript URLs are not allowed in image src'):
        RichTextMessage.objects.create(
            content='<img src="javascript:alert(\'xss\')">',
            sender=user1,
            thread=thread
        )

    # Test javascript: URLs in iframe tags
    with pytest.raises(ValidationError, match='JavaScript URLs are not allowed in iframe src'):
        RichTextMessage.objects.create(
            content='<iframe src="javascript:alert(\'xss\')"></iframe>',
            sender=user1,
            thread=thread
        )

@pytest.mark.django_db(transaction=True)
def test_image_validation(user1, thread):
    """Test validation of image tags"""
    # Test image without src attribute
    with pytest.raises(ValidationError, match='Image tags must have a src attribute'):
        RichTextMessage.objects.create(
            content='<img alt="test">',
            sender=user1,
            thread=thread
        )

    # Test valid image tag
    valid_content = '<img src="https://example.com/image.jpg" alt="test">'
    message = RichTextMessage.objects.create(
        content=valid_content,
        sender=user1,
        thread=thread
    )
    soup = BeautifulSoup(message.content, 'html.parser')
    img = soup.find('img')
    assert img is not None
    assert img['src'] == 'https://example.com/image.jpg'
    assert img['alt'] == 'test'

@pytest.mark.django_db(transaction=True)
def test_iframe_validation(user1, thread):
    """Test validation of iframe tags"""
    # Test iframe without src attribute
    with pytest.raises(ValidationError, match='Iframe tags must have a src attribute'):
        RichTextMessage.objects.create(
            content='<iframe></iframe>',
            sender=user1,
            thread=thread
        )

    # Test valid iframe tag
    valid_content = '<iframe src="https://example.com/embed" width="560" height="315"></iframe>'
    message = RichTextMessage.objects.create(
        content=valid_content,
        sender=user1,
        thread=thread
    )
    soup = BeautifulSoup(message.content, 'html.parser')
    iframe = soup.find('iframe')
    assert iframe is not None
    assert iframe['src'] == 'https://example.com/embed'
    assert iframe['width'] == '560'
    assert iframe['height'] == '315'

@pytest.mark.django_db(transaction=True)
def test_message_preview(user1, thread):
    """Test message preview generation"""
    content = '<p>This is a test message</p>'
    message = RichTextMessage.objects.create(
        content=content,
        sender=user1,
        thread=thread
    )
    assert message.get_preview() == 'This is a test message'

@pytest.mark.django_db(transaction=True)
def test_long_message_preview(user1, thread):
    """Test preview generation for long messages"""
    long_text = 'This is a very long message that should be truncated in the preview. ' * 10
    content = f'<p>{long_text}</p>'
    message = RichTextMessage.objects.create(
        content=content,
        sender=user1,
        thread=thread
    )
    preview = message.get_preview()
    assert len(preview) <= 200
    assert preview.endswith('...')

@pytest.mark.django_db(transaction=True)
def test_allowed_attributes(user1, thread):
    """Test that only allowed attributes are preserved"""
    content = '<p style="color: red;" class="test">Test</p>'
    message = RichTextMessage.objects.create(
        content=content,
        sender=user1,
        thread=thread
    )
    soup = BeautifulSoup(message.content, 'html.parser')
    p = soup.find('p')
    assert 'style' not in p.attrs
    assert 'class' not in p.attrs

class TestRichTextMessage(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.thread = Thread.objects.create(
            title='Test Thread',
            created_by=self.user
        )
        self.thread.participants.add(self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.request = type('Request', (), {'user': self.user})()

    def test_create_rich_text_message(self):
        """Test creating a rich text message with basic formatting"""
        data = {
            'content': '<p>This is a <strong>test</strong> message</p>',
            'thread': self.thread.id
        }
        serializer = RichTextMessageSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save(sender=self.user)
        self.assertEqual(message.content, data['content'])

    def test_message_with_invalid_html(self):
        """Test message creation with invalid HTML content"""
        data = {
            'content': '<script>alert("xss")</script>',
            'thread': self.thread.id
        }
        serializer = RichTextMessageSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid(), "Serializer should be invalid for script tags")
        self.assertIn('Script tags are not allowed', str(serializer.errors['content']))

    def test_message_with_media_embed(self):
        """Test creating a message with embedded media"""
        data = {
            'content': '<p>Here\'s an image:</p><img src="https://example.com/image.jpg" alt="Test">',
            'thread': self.thread.id
        }
        serializer = RichTextMessageSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save(sender=self.user)
        self.assertIn('image.jpg', message.content)

    def test_message_with_unsafe_content(self):
        """Test message creation with potentially unsafe content"""
        data = {
            'content': '<p>Safe content</p><img src="javascript:alert(\'xss\')" onerror="alert(\'xss\')">',
            'thread': self.thread.id
        }
        serializer = RichTextMessageSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid(), "Serializer should be invalid for unsafe content")
        self.assertIn('Event handlers are not allowed in HTML content', str(serializer.errors['content']), "Expected error message about event handlers")

    def test_message_preview(self):
        """Test message preview functionality"""
        data = {
            'content': '<p>This is a test message with <strong>formatting</strong> and some length to it.</p>',
            'thread': self.thread.id
        }
        serializer = RichTextMessageSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save(sender=self.user)
        preview = message.get_preview()
        self.assertLessEqual(len(preview), 100)
        self.assertIn('formatting', preview) 