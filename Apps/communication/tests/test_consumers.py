from channels.testing import WebsocketCommunicator
from django.test import TestCase
from django.urls import path
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from Core.asgi import application
from Apps.communication.consumers import ChatConsumer
from django.contrib.auth import get_user_model
import json

# Import your consumer here
# from ..consumers import MyConsumer

User = get_user_model()

class WebSocketConsumerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    async def test_websocket_connection(self):
        # Use the application with routing from Core.asgi
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"ws/chat/{self.user.id}/"
        )
        communicator.scope['url_route'] = {'kwargs': {'user_id': str(self.user.id)}}
        connected, _ = await communicator.connect()
        assert connected

        # Test sending and receiving messages
        message = {
            'message': 'Hello',
            'user_id': self.user.id
        }
        await communicator.send_to(text_data=json.dumps(message))
        response = await communicator.receive_from()
        assert json.loads(response)['message'] == 'Hello'

        # Test disconnection
        await communicator.disconnect() 