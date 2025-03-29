import factory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from ..models import Role, Permission, FieldPermission, RolePermission, UserRole

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    is_active = True

class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'role{n}')
    description = factory.Faker('text')
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

class PermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Permission
        django_get_or_create = ('codename',)

    name = factory.Sequence(lambda n: f'permission{n}')
    codename = factory.Sequence(lambda n: f'permission_{n}')
    description = factory.Faker('text')
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

class FieldPermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FieldPermission
        django_get_or_create = ('content_type', 'field_name', 'permission_type')

    content_type = factory.SubFactory(
        factory.django.DjangoModelFactory,
        model=ContentType,
        app_label='rbac',
        model='testmodel'
    )
    field_name = factory.Sequence(lambda n: f'field{n}')
    permission_type = factory.Iterator(['read', 'write', 'create', 'delete'])
    created_by = factory.SubFactory(UserFactory)

class RolePermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RolePermission
        django_get_or_create = ('role', 'permission', 'field_permission')

    role = factory.SubFactory(RoleFactory)
    permission = factory.SubFactory(PermissionFactory)
    field_permission = None  # Optional field permission
    created_by = factory.SubFactory(UserFactory)

class UserRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserRole
        django_get_or_create = ('user', 'role')

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)
    created_by = factory.SubFactory(UserFactory)
