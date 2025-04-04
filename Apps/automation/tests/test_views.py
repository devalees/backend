import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from Apps.automation.models import (
    Workflow,
    Node,
    Connection,
    WorkflowTemplate
)

User = get_user_model()

@pytest.mark.django_db
class TestVisualWorkflowViews:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def test_user(self):
        return User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def authenticated_client(self, api_client, test_user):
        api_client.force_authenticate(user=test_user)
        return api_client

    @pytest.fixture
    def workflow(self, test_user):
        return Workflow.objects.create(
            name="Test Workflow",
            description="Test workflow for API testing",
            created_by=test_user
        )

    def test_create_node(self, authenticated_client, workflow):
        """Test creating a node through the API"""
        url = reverse('automation:node-list')
        data = {
            'name': 'API Test Node',
            'workflow': workflow.id,
            'node_type': 'trigger',
            'configuration': {
                'trigger_type': 'time',
                'schedule': 'daily'
            },
            'position_x': 100,
            'position_y': 200
        }

        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'API Test Node'
        assert response.data['node_type'] == 'trigger'
        assert response.data['position_x'] == 100

    def test_update_node_position(self, authenticated_client, workflow, test_user):
        """Test updating node position through the API"""
        node = Node.objects.create(
            name="Position Test Node",
            workflow=workflow,
            node_type="action",
            configuration={"action_type": "email"},
            position_x=100,
            position_y=100,
            created_by=test_user
        )

        url = reverse('automation:node-detail', args=[node.id])
        data = {
            'position_x': 150,
            'position_y': 250
        }

        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['position_x'] == 150
        assert response.data['position_y'] == 250

    def test_create_connection(self, authenticated_client, workflow, test_user):
        """Test creating a connection through the API"""
        source_node = Node.objects.create(
            name="Source Node",
            workflow=workflow,
            node_type="trigger",
            configuration={"trigger_type": "time"},
            created_by=test_user
        )
        target_node = Node.objects.create(
            name="Target Node",
            workflow=workflow,
            node_type="action",
            configuration={"action_type": "email"},
            created_by=test_user
        )

        url = reverse('automation:connection-list')
        data = {
            'name': 'API Test Connection',
            'workflow': workflow.id,
            'source_node': source_node.id,
            'target_node': target_node.id,
            'configuration': {'condition': 'always'}
        }

        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'API Test Connection'
        assert response.data['source_node'] == source_node.id
        assert response.data['target_node'] == target_node.id

    def test_create_workflow_template(self, authenticated_client):
        """Test creating a workflow template through the API"""
        url = reverse('automation:workflowtemplate-list')
        data = {
            'name': 'API Test Template',
            'description': 'Template created through API',
            'configuration': {
                'nodes': [
                    {
                        'type': 'trigger',
                        'name': 'Start',
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
                        'from': 'Start',
                        'to': 'Send Email'
                    }
                ]
            }
        }

        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'API Test Template'
        assert len(response.data['configuration']['nodes']) == 2

    def test_validate_workflow(self, authenticated_client, workflow, test_user):
        """Test workflow validation through the API"""
        # Create nodes and connections for validation
        trigger_node = Node.objects.create(
            name="Trigger",
            workflow=workflow,
            node_type="trigger",
            configuration={"trigger_type": "time"},
            created_by=test_user
        )
        action_node = Node.objects.create(
            name="Action",
            workflow=workflow,
            node_type="action",
            configuration={"action_type": "email"},
            created_by=test_user
        )
        Connection.objects.create(
            workflow=workflow,
            source_node=trigger_node,
            target_node=action_node,
            configuration={"condition": "always"},
            created_by=test_user
        )

        url = reverse('automation:workflow-validate', args=[workflow.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_valid'] is True

    def test_instantiate_template(self, authenticated_client, test_user):
        """Test instantiating a workflow from a template through the API"""
        # Create a template first
        template = WorkflowTemplate.objects.create(
            name="Test Template",
            configuration={
                'nodes': [
                    {
                        'type': 'trigger',
                        'name': 'Start',
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
                        'from': 'Start',
                        'to': 'Send Email'
                    }
                ]
            },
            created_by=test_user
        )

        url = reverse('automation:workflowtemplate-instantiate', args=[template.id])
        data = {
            'name': 'New Workflow from Template',
            'description': 'Workflow created from template'
        }

        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Workflow from Template'
        assert 'nodes' in response.data
        assert 'connections' in response.data
        assert len(response.data['nodes']) == 2
        assert len(response.data['connections']) == 1 