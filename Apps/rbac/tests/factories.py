import factory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from ..models import Role, RBACPermission as Permission, FieldPermission, RolePermission, UserRole
from ..models.test_models import TestDocument

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

    name = factory.Sequence(lambda n: f'Test Permission {n}')
    codename = factory.Sequence(lambda n: f'test_permission_{n}')
    content_type = factory.LazyAttribute(lambda _: ContentType.objects.get_for_model(User))
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

class FieldPermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FieldPermission

    content_type = factory.LazyAttribute(
        lambda _: ContentType.objects.get_for_model(User)
    )
    field_name = factory.Iterator(['username', 'email', 'first_name', 'last_name'])
    permission_type = factory.Iterator(['read', 'write'])
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

class RolePermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RolePermission
        django_get_or_create = ('role', 'permission', 'field_permission')

    role = factory.SubFactory(RoleFactory)
    permission = factory.SubFactory(PermissionFactory, required=False)
    field_permission = None  # Optional field permission
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

    @factory.post_generation
    def set_created_by(self, create, extracted, **kwargs):
        if not create:
            return
        if not self.created_by:
            self.created_by = self.role.created_by
            self.updated_by = self.role.created_by
            self.save()

class UserRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserRole

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

    @factory.post_generation
    def set_created_by(self, create, extracted, **kwargs):
        if not create:
            return
        if not self.created_by:
            self.created_by = self.user
            self.save()
