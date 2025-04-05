from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from Apps.communication.consumers import ChatConsumer
import json
import pytest
import pytest_asyncio

User = get_user_model()

@pytest.mark.django_db
@pytest.mark.asyncio
class BasicCommunicationTest:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        self.user = await User.objects.acreate(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.channel_layer = get_channel_layer()

    async def test_websocket_connection(self):
        """
        Test that a user can establish a WebSocket connection
        """
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.user.id}/"
        )
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_send_message(self):
        """
        Test that a user can send a message through WebSocket
        """
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.user.id}/"
        )
        await communicator.connect()

        # Send a message
        message = {
            'type': 'chat.message',
            'message': 'Hello, world!',
            'user_id': self.user.id
        }
        await communicator.send_json_to(message)

        # Receive the message
        response = await communicator.receive_json_from()
        assert response['message'] == 'Hello, world!'
        assert response['user_id'] == self.user.id

        await communicator.disconnect()

    async def test_receive_message(self):
        """
        Test that a user can receive messages sent to them
        """
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.user.id}/"
        )
        await communicator.connect()

        # Send a message through the channel layer
        await self.channel_layer.group_send(
            f"chat_{self.user.id}",
            {
                'type': 'chat_message',
                'message': 'Test message',
                'user_id': self.user.id
            }
        )

        # Receive the message
        response = await communicator.receive_json_from()
        assert response['message'] == 'Test message'
        assert response['user_id'] == self.user.id

        await communicator.disconnect() 