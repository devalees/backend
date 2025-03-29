from rest_framework import serializers
from .models import Contact, ContactGroup
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