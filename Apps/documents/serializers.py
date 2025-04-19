from rest_framework import serializers
from .models import Document, DocumentVersion, DocumentClassification, DocumentTag

class DocumentTagSerializer(serializers.ModelSerializer):
    """
    Serializer for the DocumentTag model.
    """
    class Meta:
        model = DocumentTag
        fields = ['id', 'name', 'description', 'color', 'organization']
        read_only_fields = ['id', 'organization']

class DocumentClassificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the DocumentClassification model.
    """
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    
    class Meta:
        model = DocumentClassification
        fields = ['id', 'name', 'description', 'parent', 'parent_name', 'organization']
        read_only_fields = ['id', 'organization']

class DocumentVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for the DocumentVersion model.
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'document', 'document_title', 'version_number', 'file', 
            'user', 'user_name', 'comment', 'is_current', 'branch_name', 
            'parent_version', 'merged_to', 'created_at', 'updated_at', 'organization'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'organization']

class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Document model.
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    classification_name = serializers.CharField(source='classification.name', read_only=True, allow_null=True)
    tags = DocumentTagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'status', 'file', 'user', 'user_name',
            'classification', 'classification_name', 'tags', 'is_deleted',
            'created_at', 'updated_at', 'organization'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'organization']

class DocumentFilterResultSerializer(serializers.Serializer):
    """
    Serializer for the results of document filtering.
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    user = serializers.CharField(allow_null=True)
    classification = serializers.CharField(allow_null=True)

class DocumentVersionFilterResultSerializer(serializers.Serializer):
    """
    Serializer for the results of document version filtering.
    """
    id = serializers.IntegerField()
    document = serializers.IntegerField()
    document_title = serializers.CharField()
    version_number = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    user = serializers.CharField(allow_null=True)
    is_current = serializers.BooleanField()
    branch_name = serializers.CharField()

class ClassificationFilterResultSerializer(serializers.Serializer):
    """
    Serializer for the results of document classification filtering.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    parent = serializers.IntegerField(allow_null=True)
    parent_name = serializers.CharField(allow_null=True)

class TagFilterResultSerializer(serializers.Serializer):
    """
    Serializer for the results of document tag filtering.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    color = serializers.CharField()

class AggregationResultSerializer(serializers.Serializer):
    """
    Serializer for aggregation results.
    """
    # This is a generic serializer for aggregation results
    # Since the structure depends on the aggregation and grouping,
    # we'll use a JSONField to represent the data
    results = serializers.JSONField() 