import factory
from factory import (
    Sequence, LazyAttribute, SubFactory, RelatedFactoryList, Faker,
    post_generation
)
from factory.declarations import Iterator
from Apps.contacts.models import Contact, ContactGroup, ContactTemplate, ContactMonitoring, ContactGroupTemplate, ContactGroupMonitoring
from Apps.core.tests.factories import UserFactory, BaseModelFactory
from Apps.entity.tests.factories import OrganizationFactory, DepartmentFactory, TeamFactory

class ContactFactory(BaseModelFactory):
    class Meta:
        model = Contact
        skip_postgeneration_save = True

    name = Sequence(lambda n: f'Contact {n}')
    email = LazyAttribute(lambda obj: f'contact{obj.name.lower().replace(" ", "")}@example.com')
    phone = Sequence(lambda n: f'+1555{str(n).zfill(7)}'[:20])
    organization = SubFactory(OrganizationFactory)

    @post_generation
    def department(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.department = extracted
        else:
            self.department = DepartmentFactory(organization=self.organization)

    @post_generation
    def team(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.team = extracted
        else:
            self.team = TeamFactory(department=self.department)

class ContactGroupFactory(BaseModelFactory):
    class Meta:
        model = ContactGroup
        skip_postgeneration_save = True

    name = Sequence(lambda n: f'Contact Group {n}')
    description = Faker('text')
    organization = SubFactory(OrganizationFactory)
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)
    contacts = RelatedFactoryList(ContactFactory, size=3)

    @post_generation
    def contacts(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for contact in extracted:
                self.contacts.add(contact)

class ContactTemplateFactory(BaseModelFactory):
    class Meta:
        model = 'contacts.ContactTemplate'
        skip_postgeneration_save = True

    name = Sequence(lambda n: f'Contact Template {n}')
    description = Faker('text')
    organization = SubFactory(OrganizationFactory)
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)
    fields = LazyAttribute(lambda _: {
        'name': {'required': True, 'type': 'text'},
        'email': {'required': True, 'type': 'email'},
        'phone': {'required': True, 'type': 'phone'},
        'department': {'required': False, 'type': 'select'},
        'team': {'required': False, 'type': 'select'}
    })

class ContactGroupTemplateFactory(BaseModelFactory):
    class Meta:
        model = 'contacts.ContactGroupTemplate'
        skip_postgeneration_save = True

    name = Sequence(lambda n: f'Group Template {n}')
    description = Faker('text')
    organization = SubFactory(OrganizationFactory)
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)
    fields = LazyAttribute(lambda _: {
        'name': {'required': True, 'type': 'text'},
        'description': {'required': False, 'type': 'textarea'},
        'contacts': {'required': False, 'type': 'multiselect'}
    })
    version = 1

class ContactMonitoringFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'contacts.ContactMonitoring'

    contact = factory.SubFactory(ContactFactory)
    user = factory.SubFactory('Apps.core.tests.factories.UserFactory')
    activity_type = 'view'
    description = factory.LazyAttribute(lambda o: f"{o.activity_type.title()} of {o.contact.name}")
    ip_address = '192.168.1.1'
    user_agent = 'Test Browser'
    metadata = factory.LazyFunction(lambda: {})
    organization = factory.LazyAttribute(lambda o: o.contact.organization)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'contact' in kwargs:
            kwargs['organization'] = kwargs['contact'].organization
        return super()._create(model_class, *args, **kwargs)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'contact' in kwargs:
            kwargs['organization'] = kwargs['contact'].organization
        return super()._build(model_class, *args, **kwargs)

class ContactGroupMonitoringFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'contacts.ContactGroupMonitoring'

    group = factory.SubFactory(ContactGroupFactory)
    user = factory.SubFactory('Apps.core.tests.factories.UserFactory')
    activity_type = 'view'
    description = factory.LazyAttribute(lambda o: f"{o.activity_type.title()} of {o.group.name}")
    ip_address = '192.168.1.1'
    user_agent = 'Test Browser'
    metadata = factory.LazyFunction(lambda: {})
    organization = factory.LazyAttribute(lambda o: o.group.organization)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'group' in kwargs:
            kwargs['organization'] = kwargs['group'].organization
        return super()._create(model_class, *args, **kwargs)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'group' in kwargs:
            kwargs['organization'] = kwargs['group'].organization
        return super()._build(model_class, *args, **kwargs)