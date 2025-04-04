import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIRequestFactory
from Apps.automation.models import (
    Workflow,
    Node,
    Connection,
    WorkflowTemplate
)
from Apps.automation.serializers import (
    NodeSerializer,
    ConnectionSerializer,
    WorkflowTemplateSerializer
)

User = get_user_model()

@pytest.mark.django_db
class TestNodeSerializer:
    @pytest.fixture
    def test_user(self):
        return User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def workflow(self, test_user):
        return Workflow.objects.create(
            name="Test Workflow",
            description="Test workflow for serializer testing",
            created_by=test_user
        )

    @pytest.fixture
    def request_factory(self):
        return APIRequestFactory()

    def test_node_serializer_valid_data(self, workflow, test_user, request_factory):
        """Test node serializer with valid data"""
        data = {
            'name': 'Test Node',
            'workflow': workflow.id,
            'node_type': 'trigger',
            'configuration': {
                'trigger_type': 'time',
                'schedule': 'daily'
            },
            'position_x': 100,
            'position_y': 200
        }
        
        request = request_factory.post('/fake-url/')
        request.user = test_user
        
        serializer = NodeSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        
        node = serializer.save()
        assert node.name == 'Test Node'
        assert node.workflow == workflow
        assert node.node_type == 'trigger'
        assert node.configuration == {'trigger_type': 'time', 'schedule': 'daily'}
        assert node.position_x == 100
        assert node.position_y == 200
        assert node.created_by == test_user

    def test_node_serializer_invalid_type(self, workflow, test_user, request_factory):
        """Test node serializer with invalid node type"""
        data = {
            'name': 'Invalid Node',
            'workflow': workflow.id,
            'node_type': 'invalid_type',
            'configuration': {'type': 'invalid'}
        }
        
        request = request_factory.post('/fake-url/')
        request.user = test_user
        
        serializer = NodeSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'node_type' in serializer.errors

    def test_node_serializer_missing_config(self, workflow, test_user, request_factory):
        """Test node serializer with missing configuration"""
        data = {
            'name': 'Missing Config Node',
            'workflow': workflow.id,
            'node_type': 'trigger'
        }
        
        request = request_factory.post('/fake-url/')
        request.user = test_user
        
        serializer = NodeSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'configuration' in serializer.errors

@pytest.mark.django_db
class TestConnectionSerializer:
    @pytest.fixture
    def test_user(self):
        return User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def workflow(self, test_user):
        return Workflow.objects.create(
            name="Test Workflow",
            description="Test workflow for serializer testing",
            created_by=test_user
        )

    @pytest.fixture
    def source_node(self, workflow, test_user):
        return Node.objects.create(
            name="Source Node",
            workflow=workflow,
            node_type="trigger",
            configuration={"trigger_type": "time", "schedule": "daily"},
            created_by=test_user
        )

    @pytest.fixture
    def target_node(self, workflow, test_user):
        return Node.objects.create(
            name="Target Node",
            workflow=workflow,
            node_type="action",
            configuration={"action_type": "email", "recipient": "test@example.com"},
            created_by=test_user
        )

    @pytest.fixture
    def request_factory(self):
        return APIRequestFactory()

    def test_connection_serializer_valid_data(self, workflow, source_node, target_node, test_user, request_factory):
        """Test connection serializer with valid data"""
        data = {
            'name': 'Test Connection',
            'workflow': workflow.id,
            'source_node': source_node.id,
            'target_node': target_node.id,
            'configuration': {'condition': 'always'}
        }
        
        request = request_factory.post('/fake-url/')
        request.user = test_user
        
        serializer = ConnectionSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        
        connection = serializer.save()
        assert connection.name == 'Test Connection'
        assert connection.workflow == workflow
        assert connection.source_node == source_node
        assert connection.target_node == target_node
        assert connection.configuration == {'condition': 'always'}
        assert connection.created_by == test_user

    def test_connection_serializer_self_connection(self, workflow, source_node, test_user, request_factory):
        """Test connection serializer with self-connection"""
        data = {
            'name': 'Self Connection',
            'workflow': workflow.id,
            'source_node': source_node.id,
            'target_node': source_node.id,
            'configuration': {'condition': 'always'}
        }
        
        request = request_factory.post('/fake-url/')
        request.user = test_user
        
        serializer = ConnectionSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

@pytest.mark.django_db
class TestWorkflowTemplateSerializer:
    @pytest.fixture
    def test_user(self):
        return User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def request_factory(self):
        return APIRequestFactory()

    def test_workflow_template_serializer_valid_data(self, test_user, request_factory):
        """Test workflow template serializer with valid data"""
        data = {
            'name': 'Email Notification Template',
            'description': 'Template for email notifications',
            'configuration': {
                'nodes': [
                    {
                        'type': 'trigger',
                        'name': 'Time Trigger',
                        'config': {'trigger_type': 'time', 'schedule': 'daily'}
                    },
                    {
                        'type': 'action',
                        'name': 'Send Email',
                        'config': {'action_type': 'email'}
                    }
                ],
                'connections': [
                    {
                        'from': 'Time Trigger',
                        'to': 'Send Email'
                    }
                ]
            }
        }
        
        request = request_factory.post('/fake-url/')
        request.user = test_user
        
        serializer = WorkflowTemplateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        
        template = serializer.save()
        assert template.name == 'Email Notification Template'
        assert len(template.configuration['nodes']) == 2
        assert len(template.configuration['connections']) == 1
        assert template.created_by == test_user

    def test_workflow_template_serializer_invalid_config(self, test_user, request_factory):
        """Test workflow template serializer with invalid configuration"""
        data = {
            'name': 'Invalid Template',
            'description': 'Template with invalid configuration',
            'configuration': {
                'invalid': 'data'
            }
        }
        
        request = request_factory.post('/fake-url/')
        request.user = test_user
        
        serializer = WorkflowTemplateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'configuration' in serializer.errors or 'non_field_errors' in serializer.errors 