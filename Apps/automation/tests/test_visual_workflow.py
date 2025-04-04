import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from Apps.automation.models import (
    Workflow,
    Node,
    Connection,
    WorkflowTemplate
)

User = get_user_model()

@pytest.mark.django_db
class TestVisualWorkflow:
    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def workflow(self, test_user):
        """Create a test workflow"""
        return Workflow.objects.create(
            name="Test Workflow",
            description="Test workflow for visual automation",
            created_by=test_user
        )

    def test_create_node(self, workflow, test_user):
        """Test creating a node in the visual workflow"""
        node = Node.objects.create(
            name="Start Node",
            workflow=workflow,
            node_type="trigger",
            configuration={"trigger_type": "time", "schedule": "daily"},
            position_x=100,
            position_y=100,
            created_by=test_user
        )

        assert node.name == "Start Node"
        assert node.workflow == workflow
        assert node.node_type == "trigger"
        assert node.configuration == {"trigger_type": "time", "schedule": "daily"}
        assert node.position_x == 100
        assert node.position_y == 100
        assert node.is_active is True

    def test_create_connection(self, workflow, test_user):
        """Test creating a connection between nodes"""
        source_node = Node.objects.create(
            name="Source Node",
            workflow=workflow,
            node_type="trigger",
            configuration={"trigger_type": "time", "schedule": "daily"},
            created_by=test_user
        )
        
        target_node = Node.objects.create(
            name="Target Node",
            workflow=workflow,
            node_type="action",
            configuration={"action_type": "email", "recipient": "test@example.com"},
            created_by=test_user
        )

        connection = Connection.objects.create(
            name="Test Connection",
            workflow=workflow,
            source_node=source_node,
            target_node=target_node,
            configuration={"condition": "always"},
            created_by=test_user
        )

        assert connection.workflow == workflow
        assert connection.source_node == source_node
        assert connection.target_node == target_node
        assert connection.configuration == {"condition": "always"}
        assert connection.is_active is True

    def test_node_validation(self, workflow, test_user):
        """Test node validation rules"""
        # Test invalid node type
        with pytest.raises(ValidationError):
            node = Node(
                name="Invalid Node",
                workflow=workflow,
                node_type="invalid_type",
                configuration={"type": "invalid"},
                created_by=test_user
            )
            node.full_clean()

        # Test missing name
        with pytest.raises(ValidationError):
            node = Node(
                workflow=workflow,
                node_type="trigger",
                configuration={"trigger_type": "time"},
                created_by=test_user
            )
            node.full_clean()

    def test_connection_validation(self, workflow, test_user):
        """Test connection validation rules"""
        source_node = Node.objects.create(
            name="Source Node",
            workflow=workflow,
            node_type="trigger",
            configuration={"trigger_type": "time", "schedule": "daily"},
            created_by=test_user
        )
        
        target_node = Node.objects.create(
            name="Target Node",
            workflow=workflow,
            node_type="action",
            configuration={"action_type": "email", "recipient": "test@example.com"},
            created_by=test_user
        )

        # Test connecting node to itself
        with pytest.raises(ValidationError):
            connection = Connection(
                workflow=workflow,
                source_node=source_node,
                target_node=source_node,
                configuration={"condition": "always"},
                created_by=test_user
            )
            connection.full_clean()

        # Create another workflow to test cross-workflow connections
        other_workflow = Workflow.objects.create(
            name="Other Workflow",
            created_by=test_user
        )
        other_node = Node.objects.create(
            name="Other Node",
            workflow=other_workflow,
            node_type="action",
            configuration={"action_type": "email"},
            created_by=test_user
        )

        # Test connecting nodes from different workflows
        with pytest.raises(ValidationError):
            connection = Connection(
                workflow=workflow,
                source_node=source_node,
                target_node=other_node,
                configuration={"condition": "always"},
                created_by=test_user
            )
            connection.full_clean()

    def test_workflow_template(self, test_user):
        """Test creating and using workflow templates"""
        template = WorkflowTemplate.objects.create(
            name="Email Notification Flow",
            description="Template for email notification workflows",
            configuration={
                "nodes": [
                    {
                        "type": "trigger",
                        "name": "Time Trigger",
                        "config": {"trigger_type": "time", "schedule": "daily"}
                    },
                    {
                        "type": "action",
                        "name": "Send Email",
                        "config": {"action_type": "email"}
                    }
                ],
                "connections": [
                    {
                        "from": "Time Trigger",
                        "to": "Send Email"
                    }
                ]
            },
            created_by=test_user
        )

        assert template.name == "Email Notification Flow"
        assert "nodes" in template.configuration
        assert "connections" in template.configuration
        assert len(template.configuration["nodes"]) == 2
        assert len(template.configuration["connections"]) == 1

    def test_node_positions(self, workflow, test_user):
        """Test node positioning in the visual designer"""
        node1 = Node.objects.create(
            name="Node 1",
            workflow=workflow,
            node_type="trigger",
            configuration={"trigger_type": "time", "schedule": "daily"},
            position_x=100,
            position_y=200,
            created_by=test_user
        )

        node2 = Node.objects.create(
            name="Node 2",
            workflow=workflow,
            node_type="action",
            configuration={"action_type": "email", "recipient": "test@example.com"},
            position_x=300,
            position_y=200,
            created_by=test_user
        )

        assert node1.position_x == 100
        assert node1.position_y == 200
        assert node2.position_x == 300
        assert node2.position_y == 200

        # Update node position
        node1.position_x = 150
        node1.position_y = 250
        node1.save()

        node1.refresh_from_db()
        assert node1.position_x == 150
        assert node1.position_y == 250 