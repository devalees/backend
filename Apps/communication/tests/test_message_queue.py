from django.test import TestCase
from channels.layers import get_channel_layer
from channels.testing import ApplicationCommunicator
from channels.consumer import AsyncConsumer

class TestConsumer(AsyncConsumer):
    async def handle_test_message(self, message):
        """
        Handle test.message type messages
        """
        await self.send({
            "type": "test.message",
            "text": message["text"],
        })

class MessageQueueTest(TestCase):
    async def test_redis_connection(self):
        channel_layer = get_channel_layer()
        assert channel_layer is not None

    async def test_message_handling(self):
        channel_layer = get_channel_layer()
        await channel_layer.send('test_channel', {'type': 'handle.test.message', 'text': 'Hello'})

        # Create a communicator to simulate a consumer
        communicator = ApplicationCommunicator(TestConsumer(), {
            'type': 'handle.test.message',
            'channel': 'test_channel',
        })
        await communicator.send_input({'type': 'handle.test.message', 'text': 'Hello'})

        # Receive the message
        response = await communicator.receive_output()
        assert response['text'] == 'Hello' 