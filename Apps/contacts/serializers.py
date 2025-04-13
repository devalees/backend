from rest_framework import serializers
from Apps.entity.serializers import OrganizationSerializer, DepartmentSerializer, TeamSerializer

class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        from .models import Contact
        model = Contact
        fields = ('id', 'name', 'email', 'phone', 'organization', 'organization_name',
                 'department', 'department_name', 'team', 'team_name', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class ContactGroupSerializer(serializers.ModelSerializer):
    """Serializer for ContactGroup model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    contact_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        from .models import ContactGroup
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
        from .models import ContactTemplate
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

class CommunicationSerializer(serializers.ModelSerializer):
    """Serializer for Communication model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        from .models import Communication
        model = Communication
        fields = (
            'id', 'subject', 'message', 'communication_type', 'status',
            'contact', 'contact_name', 'organization', 'organization_name',
            'created_at', 'updated_at', 'scheduled_at', 'sent_at',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'is_active', 'metadata'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'sent_at')
        
    def validate(self, data):
        """Validate the data"""
        # Check that contact belongs to organization if both are provided
        if 'contact' in data and 'organization' in data:
            if data['contact'].organization != data['organization']:
                raise serializers.ValidationError(
                    {'contact': 'Contact must belong to the specified organization.'}
                )
        
        # Validate communication_type
        if 'communication_type' in data:
            from .models import Communication
            valid_types = dict(Communication.COMMUNICATION_TYPES).keys()
            if data['communication_type'] not in valid_types:
                raise serializers.ValidationError(
                    {'communication_type': f'Invalid communication type. Must be one of {valid_types}'}
                )
                
        # Validate status
        if 'status' in data:
            from .models import Communication
            valid_statuses = dict(Communication.STATUS_TYPES).keys()
            if data['status'] not in valid_statuses:
                raise serializers.ValidationError(
                    {'status': f'Invalid status. Must be one of {valid_statuses}'}
                )
                
        # Validate scheduled communications
        if data.get('status') == 'scheduled' and not data.get('scheduled_at'):
            raise serializers.ValidationError(
                {'scheduled_at': 'Scheduled communications must have a scheduled date and time.'}
            )
            
        return data

class CommunicationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for CommunicationTemplate model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        from .models import CommunicationTemplate
        model = CommunicationTemplate
        fields = (
            'id', 'name', 'description', 'subject_template', 'message_template',
            'communication_type', 'organization', 'organization_name', 
            'created_at', 'updated_at', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name', 'is_active'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
        
    def validate(self, data):
        """Validate the data"""
        # Validate communication_type
        if 'communication_type' in data:
            from .models import Communication
            valid_types = dict(Communication.COMMUNICATION_TYPES).keys()
            if data['communication_type'] not in valid_types:
                raise serializers.ValidationError(
                    {'communication_type': f'Invalid communication type. Must be one of {valid_types}'}
                )
                
        return data
        
class CommunicationMonitoringSerializer(serializers.ModelSerializer):
    """Serializer for CommunicationMonitoring model"""
    communication_subject = serializers.CharField(source='communication.subject', read_only=True, allow_null=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    
    class Meta:
        from .models import CommunicationMonitoring
        model = CommunicationMonitoring
        fields = (
            'id', 'communication', 'communication_subject', 'user', 'user_name',
            'activity_type', 'description', 'organization', 'organization_name',
            'created_at', 'ip_address', 'user_agent', 'metadata'
        )
        read_only_fields = ('id', 'created_at') 

class ContactListSerializer(serializers.ModelSerializer):
    """Serializer for ContactList model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    contact_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        from .models import ContactList
        model = ContactList
        fields = (
            'id', 'name', 'description', 'organization', 'organization_name',
            'contacts', 'contact_ids', 'is_active', 'metadata',
            'created_at', 'updated_at', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
        
    def create(self, validated_data):
        """Create a contact list and add contacts if provided"""
        contact_ids = validated_data.pop('contact_ids', [])
        contact_list = super().create(validated_data)
        if contact_ids:
            contact_list.contacts.set(contact_ids)
        return contact_list
        
    def update(self, instance, validated_data):
        """Update a contact list and update contacts if provided"""
        contact_ids = validated_data.pop('contact_ids', None)
        contact_list = super().update(instance, validated_data)
        if contact_ids is not None:
            contact_list.contacts.set(contact_ids)
        return contact_list
        
    def validate(self, data):
        """Validate the data"""
        # Check that all contacts belong to the same organization if both are provided
        if 'contact_ids' in data and 'organization' in data:
            from .models import Contact
            
            contact_ids = data['contact_ids']
            organization = data['organization']
            
            # Find any contacts that don't belong to the organization
            invalid_contacts = Contact.objects.filter(
                id__in=contact_ids
            ).exclude(organization=organization)
            
            if invalid_contacts.exists():
                raise serializers.ValidationError(
                    {'contact_ids': 'All contacts must belong to the specified organization.'}
                )
        
        return data 