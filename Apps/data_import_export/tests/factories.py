import factory
import random
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from ..models import ImportExportConfig, ImportExportLog
from .models_for_testing import TestModel, NonImportExportModel
from factory.django import DjangoModelFactory
from faker import Faker

User = get_user_model()
faker = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted or 'testpass123'
        self.set_password(password)
        self.save()


class ContentTypeFactory(factory.django.DjangoModelFactory):
    """Factory for ContentType model."""
    class Meta:
        model = ContentType
        django_get_or_create = ('app_label', 'model')

    app_label = 'data_import_export'
    model = factory.Iterator(['testmodel', 'nonimportexportmodel'])


class ImportExportConfigFactory(DjangoModelFactory):
    """Factory for ImportExportConfig model."""
    class Meta:
        model = ImportExportConfig
        django_get_or_create = ('name',)
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f'Config {n}')
    content_type = factory.SubFactory(ContentTypeFactory)
    description = factory.Faker('sentence')
    field_mapping = factory.Dict({
        'field1': 'Field 1',
        'field2': 'Field 2'
    })


class ImportExportLogFactory(DjangoModelFactory):
    """Factory for ImportExportLog model."""
    class Meta:
        model = ImportExportLog
        django_get_or_create = ('config',)
        skip_postgeneration_save = True

    config = factory.SubFactory(ImportExportConfigFactory)
    performed_by = factory.SubFactory('Apps.users.tests.factories.UserFactory')
    operation = factory.Iterator(['import', 'export'])
    status = factory.Iterator(['in_progress', 'completed', 'failed'])
    records_succeeded = factory.Faker('random_int', min=0, max=500)
    records_failed = factory.Faker('random_int', min=0, max=500)
    records_processed = factory.LazyAttribute(lambda obj: obj.records_succeeded + obj.records_failed)
    error_message = factory.LazyAttribute(lambda obj: faker.sentence() if obj.status == 'failed' else None)
    file_name = factory.django.FileField(filename='test.csv', null=True)

    @factory.post_generation
    def validate(self, create, extracted, **kwargs):
        if not create:
            return
        self.full_clean() 