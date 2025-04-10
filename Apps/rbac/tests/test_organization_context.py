import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from Apps.rbac.models import OrganizationContext
from Apps.entity.models import Organization, Department, Team, TeamMember
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def organization_context(organization):
    """Create a test organization context"""
    return OrganizationContext.objects.create(
        organization=organization,
        name="Test Context",
        description="Test organization context"
    )

@pytest.fixture
def parent_organization_context(organization):
    """Create a parent organization context"""
    return OrganizationContext.objects.create(
        organization=organization,
        name="Parent Context",
        description="Parent organization context"
    )

@pytest.fixture
def child_organization_context(organization, parent_organization_context):
    """Create a child organization context"""
    return OrganizationContext.objects.create(
        organization=organization,
        name="Child Context",
        description="Child organization context",
        parent=parent_organization_context
    )

@pytest.mark.django_db
class TestOrganizationContext:
    """Tests for the OrganizationContext model"""
    
    def test_create_organization_context(self, organization):
        """Test creating a basic organization context"""
        context = OrganizationContext.objects.create(
            organization=organization,
            name="Test Context",
            description="Test organization context"
        )
        
        assert context.name == "Test Context"
        assert context.description == "Test organization context"
        assert context.organization == organization
        assert context.parent is None
        assert context.is_active is True
    
    def test_organization_context_str(self, organization_context):
        """Test the string representation of an organization context"""
        expected_str = f"{organization_context.name} ({organization_context.organization.name})"
        assert str(organization_context) == expected_str
    
    def test_organization_context_hierarchy(self, organization, parent_organization_context, child_organization_context):
        """Test organization context hierarchy"""
        assert child_organization_context.parent == parent_organization_context
        assert parent_organization_context.children.first() == child_organization_context
    
    def test_organization_context_validation(self, organization):
        """Test organization context validation"""
        # Test with empty name
        with pytest.raises(ValidationError):
            context = OrganizationContext(
                organization=organization,
                name="",
                description="Test organization context"
            )
            context.full_clean()
        
        # Test with duplicate name in the same organization
        OrganizationContext.objects.create(
            organization=organization,
            name="Duplicate Name",
            description="First context"
        )
        
        with pytest.raises(ValidationError):
            context = OrganizationContext(
                organization=organization,
                name="Duplicate Name",
                description="Second context"
            )
            context.full_clean()
    
    def test_organization_context_deactivation(self, organization_context):
        """Test deactivating an organization context"""
        organization_context.deactivate()
        assert organization_context.is_active is False
        assert organization_context.deactivated_at is not None
    
    def test_organization_context_activation(self, organization_context):
        """Test activating an organization context"""
        # First deactivate
        organization_context.deactivate()
        assert organization_context.is_active is False
        
        # Then activate
        organization_context.activate()
        assert organization_context.is_active is True
        assert organization_context.deactivated_at is None
    
    def test_organization_context_hard_delete(self, organization_context):
        """Test hard deleting an organization context"""
        context_id = organization_context.id
        organization_context.hard_delete()
        
        # Verify it's completely deleted from the database
        with pytest.raises(OrganizationContext.DoesNotExist):
            OrganizationContext.objects.get(id=context_id)
    
    def test_organization_context_soft_delete(self, organization_context):
        """Test soft deleting an organization context"""
        organization_context.delete()
        assert organization_context.is_active is False
        
        # Verify it still exists in the database
        assert OrganizationContext.objects.filter(id=organization_context.id).exists()
        
        # Verify it's not returned by the default manager
        assert not OrganizationContext.objects.filter(id=organization_context.id, is_active=True).exists()
    
    def test_organization_context_get_ancestors(self, organization, parent_organization_context, child_organization_context):
        """Test getting ancestors of an organization context"""
        ancestors = child_organization_context.get_ancestors()
        assert len(ancestors) == 1
        assert ancestors[0] == parent_organization_context
    
    def test_organization_context_get_descendants(self, organization, parent_organization_context, child_organization_context):
        """Test getting descendants of an organization context"""
        descendants = parent_organization_context.get_descendants()
        assert len(descendants) == 1
        assert descendants[0] == child_organization_context
    
    def test_organization_context_get_all_children(self, organization, parent_organization_context, child_organization_context):
        """Test getting all children of an organization context"""
        children = parent_organization_context.get_all_children()
        assert len(children) == 1
        assert children[0] == child_organization_context
    
    def test_organization_context_get_all_parents(self, organization, parent_organization_context, child_organization_context):
        """Test getting all parents of an organization context"""
        parents = child_organization_context.get_all_parents()
        assert len(parents) == 1
        assert parents[0] == parent_organization_context 