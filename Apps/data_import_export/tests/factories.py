import factory
import random
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from ..models import ImportExportConfig, ImportExportLog, TestModel, NonImportExportModel
from factory.django import DjangoModelFactory
from faker import Faker

User = get_user_model()
faker = Faker()


class ContentTypeFactory(DjangoModelFactory):
    class Meta:
        model = ContentType
        django_get_or_create = ('app_label', 'model')

    app_label = factory.Sequence(lambda n: f'app_{n}')
    model = factory.Sequence(lambda n: f'model_{n}')


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""
    class Meta:
        model = User
        django_get_or_create = ('username',)
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True


class TestModelFactory(DjangoModelFactory):
    class Meta:
        model = TestModel
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'Test Model {n}')
    created_by = factory.SubFactory(UserFactory)


class NonImportExportModelFactory(DjangoModelFactory):
    class Meta:
        model = NonImportExportModel
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'Non Import Export Model {n}')
    created_by = factory.SubFactory(UserFactory)


class ImportExportConfigFactory(DjangoModelFactory):
    """Factory for ImportExportConfig model."""
    class Meta:
        model = ImportExportConfig
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'Config {n}')
    description = factory.LazyFunction(lambda: faker.text())
    content_type = factory.LazyFunction(lambda: ContentType.objects.get_for_model(TestModel))
    field_mapping = {'name': 'name', 'description': 'description'}
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute('created_by')


class ImportExportLogFactory(DjangoModelFactory):
    """Factory for ImportExportLog model."""
    class Meta:
        model = ImportExportLog
        skip_postgeneration_save = True

    config = factory.SubFactory(ImportExportConfigFactory)
    operation = factory.Iterator([ImportExportLog.OPERATION_IMPORT, ImportExportLog.OPERATION_EXPORT])
    status = factory.Iterator([
        ImportExportLog.STATUS_IN_PROGRESS,
        ImportExportLog.STATUS_COMPLETED,
        ImportExportLog.STATUS_FAILED
    ])
    file_name = factory.Sequence(lambda n: f'test_file_{n}.csv')
    error_message = factory.LazyFunction(lambda: faker.text() if random.choice([True, False]) else '')
    
    @factory.lazy_attribute
    def records_processed(self):
        return random.randint(10, 1000)
    
    @factory.lazy_attribute
    def records_failed(self):
        return random.randint(0, self.records_processed // 2)
    
    @factory.lazy_attribute
    def records_succeeded(self):
        return random.randint(0, self.records_processed - self.records_failed)
        
    performed_by = factory.SubFactory(UserFactory)

    @factory.post_generation
    def validate(self, create, extracted, **kwargs):
        if not create:
            return
        self.full_clean() 