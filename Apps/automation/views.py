from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Node, Connection, WorkflowTemplate, Workflow
from .serializers import (
    NodeSerializer,
    ConnectionSerializer,
    WorkflowTemplateSerializer
)
from rest_framework.exceptions import ValidationError

class NodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflow nodes.
    """
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        workflow_id = self.request.data.get('workflow')
        workflow = get_object_or_404(Workflow, id=workflow_id)
        
        # Validate workflow ownership
        if workflow.created_by != self.request.user:
            raise ValidationError("You don't have permission to add nodes to this workflow")
            
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        # Validate node ownership through workflow
        instance = self.get_object()
        if instance.workflow.created_by != self.request.user:
            raise ValidationError("You don't have permission to modify this node")
        serializer.save()

    @action(detail=True, methods=['patch'])
    def position(self, request, pk=None):
        """Update node position"""
        node = self.get_object()
        
        # Validate node ownership through workflow
        if node.workflow.created_by != request.user:
            raise ValidationError("You don't have permission to modify this node")
            
        position_x = request.data.get('position_x')
        position_y = request.data.get('position_y')

        if position_x is not None:
            node.position_x = position_x
        if position_y is not None:
            node.position_y = position_y

        node.save()
        serializer = self.get_serializer(node)
        return Response(serializer.data)

class ConnectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflow connections.
    """
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        workflow_id = self.request.data.get('workflow')
        source_node_id = self.request.data.get('source_node')
        target_node_id = self.request.data.get('target_node')
        
        # Get workflow and validate ownership
        workflow = get_object_or_404(Workflow, id=workflow_id)
        if workflow.created_by != self.request.user:
            raise ValidationError("You don't have permission to add connections to this workflow")
            
        # Get nodes and validate they belong to the same workflow
        source_node = get_object_or_404(Node, id=source_node_id)
        target_node = get_object_or_404(Node, id=target_node_id)
        
        if source_node.workflow_id != workflow_id or target_node.workflow_id != workflow_id:
            raise ValidationError("Source and target nodes must belong to the same workflow")
            
        if source_node.workflow.created_by != self.request.user:
            raise ValidationError("You don't have permission to use this source node")
            
        if target_node.workflow.created_by != self.request.user:
            raise ValidationError("You don't have permission to use this target node")
            
        serializer.save(created_by=self.request.user)

class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflow templates.
    """
    queryset = WorkflowTemplate.objects.all()
    serializer_class = WorkflowTemplateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Validate configuration structure
        configuration = self.request.data.get('configuration', {})
        
        # Validate nodes
        nodes = configuration.get('nodes', [])
        if not nodes:
            raise ValidationError("Configuration must include at least one node")
            
        for node in nodes:
            if not isinstance(node, dict):
                raise ValidationError("Each node must be a dictionary")
            if 'type' not in node:
                raise ValidationError("Each node must have a type")
            if 'name' not in node:
                raise ValidationError("Each node must have a name")
            if 'config' not in node:
                raise ValidationError("Each node must have a configuration")
                
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
        node_names = {node['name'] for node in nodes}
        
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
        
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def instantiate(self, request, pk=None):
        """Create a new workflow from a template"""
        template = self.get_object()
        
        # Create the workflow
        workflow = Workflow.objects.create(
            name=request.data.get('name'),
            description=request.data.get('description', ''),
            created_by=request.user
        )

        # Create nodes
        node_mapping = {}  # Map template node names to actual node IDs
        for node_config in template.configuration['nodes']:
            node = Node.objects.create(
                name=node_config['name'],
                workflow=workflow,
                node_type=node_config['type'],
                configuration=node_config['config'],
                created_by=request.user
            )
            node_mapping[node_config['name']] = node

        # Create connections
        connections = []
        for conn_config in template.configuration.get('connections', []):
            connection = Connection.objects.create(
                workflow=workflow,
                source_node=node_mapping[conn_config['from']],
                target_node=node_mapping[conn_config['to']],
                configuration={'condition': 'always'},
                created_by=request.user
            )
            connections.append(connection)

        # Prepare response data
        response_data = {
            'id': workflow.id,
            'name': workflow.name,
            'description': workflow.description,
            'nodes': [
                {
                    'id': node.id,
                    'name': node.name,
                    'type': node.node_type,
                    'configuration': node.configuration
                }
                for node in node_mapping.values()
            ],
            'connections': [
                {
                    'id': conn.id,
                    'source_node': conn.source_node_id,
                    'target_node': conn.target_node_id,
                    'configuration': conn.configuration
                }
                for conn in connections
            ]
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workflows with visual design capabilities.
    """
    queryset = Workflow.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate workflow structure and configuration"""
        workflow = self.get_object()
        
        # Get all nodes and connections for the workflow
        nodes = Node.objects.filter(workflow=workflow)
        connections = Connection.objects.filter(workflow=workflow)

        # Validation rules
        validation_errors = []

        # 1. Check if workflow has at least one trigger node
        trigger_nodes = nodes.filter(node_type='trigger')
        if not trigger_nodes.exists():
            validation_errors.append("Workflow must have at least one trigger node")

        # 2. Check if workflow has at least one action node
        action_nodes = nodes.filter(node_type='action')
        if not action_nodes.exists():
            validation_errors.append("Workflow must have at least one action node")

        # 3. Check if all nodes are connected
        connected_nodes = set()
        for conn in connections:
            connected_nodes.add(conn.source_node_id)
            connected_nodes.add(conn.target_node_id)
        
        disconnected_nodes = nodes.exclude(id__in=connected_nodes)
        if disconnected_nodes.exists():
            validation_errors.append("All nodes must be connected")

        # 4. Check for cycles in the workflow
        def has_cycle(node, visited, path):
            visited.add(node.id)
            path.add(node.id)

            for conn in node.outgoing_connections.all():
                if conn.target_node_id not in visited:
                    if has_cycle(conn.target_node, visited, path):
                        return True
                elif conn.target_node_id in path:
                    return True

            path.remove(node.id)
            return False

        for trigger_node in trigger_nodes:
            visited = set()
            path = set()
            if has_cycle(trigger_node, visited, path):
                validation_errors.append("Workflow contains cycles")
                break

        # Return validation results
        is_valid = len(validation_errors) == 0
        return Response({
            'is_valid': is_valid,
            'errors': validation_errors
        }) 