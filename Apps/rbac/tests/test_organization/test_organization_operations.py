import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from Apps.rbac.models import OrganizationContext
from Apps.entity.models import Organization
from Apps.rbac.operations.organization import OrganizationOperations

@pytest.mark.django_db
class TestOrganizationOperations:
    """Test cases for organization operations"""

    def test_create_organization(self, organization_factory):
        """Test creating a new organization through operations"""
        org_data = {
            "name": "Test Operations Org",
            "description": "Test Description",
            "metadata": {"key": "value"}
        }
        
        org = OrganizationOperations.create_organization(**org_data)
        assert org.name == org_data["name"]
        assert org.description == org_data["description"]
        assert org.metadata == org_data["metadata"]
        assert org.is_active is True
        
        # Verify base organization was created
        entity_org = org.organization
        assert entity_org.name == org_data["name"]
        assert entity_org.description == org_data["description"]
        assert entity_org.status == Organization.Status.ACTIVE

    def test_create_child_organization(self, organization_factory):
        """Test creating a child organization"""
        # Create parent with base organization
        base_org = Organization.objects.create(name="Base Org")
        parent = organization_factory(organization=base_org)
        
        child_data = {
            "name": "Child Org",
            "description": "Child Description",
            "parent": parent
        }
        
        child = OrganizationOperations.create_organization(**child_data)
        assert child.parent == parent
        assert child in parent.get_all_children()
        assert child.organization == parent.organization
        
        # Test validation of parent organization
        different_base_org = Organization.objects.create(name="Different Base")
        different_parent = organization_factory(organization=different_base_org)
        
        # Test validation directly on the model
        with pytest.raises(ValidationError) as exc_info:
            child_org = OrganizationContext(
                name="Invalid Child",
                description="Invalid Description",
                parent=different_parent,
                organization=base_org  # Use parent's organization
            )
            child_org.full_clean()
            
        assert "Parent context must belong to the same organization" in str(exc_info.value)

    def test_update_organization(self, organization_factory):
        """Test updating organization details"""
        org = organization_factory()
        update_data = {
            "name": "Updated Name",
            "description": "Updated Description",
            "metadata": {"new": "value"}
        }
        
        updated_org = OrganizationOperations.update_organization(org.id, **update_data)
        assert updated_org.name == update_data["name"]
        assert updated_org.description == update_data["description"]
        assert updated_org.metadata == update_data["metadata"]
        
        # Verify base organization was updated
        entity_org = updated_org.organization
        assert entity_org.name == update_data["name"]
        assert entity_org.description == update_data["description"]

    def test_bulk_create_organizations(self, organization_factory):
        """Test creating multiple organizations at once"""
        orgs_data = [
            {"name": f"Bulk Org {i}", "description": f"Bulk Description {i}"}
            for i in range(3)
        ]
        
        orgs = OrganizationOperations.bulk_create_organizations(orgs_data)
        assert len(orgs) == 3
        for org, data in zip(orgs, orgs_data):
            assert org.name == data["name"]
            assert org.description == data["description"]
            assert org.organization.name == data["name"]

    def test_transfer_organization(self, organization_factory):
        """Test transferring organization to new parent"""
        # Create organizations with same base organization
        base_org = Organization.objects.create(name="Base Org")
        old_parent = organization_factory(organization=base_org)
        new_parent = organization_factory(organization=base_org)
        child = organization_factory(parent=old_parent, organization=base_org)
        
        transferred_org = OrganizationOperations.transfer_organization(
            child.id, new_parent.id
        )
        assert transferred_org.parent == new_parent
        assert transferred_org not in old_parent.get_all_children()
        assert transferred_org in new_parent.get_all_children()
        
        # Test transfer validation
        different_base_org = Organization.objects.create(name="Different Base")
        different_parent = organization_factory(organization=different_base_org)
        
        with pytest.raises(ValidationError) as exc_info:
            OrganizationOperations.transfer_organization(child.id, different_parent.id)
        assert "Cannot transfer organization to a parent in a different organization" in str(exc_info.value)

    def test_archive_organization(self, organization_factory):
        """Test archiving an organization"""
        base_org = Organization.objects.create(name="Base Org")
        org = organization_factory(organization=base_org)
        child = organization_factory(parent=org, organization=base_org)
        
        archived_org = OrganizationOperations.archive_organization(org.id)
        assert archived_org.is_active is False
        assert archived_org.deactivated_at is not None
        assert archived_org.organization.status == Organization.Status.INACTIVE
        
        # Check that child is also archived
        child.refresh_from_db()
        assert child.is_active is False

    def test_restore_organization(self, organization_factory):
        """Test restoring an archived organization"""
        base_org = Organization.objects.create(name="Base Org")
        org = organization_factory(
            organization=base_org,
            is_active=False,
            deactivated_at=timezone.now()
        )
        org.organization.status = Organization.Status.INACTIVE
        org.organization.save()
        
        restored_org = OrganizationOperations.restore_organization(org.id)
        assert restored_org.is_active is True
        assert restored_org.deactivated_at is None
        assert restored_org.organization.status == Organization.Status.ACTIVE

    def test_get_organization_hierarchy(self, organization_factory):
        """Test getting complete organization hierarchy"""
        base_org = Organization.objects.create(name="Base Org")
        root = organization_factory(organization=base_org)
        child1 = organization_factory(parent=root, organization=base_org)
        child2 = organization_factory(parent=root, organization=base_org)
        grandchild = organization_factory(parent=child1, organization=base_org)
        
        hierarchy = OrganizationOperations.get_organization_hierarchy(root.id)
        assert hierarchy["id"] == root.id
        assert len(hierarchy["children"]) == 2
        assert any(c["id"] == child1.id for c in hierarchy["children"])
        assert any(c["id"] == child2.id for c in hierarchy["children"])
        child1_in_hierarchy = next(c for c in hierarchy["children"] if c["id"] == child1.id)
        assert len(child1_in_hierarchy["children"]) == 1
        assert child1_in_hierarchy["children"][0]["id"] == grandchild.id

    def test_validate_organization_structure(self, organization_factory):
        """Test validating organization structure"""
        base_org = Organization.objects.create(name="Base Org")
        parent = organization_factory(organization=base_org)
        child = organization_factory(parent=parent, organization=base_org)
    
        # Should not raise any validation errors for valid structure
        OrganizationOperations.validate_organization_structure(child.id)
    
        # Create circular reference by making parent a child of child
        parent.parent = child
        with pytest.raises(ValidationError) as exc_info:
            parent.full_clean()  # This should raise ValidationError
        assert "Circular reference detected in organization context hierarchy" in str(exc_info.value)
        
        # Save the parent to persist the circular reference, skipping validation
        parent.save(skip_validation=True)
    
        # Test circular reference validation in validate_organization_structure
        with pytest.raises(ValidationError) as exc_info:
            OrganizationOperations.validate_organization_structure(parent.id)
        assert "Circular reference detected in organization structure" in str(exc_info.value)

    def test_merge_organizations(self, organization_factory):
        """Test merging two organizations"""
        base_org = Organization.objects.create(name="Base Org")
        org1 = organization_factory(organization=base_org)
        org2 = organization_factory(organization=base_org)
        child = organization_factory(parent=org2, organization=base_org)
        
        merged_org = OrganizationOperations.merge_organizations(
            source_org_id=org2.id,
            target_org_id=org1.id
        )
        
        # Check that children were transferred
        child.refresh_from_db()
        assert child.parent == org1
        # Check that source org is archived
        org2.refresh_from_db()
        assert org2.is_active is False
        
        # Test merge validation
        different_base_org = Organization.objects.create(name="Different Base")
        different_org = organization_factory(organization=different_base_org)
        
        with pytest.raises(ValidationError) as exc_info:
            OrganizationOperations.merge_organizations(
                source_org_id=different_org.id,
                target_org_id=org1.id
            )
        assert "Cannot merge organizations from different base organizations" in str(exc_info.value) 