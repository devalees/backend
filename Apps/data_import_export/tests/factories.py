import factory
import random
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from ..models import ImportExportConfig, ImportExportLog

User = get_user_model()


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

    app_label = 'testapp'
    model = 'testmodel'


class ImportExportConfigFactory(factory.django.DjangoModelFactory):
    """Factory for ImportExportConfig model."""
    class Meta:
        model = ImportExportConfig

    name = factory.Sequence(lambda n: f'Config {n}')
    description = factory.Faker('text', max_nb_chars=200, locale='en_US')
    content_type = factory.SubFactory(ContentTypeFactory)
    field_mapping = factory.SubFactory(factory.DictFactory,
        source_field='target_field',
        name='name',
        email='email'
    )
    is_active = True
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute('created_by')


class ImportExportLogFactory(factory.django.DjangoModelFactory):
    """Factory for ImportExportLog model."""
    class Meta:
        model = ImportExportLog

    config = factory.SubFactory(ImportExportConfigFactory)
    operation = 'import'
    status = 'completed'
    file_name = factory.Sequence(lambda n: f'test_file_{n}.csv')
    records_processed = factory.LazyFunction(lambda: random.randint(0, 1000))
    records_succeeded = factory.LazyAttribute(
        lambda obj: random.randint(0, obj.records_processed)
    )
    records_failed = factory.LazyAttribute(
        lambda obj: obj.records_processed - obj.records_succeeded
    )
    error_message = factory.Maybe(
        'records_failed',
        factory.Faker('text', max_nb_chars=200, locale='en_US'),
        ''
    )
    performed_by = factory.SubFactory(UserFactory) 