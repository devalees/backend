from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg, Max, Min

from .models import Document, DocumentVersion, DocumentClassification, DocumentTag
from .serializers import (
    DocumentSerializer, 
    DocumentVersionSerializer, 
    DocumentClassificationSerializer, 
    DocumentTagSerializer,
    DocumentFilterResultSerializer,
    DocumentVersionFilterResultSerializer,
    ClassificationFilterResultSerializer,
    TagFilterResultSerializer,
    AggregationResultSerializer
)

class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Document model with filtering and aggregation support.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def filter(self, request):
        """
        Apply filters to the Document model.
        
        Example payload:
        {
            "title": "Report",
            "status": "approved",
            "is_deleted": false
        }
        """
        filters = request.data
        filtered_docs = Document.filter(filters)
        
        # Convert QuerySet to list of dicts for the response
        result = []
        for doc in filtered_docs:
            result.append({
                'id': doc.id,
                'title': doc.title,
                'status': doc.status,
                'created_at': doc.created_at,
                'updated_at': doc.updated_at,
                'user': doc.user.username if doc.user else None,
                'classification': doc.classification.name if doc.classification else None,
            })
        
        # Use serializer to validate/format the results
        serializer = DocumentFilterResultSerializer(data=result, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def aggregate(self, request):
        """
        Apply aggregations to the Document model.
        
        Example payload:
        {
            "aggregations": {
                "id": "count"
            },
            "group_by": ["status"]
        }
        """
        data = request.data
        aggregations = data.get('aggregations', {})
        group_by = data.get('group_by', [])
        
        # Handle both formats: {'count': ['id']} and {'id': 'count'}
        normalized_aggregations = {}
        for key, value in aggregations.items():
            if isinstance(value, list):
                # Format: {'count': ['id']} -> {'id': 'count'}
                for field in value:
                    normalized_aggregations[field] = key
            else:
                # Format: {'id': 'count'} (already correct)
                normalized_aggregations[key] = value
        
        result = Document.aggregate(normalized_aggregations, group_by)
        
        # Use serializer to format the result
        serializer = AggregationResultSerializer(data={'results': result})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def status_counts(self, request):
        """
        Get document counts by status.
        """
        aggregations = {'id': 'count'}
        group_by = ['status']
        
        result = Document.aggregate(aggregations, group_by)
        
        # Use serializer to format the result
        serializer = AggregationResultSerializer(data={'results': result})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_documents(self, request):
        """
        Get documents for the current user.
        """
        filters = {'user': request.user}
        user_docs = Document.filter(filters)
        
        # Convert QuerySet to list of dicts for the response
        result = []
        for doc in user_docs:
            result.append({
                'id': doc.id,
                'title': doc.title,
                'status': doc.status,
                'created_at': doc.created_at,
                'updated_at': doc.updated_at,
                'classification': doc.classification.name if doc.classification else None,
            })
        
        # Use serializer to validate/format the results
        serializer = DocumentFilterResultSerializer(data=result, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

class DocumentVersionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DocumentVersion model with filtering and aggregation support.
    """
    queryset = DocumentVersion.objects.all()
    serializer_class = DocumentVersionSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def filter(self, request):
        """
        Apply filters to the DocumentVersion model.
        
        Example payload:
        {
            "document": 1,
            "is_current": true,
            "branch_name": "main"
        }
        """
        filters = request.data
        filtered_versions = DocumentVersion.filter(filters)
        
        # Convert QuerySet to list of dicts for the response
        result = []
        for version in filtered_versions:
            result.append({
                'id': version.id,
                'document': version.document.id,
                'document_title': version.document.title,
                'version_number': version.version_number,
                'created_at': version.created_at,
                'user': version.user.username if version.user else None,
                'is_current': version.is_current,
                'branch_name': version.branch_name,
            })
        
        # Use serializer to validate/format the results
        serializer = DocumentVersionFilterResultSerializer(data=result, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def aggregate(self, request):
        """
        Apply aggregations to the DocumentVersion model.
        
        Example payload:
        {
            "aggregations": {
                "version_number": "max"
            },
            "group_by": ["document", "branch_name"]
        }
        """
        data = request.data
        aggregations = data.get('aggregations', {})
        group_by = data.get('group_by', [])
        
        # Handle both formats: {'max': ['version_number']} and {'version_number': 'max'}
        normalized_aggregations = {}
        for key, value in aggregations.items():
            if isinstance(value, list):
                # Format: {'max': ['version_number']} -> {'version_number': 'max'}
                for field in value:
                    normalized_aggregations[field] = key
            else:
                # Format: {'version_number': 'max'} (already correct)
                normalized_aggregations[key] = value
        
        result = DocumentVersion.aggregate(normalized_aggregations, group_by)
        
        # Use serializer to format the result
        serializer = AggregationResultSerializer(data={'results': result})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def version_counts(self, request):
        """
        Get version counts by document.
        """
        aggregations = {'id': 'count'}
        group_by = ['document']
        
        result = DocumentVersion.aggregate(aggregations, group_by)
        
        # Use serializer to format the result
        serializer = AggregationResultSerializer(data={'results': result})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

class DocumentClassificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DocumentClassification model with filtering and aggregation support.
    """
    queryset = DocumentClassification.objects.all()
    serializer_class = DocumentClassificationSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def filter(self, request):
        """
        Apply filters to the DocumentClassification model.
        
        Example payload:
        {
            "name": "Report"
        }
        """
        filters = request.data
        filtered_classifications = DocumentClassification.filter(filters)
        
        # Convert QuerySet to list of dicts for the response
        result = []
        for classification in filtered_classifications:
            result.append({
                'id': classification.id,
                'name': classification.name,
                'description': classification.description,
                'parent': classification.parent.id if classification.parent else None,
                'parent_name': classification.parent.name if classification.parent else None,
            })
        
        # Use serializer to validate/format the results
        serializer = ClassificationFilterResultSerializer(data=result, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def aggregate(self, request):
        """
        Apply aggregations to the DocumentClassification model.
        
        Example payload:
        {
            "aggregations": {
                "id": "count"
            },
            "group_by": ["parent"]
        }
        """
        data = request.data
        aggregations = data.get('aggregations', {})
        group_by = data.get('group_by', [])
        
        # Handle both formats: {'count': ['id']} and {'id': 'count'}
        normalized_aggregations = {}
        for key, value in aggregations.items():
            if isinstance(value, list):
                # Format: {'count': ['id']} -> {'id': 'count'}
                for field in value:
                    normalized_aggregations[field] = key
            else:
                # Format: {'id': 'count'} (already correct)
                normalized_aggregations[key] = value
        
        result = DocumentClassification.aggregate(normalized_aggregations, group_by)
        
        # Use serializer to format the result
        serializer = AggregationResultSerializer(data={'results': result})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

class DocumentTagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DocumentTag model with filtering and aggregation support.
    """
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def filter(self, request):
        """
        Apply filters to the DocumentTag model.
        
        Example payload:
        {
            "name": "Important"
        }
        """
        filters = request.data
        filtered_tags = DocumentTag.filter(filters)
        
        # Convert QuerySet to list of dicts for the response
        result = []
        for tag in filtered_tags:
            result.append({
                'id': tag.id,
                'name': tag.name,
                'description': tag.description,
                'color': tag.color,
            })
        
        # Use serializer to validate/format the results
        serializer = TagFilterResultSerializer(data=result, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def aggregate(self, request):
        """
        Apply aggregations to the DocumentTag model.
        
        Example payload:
        {
            "aggregations": {
                "id": "count"
            }
        }
        """
        data = request.data
        aggregations = data.get('aggregations', {})
        group_by = data.get('group_by', [])
        
        # Handle both formats: {'count': ['id']} and {'id': 'count'}
        normalized_aggregations = {}
        for key, value in aggregations.items():
            if isinstance(value, list):
                # Format: {'count': ['id']} -> {'id': 'count'}
                for field in value:
                    normalized_aggregations[field] = key
            else:
                # Format: {'id': 'count'} (already correct)
                normalized_aggregations[key] = value
        
        result = DocumentTag.aggregate(normalized_aggregations, group_by)
        
        # Use serializer to format the result
        serializer = AggregationResultSerializer(data={'results': result})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
