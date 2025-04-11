import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from Apps.rbac.models import OrganizationContext
from Apps.entity.models import Organization as EntityOrganization

@pytest.mark.django_db
class TestOrganizationModel:
    """Test cases for the Organization model"""

    def test_organization_creation(self, organization_factory):
        """Test creating a new organization"""
        org = organization_factory()
        assert org.name is not None
        assert org.description is not None
        assert org.is_active is True
        assert org.created_at is not None
        assert org.updated_at is not None

    def test_organization_str_representation(self, organization_factory):
        """Test string representation of organization"""
        org = organization_factory(name="Test Org")
        assert str(org) == "Test Org (Test Entity Org)"

    def test_organization_unique_name_constraint(self, organization_factory):
        """Test that organization names must be unique within the same parent organization"""
        parent_org = organization_factory()
        org1 = organization_factory(name="Same Name", parent=parent_org)
        
        with pytest.raises(ValidationError):
            org2 = organization_factory(name="Same Name", parent=parent_org)
            org2.full_clean()

    def test_organization_hierarchy(self, organization_factory):
        """Test organization hierarchy functionality"""
        parent = organization_factory()
        child = organization_factory(parent=parent)
        
        assert child.parent == parent
        assert parent in child.get_all_parents()
        assert child in parent.get_all_children()

    def test_organization_deactivation(self, organization_factory):
        """Test organization deactivation"""
        org = organization_factory()
        org.deactivate()
        
        assert org.is_active is False
        assert org.deactivated_at is not None

    def test_organization_activation(self, organization_factory):
        """Test organization activation"""
        org = organization_factory(is_active=False, deactivated_at=timezone.now())
        org.activate()
        
        assert org.is_active is True
        assert org.deactivated_at is None

    def test_organization_metadata(self, organization_factory):
        """Test organization metadata handling"""
        metadata = {"key": "value", "number": 123}
        org = organization_factory(metadata=metadata)
        
        assert org.metadata == metadata
        assert org.metadata["key"] == "value"
        assert org.metadata["number"] == 123

    def test_organization_clean_validation(self, organization_factory):
        """Test organization validation during clean"""
        org = organization_factory()
        org.full_clean()  # Should not raise any validation errors

    def test_organization_cascade_delete(self, organization_factory):
        """Test that deleting an organization cascades to its organization contexts"""
        # Create an organization context
        org_context = organization_factory()
        org = org_context.organization
        
        # Delete the organization
        org.hard_delete()
        
        # Verify the organization context is also deleted
        with pytest.raises(OrganizationContext.DoesNotExist):
            OrganizationContext.objects.get(id=org_context.id)

    def test_organization_hard_delete(self, organization_factory):
        """Test hard delete functionality"""
        org = organization_factory()
        org_id = org.id
        org.hard_delete()
        
        with pytest.raises(OrganizationContext.DoesNotExist):
            OrganizationContext.objects.get(id=org_id)

    def test_organization_get_ancestors(self, organization_factory):
        """Test getting organization ancestors"""
        grandparent = organization_factory()
        parent = organization_factory(parent=grandparent)
        child = organization_factory(parent=parent)
        
        ancestors = child.get_ancestors()
        assert len(ancestors) == 2
        assert parent in ancestors
        assert grandparent in ancestors

    def test_organization_get_descendants(self, organization_factory):
        """Test getting organization descendants"""
        parent = organization_factory()
        child1 = organization_factory(parent=parent)
        child2 = organization_factory(parent=parent)
        grandchild = organization_factory(parent=child1)
        
        descendants = parent.get_descendants()
        assert len(descendants) == 3
        assert child1 in descendants
        assert child2 in descendants
        assert grandchild in descendants

    def test_organization_get_all_children(self, organization_factory):
        """Test getting all immediate children"""
        parent = organization_factory()
        child1 = organization_factory(parent=parent)
        child2 = organization_factory(parent=parent)
        
        children = parent.get_all_children()
        assert len(children) == 2
        assert child1 in children
        assert child2 in children

    def test_organization_get_all_parents(self, organization_factory):
        """Test getting all immediate parents"""
        grandparent = organization_factory()
        parent = organization_factory(parent=grandparent)
        child = organization_factory(parent=parent)
        
        parents = child.get_all_parents()
        assert len(parents) == 2
        assert parent in parents
        assert grandparent in parents 