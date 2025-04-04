from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Node, Connection, WorkflowTemplate, Workflow

class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = [
            'id', 'name', 'workflow', 'node_type', 'configuration',
            'position_x', 'position_y', 'is_active', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate(self, data):
        # For partial updates, only validate fields that are present
        if self.partial:
            # If only position fields are being updated, skip other validations
            position_fields = {'position_x', 'position_y'}
            update_fields = set(data.keys())
            if update_fields.issubset(position_fields):
                # Validate position values if provided
                position_x = data.get('position_x')
                position_y = data.get('position_y')
                if position_x is not None and not isinstance(position_x, (int, float)):
                    raise ValidationError("position_x must be a number")
                if position_y is not None and not isinstance(position_y, (int, float)):
                    raise ValidationError("position_y must be a number")
                return data

        # Validate configuration if present
        if 'configuration' in data:
            configuration = data['configuration']
            if not isinstance(configuration, dict):
                raise ValidationError("Configuration must be a JSON object")

        # Validate workflow ownership if workflow is being updated
        request = self.context.get('request')
        if request and request.user:
            workflow = data.get('workflow')
            if workflow and workflow.created_by != request.user:
                raise ValidationError("You don't have permission to add nodes to this workflow")

        # Validate node type and configuration if either is present
        node_type = data.get('node_type')
        configuration = data.get('configuration', {})
        
        if node_type or not self.partial:  # Validate on create or if node_type is being updated
            if node_type == 'trigger':
                if not configuration.get('trigger_type'):
                    raise ValidationError("Trigger nodes must specify trigger_type")
            elif node_type == 'action':
                if not configuration.get('action_type'):
                    raise ValidationError("Action nodes must specify action_type")
            elif node_type is not None:  # Allow node_type to be missing in partial updates
                raise ValidationError("Invalid node type")

        # Validate position values if provided
        position_x = data.get('position_x')
        position_y = data.get('position_y')
        if position_x is not None and not isinstance(position_x, (int, float)):
            raise ValidationError("position_x must be a number")
        if position_y is not None and not isinstance(position_y, (int, float)):
            raise ValidationError("position_y must be a number")

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # For partial updates, only validate workflow ownership if workflow is being changed
        request = self.context.get('request')
        if request and request.user:
            workflow = validated_data.get('workflow', instance.workflow)
            if workflow and workflow.created_by != request.user:
                raise ValidationError("You don't have permission to modify this node")
        return super().update(instance, validated_data)

class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = ['id', 'name', 'workflow', 'source_node', 'target_node', 'configuration', 'created_by']
        read_only_fields = ['created_by']

    def validate(self, data):
        # Validate configuration is a JSON object
        configuration = data.get('configuration', {})
        if not isinstance(configuration, dict):
            raise ValidationError("Configuration must be a JSON object")

        # Get request user
        request = self.context.get('request')
        if not request or not request.user:
            raise ValidationError("Authentication required")

        # Validate workflow ownership
        workflow = data.get('workflow')
        if workflow and workflow.created_by != request.user:
            raise ValidationError("You don't have permission to add connections to this workflow")

        # Validate source and target nodes
        source_node = data.get('source_node')
        target_node = data.get('target_node')

        if source_node and target_node:
            # Check nodes belong to the same workflow
            if source_node.workflow_id != workflow.id or target_node.workflow_id != workflow.id:
                raise ValidationError("Source and target nodes must belong to the same workflow")

            # Check node ownership
            if source_node.workflow.created_by != request.user:
                raise ValidationError("You don't have permission to use this source node")
            if target_node.workflow.created_by != request.user:
                raise ValidationError("You don't have permission to use this target node")

            # Prevent self-connections
            if source_node == target_node:
                raise ValidationError("A node cannot connect to itself")

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class WorkflowTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTemplate
        fields = ['id', 'name', 'description', 'configuration', 'created_by']
        read_only_fields = ['created_by']

    def validate(self, data):
        # Validate configuration is a JSON object
        configuration = data.get('configuration', {})
        if not isinstance(configuration, dict):
            raise ValidationError("Configuration must be a JSON object")

        # Validate nodes
        nodes = configuration.get('nodes', [])
        if not nodes:
            raise ValidationError("Configuration must include at least one node")

        node_names = set()
        for node in nodes:
            if not isinstance(node, dict):
                raise ValidationError("Each node must be a dictionary")
            if 'type' not in node:
                raise ValidationError("Each node must have a type")
            if 'name' not in node:
                raise ValidationError("Each node must have a name")
            if 'config' not in node:
                raise ValidationError("Each node must have a configuration")

            # Track node names for connection validation
            node_names.add(node['name'])

            # Validate node type
            if node['type'] not in ['trigger', 'action']:
                raise ValidationError(f"Invalid node type: {node['type']}")

            # Validate node configuration based on type
            config = node['config']
            if node['type'] == 'trigger':
                if 'trigger_type' not in config:
                    raise ValidationError("Trigger nodes must specify trigger_type")
            elif node['type'] == 'action':
                if 'action_type' not in config:
                    raise ValidationError("Action nodes must specify action_type")

        # Validate connections
        connections = configuration.get('connections', [])
        for connection in connections:
            if not isinstance(connection, dict):
                raise ValidationError("Each connection must be a dictionary")
            if 'from' not in connection:
                raise ValidationError("Each connection must have a 'from' field")
            if 'to' not in connection:
                raise ValidationError("Each connection must have a 'to' field")

            # Validate node references
            if connection['from'] not in node_names:
                raise ValidationError(f"Connection references non-existent source node: {connection['from']}")
            if connection['to'] not in node_names:
                raise ValidationError(f"Connection references non-existent target node: {connection['to']}")

            # Prevent self-connections
            if connection['from'] == connection['to']:
                raise ValidationError("A node cannot connect to itself")

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data) 