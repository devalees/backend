from rest_framework import serializers
from .models import Contact, ContactGroup, ContactTemplate
from Apps.entity.serializers import OrganizationSerializer, DepartmentSerializer, TeamSerializer

class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = Contact
        fields = ('id', 'first_name', 'last_name', 'email', 'phone', 'organization', 'organization_name',
                 'department', 'department_name', 'team', 'team_name', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class ContactGroupSerializer(serializers.ModelSerializer):
    """Serializer for ContactGroup model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    contact_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = ContactGroup
        fields = ('id', 'name', 'description', 'organization', 'organization_name',
                 'contacts', 'contact_ids', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        contact_ids = validated_data.pop('contact_ids', [])
        group = super().create(validated_data)
        if contact_ids:
            group.contacts.set(contact_ids)
        return group

    def update(self, instance, validated_data):
        contact_ids = validated_data.pop('contact_ids', None)
        group = super().update(instance, validated_data)
        if contact_ids is not None:
            group.contacts.set(contact_ids)
        return group

class ContactTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ContactTemplate model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = ContactTemplate
        fields = (
            'id', 'name', 'description', 'organization', 'organization_name',
            'fields', 'is_active', 'created_at', 'updated_at',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_fields(self, value):
        """Validate the fields JSON structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Fields must be a dictionary.")
        
        valid_field_types = {'text', 'email', 'phone', 'select', 'number', 'date'}
        for field_name, field_config in value.items():
            if not isinstance(field_config, dict):
                raise serializers.ValidationError(
                    f"Field {field_name} configuration must be a dictionary."
                )
            
            if 'type' not in field_config:
                raise serializers.ValidationError(
                    f"Field {field_name} must have a type."
                )
            
            if field_config['type'] not in valid_field_types:
                raise serializers.ValidationError(
                    f"Invalid type for field {field_name}. Must be one of {valid_field_types}"
                )
            
            if 'required' not in field_config:
                raise serializers.ValidationError(
                    f"Field {field_name} must specify if it is required."
                )
            
            if not isinstance(field_config['required'], bool):
                raise serializers.ValidationError(
                    f"Required property for field {field_name} must be a boolean."
                )
        
        return value 