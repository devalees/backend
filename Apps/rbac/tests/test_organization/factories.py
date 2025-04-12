import factory
from django.utils import timezone
from Apps.rbac.models import OrganizationContext
from Apps.entity.models import Organization as EntityOrganization

class OrganizationFactory(factory.django.DjangoModelFactory):
    """Factory for creating Organization instances for testing"""
    
    class Meta:
        model = OrganizationContext
        django_get_or_create = ('name', 'organization')

    name = factory.Sequence(lambda n: f'Test Organization {n}')
    description = factory.Faker('text')
    organization = factory.LazyFunction(
        lambda: EntityOrganization.objects.first() or EntityOrganization.objects.create(name='Test Entity Org')
    )
    is_active = True
    metadata = factory.LazyFunction(lambda: {})
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to call full_clean() before saving"""
        obj = model_class(*args, **kwargs)
        obj.full_clean()
        obj.save()
        return obj 