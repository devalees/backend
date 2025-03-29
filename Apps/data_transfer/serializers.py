from rest_framework import serializers
from .models import DataTransfer, DataTransferItem
from Apps.entity.serializers import OrganizationSerializer
from Apps.contacts.serializers import ContactSerializer

class DataTransferItemSerializer(serializers.ModelSerializer):
    """Serializer for DataTransferItem model"""
    contact = ContactSerializer(read_only=True)
    contact_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = DataTransferItem
        fields = ('id', 'data_transfer', 'contact', 'contact_id', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class DataTransferSerializer(serializers.ModelSerializer):
    """Serializer for DataTransfer model"""
    source_organization_name = serializers.CharField(source='source_organization.name', read_only=True)
    destination_organization_name = serializers.CharField(source='destination_organization.name', read_only=True)
    items = DataTransferItemSerializer(many=True, read_only=True)
    item_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = DataTransfer
        fields = ('id', 'source_organization', 'source_organization_name',
                 'destination_organization', 'destination_organization_name',
                 'status', 'items', 'item_ids', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        item_ids = validated_data.pop('item_ids', [])
        transfer = super().create(validated_data)
        if item_ids:
            for contact_id in item_ids:
                DataTransferItem.objects.create(data_transfer=transfer, contact_id=contact_id)
        return transfer

    def update(self, instance, validated_data):
        item_ids = validated_data.pop('item_ids', None)
        transfer = super().update(instance, validated_data)
        if item_ids is not None:
            instance.items.all().delete()
            for contact_id in item_ids:
                DataTransferItem.objects.create(data_transfer=transfer, contact_id=contact_id)
        return transfer 