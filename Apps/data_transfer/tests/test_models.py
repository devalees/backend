import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from Apps.data_transfer.models import DataTransfer, DataTransferItem
from Apps.data_transfer.tests.factories import DataTransferFactory, DataTransferItemFactory
from Apps.entity.tests.factories import OrganizationFactory
from Apps.contacts.tests.factories import ContactFactory

@pytest.mark.django_db
class TestDataTransfer:
    def test_create_data_transfer(self):
        """Test creating a data transfer"""
        transfer = DataTransferFactory()
        assert transfer.pk is not None
        assert transfer.name is not None
        assert transfer.source_organization is not None
        assert transfer.destination_organization is not None
        assert transfer.status == DataTransfer.Status.DRAFT

    def test_data_transfer_str(self):
        """Test string representation of data transfer"""
        transfer = DataTransferFactory(name="Test Transfer")
        assert str(transfer) == f"Test Transfer ({transfer.get_status_display()})"

    def test_data_transfer_soft_delete(self):
        """Test soft delete functionality"""
        transfer = DataTransferFactory()
        transfer_id = transfer.id
        transfer.delete()
        
        # Check that the object is not in the default queryset
        assert not DataTransfer.objects.filter(id=transfer_id).exists()
        
        # Check that the object still exists in all_objects
        assert DataTransfer.all_objects.filter(id=transfer_id).exists()

    def test_data_transfer_hard_delete(self):
        """Test hard delete functionality"""
        transfer = DataTransferFactory()
        transfer_id = transfer.id
        transfer.hard_delete()
        assert not DataTransfer.objects.filter(id=transfer_id).exists()

    def test_same_organization_validation(self):
        """Test that source and destination organizations cannot be the same"""
        org = OrganizationFactory()
        with pytest.raises(ValidationError):
            DataTransferFactory(
                source_organization=org,
                destination_organization=org
            )

    def test_status_transitions(self):
        """Test valid status transitions"""
        data_transfer = DataTransferFactory(status=DataTransfer.Status.DRAFT)
        
        # Test invalid transition from DRAFT to COMPLETED
        with pytest.raises(ValidationError):
            data_transfer.status = DataTransfer.Status.COMPLETED
            data_transfer.full_clean()

        # Test valid transition from DRAFT to IN_PROGRESS
        data_transfer.status = DataTransfer.Status.IN_PROGRESS
        data_transfer.full_clean()
        data_transfer.save()

        # Test valid transition from IN_PROGRESS to COMPLETED
        data_transfer.status = DataTransfer.Status.COMPLETED
        data_transfer.full_clean()
        data_transfer.save()

        # Test invalid transition from COMPLETED to IN_PROGRESS
        with pytest.raises(ValidationError):
            data_transfer.status = DataTransfer.Status.IN_PROGRESS
            data_transfer.full_clean()

@pytest.mark.django_db
class TestDataTransferItem:
    def test_create_data_transfer_item(self):
        """Test creating a data transfer item"""
        data_transfer = DataTransferFactory()
        contact = ContactFactory(organization=data_transfer.source_organization)
        item = DataTransferItemFactory(
            data_transfer=data_transfer,
            contact=contact
        )
        assert item.pk is not None
        assert item.data_transfer == data_transfer
        assert item.contact == contact
        assert item.status == DataTransfer.Status.DRAFT

    def test_contact_organization_validation(self):
        """Test that contact must belong to source organization"""
        data_transfer = DataTransferFactory()
        contact = ContactFactory()  # Different organization
        with pytest.raises(ValidationError):
            DataTransferItemFactory(
                data_transfer=data_transfer,
                contact=contact
            ) 