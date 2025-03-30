from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import ImportExportConfig, ImportExportLog
from rest_framework.validators import UniqueTogetherValidator


class ContentTypeSerializer(serializers.ModelSerializer):
    """Serializer for ContentType model."""
    class Meta:
        model = ContentType
        fields = ('id', 'app_label', 'model')


class ImportExportConfigSerializer(serializers.ModelSerializer):
    """Serializer for ImportExportConfig model."""
    content_type = ContentTypeSerializer(read_only=True)
    content_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all(),
        write_only=True,
        source='content_type',
        required=True
    )
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    field_mapping = serializers.JSONField(required=True)

    class Meta:
        model = ImportExportConfig
        fields = (
            'id', 'content_type', 'content_type_id', 'name', 'description', 'field_mapping',
            'is_active', 'created_by', 'updated_by', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
        validators = [
            UniqueTogetherValidator(
                queryset=ImportExportConfig.objects.all(),
                fields=('content_type', 'name'),
                message='A configuration with this name already exists for this content type.'
            )
        ]

    def validate_field_mapping(self, value):
        """Validate field_mapping."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Field mapping must be a dictionary.")
        if not value:
            raise serializers.ValidationError("Field mapping cannot be empty.")
        return value

    def create(self, validated_data):
        """Create a new ImportExportConfig instance."""
        if 'request' in self.context:
            validated_data['created_by'] = self.context['request'].user
            validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update an ImportExportConfig instance."""
        if 'request' in self.context:
            validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ImportExportLogSerializer(serializers.ModelSerializer):
    """Serializer for ImportExportLog model."""
    config = ImportExportConfigSerializer(read_only=True)
    config_id = serializers.PrimaryKeyRelatedField(
        queryset=ImportExportConfig.objects.all(),
        write_only=True,
        source='config',
        required=True
    )
    performed_by = serializers.StringRelatedField(read_only=True)
    operation_display = serializers.CharField(source='get_operation_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    records_processed = serializers.IntegerField(required=True, min_value=0)
    records_succeeded = serializers.IntegerField(required=True, min_value=0)
    records_failed = serializers.IntegerField(required=True, min_value=0)

    class Meta:
        model = ImportExportLog
        fields = (
            'id', 'config', 'config_id', 'operation', 'operation_display', 'status',
            'status_display', 'file_name', 'error_message', 'records_processed',
            'records_succeeded', 'records_failed', 'success_rate', 'performed_by',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'operation_display', 'status_display', 'success_rate', 'performed_by',
            'created_at', 'updated_at'
        )

    def validate(self, data):
        """Validate records count."""
        records_processed = data.get('records_processed', 0)
        records_succeeded = data.get('records_succeeded', 0)
        records_failed = data.get('records_failed', 0)

        if records_succeeded + records_failed != records_processed:
            raise serializers.ValidationError({
                'records_succeeded': 'Sum of succeeded and failed records must equal total processed.',
                'records_failed': 'Sum of succeeded and failed records must equal total processed.',
                'records_processed': 'Sum of succeeded and failed records must equal total processed.'
            })

        return data

    def create(self, validated_data):
        """Create a new ImportExportLog instance."""
        if 'request' in self.context:
            validated_data['performed_by'] = self.context['request'].user
        return super().create(validated_data)
