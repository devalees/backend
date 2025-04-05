from django.test import TestCase
from django.contrib.auth import get_user_model
from Apps.communication.models import Message, Thread, Channel, Notification

User = get_user_model()

class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='testpass')
        self.thread = Thread.objects.create(title='Test Thread')

    def test_create_message(self):
        message = Message.objects.create(content='Hello, World!', sender=self.user, thread=self.thread)
        self.assertEqual(message.content, 'Hello, World!')
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.thread, self.thread)

class ThreadModelTest(TestCase):
    def test_create_thread(self):
        thread = Thread.objects.create(title='Test Thread')
        self.assertEqual(thread.title, 'Test Thread')

class ChannelModelTest(TestCase):
    def test_create_channel(self):
        channel = Channel.objects.create(name='Test Channel')
        self.assertEqual(channel.name, 'Test Channel')

class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='testpass')

    def test_create_notification(self):
        notification = Notification.objects.create(content='You have a new message', user=self.user)
        self.assertEqual(notification.content, 'You have a new message')
        self.assertEqual(notification.user, self.user) 