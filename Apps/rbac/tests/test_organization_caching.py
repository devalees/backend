import pytest
from django.core.cache import cache
from django.utils import timezone
from Apps.rbac.models import OrganizationContext
from Apps.entity.models import Organization, Department, Team, TeamMember
from django.contrib.auth import get_user_model
from django.db.models import Q

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
class TestOrganizationCaching:
    """Tests for organization caching functionality"""
    
    def test_organization_cache_key_generation(self, organization_context):
        """Test that organization cache keys are generated correctly"""
        cache_key = organization_context.get_organization_cache_key()
        expected_key = f"rbac_organization_context_{organization_context.id}_{organization_context.organization.id}"
        assert cache_key == expected_key
    
    def test_organization_cache_set(self, organization_context):
        """Test that organization data is cached correctly"""
        # Clear cache first
        cache.clear()
        
        # Set cache
        organization_context.cache_organization_data()
        
        # Check if cache was set
        cache_key = organization_context.get_organization_cache_key()
        cached_data = cache.get(cache_key)
        
        assert cached_data is not None
        assert cached_data['id'] == organization_context.organization.id
        assert cached_data['name'] == organization_context.organization.name
        assert cached_data['context_id'] == organization_context.id
        assert cached_data['context_name'] == organization_context.name
        assert cached_data['context_description'] == organization_context.description
    
    def test_organization_cache_get(self, organization_context):
        """Test that organization data is retrieved from cache correctly"""
        # Clear cache first
        cache.clear()
        
        # Set cache
        organization_context.cache_organization_data()
        
        # Get from cache
        cached_org = organization_context.get_cached_organization()
        
        assert cached_org is not None
        assert cached_org['id'] == organization_context.organization.id
        assert cached_org['name'] == organization_context.organization.name
        assert cached_org['context_id'] == organization_context.id
        assert cached_org['context_name'] == organization_context.name
    
    def test_organization_cache_invalidation(self, organization_context):
        """Test that organization cache is invalidated correctly"""
        # Clear cache first
        cache.clear()
        
        # Set cache
        organization_context.cache_organization_data()
        
        # Invalidate cache
        organization_context.invalidate_organization_cache()
        
        # Check if cache was invalidated
        cache_key = organization_context.get_organization_cache_key()
        cached_data = cache.get(cache_key)
        
        assert cached_data is None
    
    def test_organization_cache_update(self, organization_context):
        """Test that organization cache is updated when organization changes"""
        # Clear cache first
        cache.clear()
        
        # Set cache
        organization_context.cache_organization_data()
        
        # Update organization context
        organization_context.name = "Updated Context"
        organization_context.save()
        
        # Get from cache
        cached_org = organization_context.get_cached_organization()
        
        assert cached_org is not None
        assert cached_org['context_name'] == "Updated Context"
    
    def test_organization_cache_bulk_operations(self, organization):
        """Test caching with bulk operations"""
        # Clear cache first
        cache.clear()
        
        # Create multiple contexts
        contexts = []
        for i in range(5):
            context = OrganizationContext.objects.create(
                organization=organization,
                name=f"Context {i}",
                description=f"Test context {i}"
            )
            contexts.append(context)
        
        # Cache all contexts
        OrganizationContext.cache_organization_data_bulk(organization)
        
        # Check if all contexts were cached separately
        for context in contexts:
            cache_key = context.get_organization_cache_key()
            cached_data = cache.get(cache_key)
            assert cached_data is not None
            assert cached_data['context_id'] == context.id
            assert cached_data['context_name'] == context.name
    
    def test_organization_cache_performance(self, organization):
        """Test performance of organization caching"""
        # Clear cache first
        cache.clear()
        
        # Create multiple contexts with hierarchy
        contexts = []
        parent = None
        for i in range(5):
            context = OrganizationContext.objects.create(
                organization=organization,
                name=f"Context {i}",
                description=f"Test context {i}",
                parent=parent
            )
            contexts.append(context)
            parent = context
        
        # Measure time without cache
        start_time = timezone.now()
        for context in contexts:
            _ = context.organization
            _ = context.parent
            _ = context.children.all()
            _ = context.get_ancestors()
            _ = context.get_descendants()
        without_cache_time = (timezone.now() - start_time).total_seconds()
        
        # Cache all contexts
        OrganizationContext.cache_organization_data_bulk(organization)
        
        # Measure time with cache
        start_time = timezone.now()
        for context in contexts:
            _ = context.get_cached_organization()
        with_cache_time = (timezone.now() - start_time).total_seconds()
        
        # Cache should be significantly faster
        assert with_cache_time < without_cache_time
    
    def test_organization_cache_expiration(self, organization_context):
        """Test that organization cache expires correctly"""
        # Clear cache first
        cache.clear()
        
        # Set cache with short expiration
        organization_context.cache_organization_data(expiration=1)  # 1 second
        
        # Check if cache was set
        cache_key = organization_context.get_organization_cache_key()
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        
        # Wait for cache to expire
        import time
        time.sleep(1.1)
        
        # Check if cache expired
        cached_data = cache.get(cache_key)
        assert cached_data is None
    
    def test_organization_cache_hierarchy(self, organization, parent_organization_context, child_organization_context):
        """Test caching with organization hierarchy"""
        # Clear cache first
        cache.clear()
        
        # Cache parent context
        parent_organization_context.cache_organization_data()
        
        # Cache child context
        child_organization_context.cache_organization_data()
        
        # Check if both were cached
        parent_cache_key = parent_organization_context.get_organization_cache_key()
        child_cache_key = child_organization_context.get_organization_cache_key()
        
        parent_cached_data = cache.get(parent_cache_key)
        child_cached_data = cache.get(child_cache_key)
        
        assert parent_cached_data is not None
        assert child_cached_data is not None
        
        # Check if hierarchy information was cached
        assert 'children' in parent_cached_data
        assert len(parent_cached_data['children']) == 1
        assert parent_cached_data['children'][0]['context_id'] == child_organization_context.id
        
        assert 'parent' in child_cached_data
        assert child_cached_data['parent']['context_id'] == parent_organization_context.id 