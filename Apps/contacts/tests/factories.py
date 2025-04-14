import factory
from factory import (
    Sequence, LazyAttribute, SubFactory, RelatedFactoryList, Faker,
    post_generation
)
from factory.declarations import Iterator
from Apps.contacts.models import Contact, ContactGroup, ContactTemplate, ContactMonitoring, ContactGroupTemplate, ContactGroupMonitoring, ContactList, ContactSegment, ContactNote, ContactNoteMonitoring, ContactNoteNotification
from Apps.core.tests.factories import UserFactory, BaseModelFactory
from Apps.entity.tests.factories import OrganizationFactory, DepartmentFactory, TeamFactory
from django.utils import timezone
from datetime import timedelta

class ContactFactory(BaseModelFactory):
    class Meta:
        model = Contact
        skip_postgeneration_save = True

    name = Sequence(lambda n: f'Contact {n}')
    email = Sequence(lambda n: f'contact{n}@example.com')
    phone = Sequence(lambda n: f'+1{str(n).zfill(10)}')
    organization = SubFactory(OrganizationFactory)
    first_name = Faker('first_name')
    is_active = True

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

    @post_generation
    def contact_list(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            extracted.contacts.add(self)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to ensure validation runs"""
        instance = super()._create(model_class, *args, **kwargs)
        instance.full_clean()
        return instance

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

class CommunicationFactory(BaseModelFactory):
    class Meta:
        model = 'contacts.Communication'
        skip_postgeneration_save = True
        
    subject = Sequence(lambda n: f'Communication Subject {n}')
    message = Faker('text')
    contact = SubFactory(ContactFactory)
    organization = LazyAttribute(lambda o: o.contact.organization)
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)
    communication_type = 'email'
    status = 'draft'
    scheduled_at = None
    
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

class CommunicationMonitoringFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'contacts.CommunicationMonitoring'
        
    communication = factory.SubFactory(CommunicationFactory)
    user = factory.SubFactory('Apps.core.tests.factories.UserFactory')
    activity_type = 'view'
    description = factory.LazyAttribute(lambda o: f"{o.activity_type.title()} of {o.communication.subject}")
    ip_address = '192.168.1.1'
    user_agent = 'Test Browser'
    metadata = factory.LazyFunction(lambda: {})
    organization = factory.LazyAttribute(lambda o: o.communication.organization)
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'communication' in kwargs:
            kwargs['organization'] = kwargs['communication'].organization
        return super()._create(model_class, *args, **kwargs)
        
    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'communication' in kwargs:
            kwargs['organization'] = kwargs['communication'].organization
        return super()._build(model_class, *args, **kwargs)

class ContactListFactory(factory.django.DjangoModelFactory):
    """Factory for ContactList model"""
    
    class Meta:
        model = 'contacts.ContactList'
        
    name = factory.Sequence(lambda n: f'Contact List {n}')
    description = factory.Faker('paragraph')
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SelfAttribute('organization.created_by')
    updated_by = factory.SelfAttribute('organization.created_by')
    is_active = True
    metadata = {}
    
    @factory.post_generation
    def contacts(self, create, extracted, **kwargs):
        if not create:
            return
            
        if extracted:
            for contact in extracted:
                self.contacts.add(contact)
        else:
            # Create 3 contacts by default
            for _ in range(3):
                contact = ContactFactory(organization=self.organization)
                self.contacts.add(contact)

class ContactListTemplateFactory(BaseModelFactory):
    """Factory for ContactListTemplate model"""
    
    class Meta:
        model = 'contacts.ContactListTemplate'
        skip_postgeneration_save = True
        
    name = Sequence(lambda n: f'Contact List Template {n}')
    description = Faker('text')
    organization = SubFactory(OrganizationFactory)
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)
    fields = LazyAttribute(lambda _: {
        'name': {'required': True, 'type': 'text'},
        'description': {'required': False, 'type': 'textarea'},
        'contacts': {'required': False, 'type': 'multiselect'}
    })
    is_active = True
    version = 1
    parent = None
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to ensure validation runs"""
        instance = super()._create(model_class, *args, **kwargs)
        instance.clean()
        instance.save()
        return instance

class ContactSegmentFactory(BaseModelFactory):
    class Meta:
        model = ContactSegment
        skip_postgeneration_save = True

    name = Sequence(lambda n: f'Contact Segment {n}')
    description = Faker('text')
    contact_list = SubFactory(ContactListFactory)
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)
    is_active = True
    filter_criteria = LazyAttribute(lambda _: {
        "field": "email",
        "operator": "contains",
        "value": "example.com"
    })
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create(*args, **kwargs)

class ContactMetricsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'contacts.ContactMetrics'

    contact = factory.SubFactory(ContactFactory)
    organization = factory.LazyAttribute(lambda o: o.contact.organization)
    engagement_score = factory.Faker('pyfloat', min_value=0, max_value=100)
    last_interaction = factory.LazyFunction(timezone.now)
    total_interactions = factory.Faker('random_int', min=0, max=1000)
    email_opens = factory.Faker('random_int', min=0, max=500)
    email_clicks = factory.Faker('random_int', min=0, max=200)
    response_rate = factory.Faker('pyfloat', min_value=0, max_value=100)
    average_response_time = factory.LazyFunction(lambda: timedelta(hours=factory.Faker('random_int', min=1, max=48)))
    communication_frequency = factory.Faker('pyfloat', min_value=0, max_value=30)

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

class ContactNoteFactory(BaseModelFactory):
    class Meta:
        model = ContactNote
        skip_postgeneration_save = True

    contact = SubFactory(ContactFactory)
    organization = LazyAttribute(lambda o: o.contact.organization)
    content = Faker('paragraph')
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)
    is_private = False
    is_active = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'contact' in kwargs:
            kwargs['organization'] = kwargs['contact'].organization
        instance = super()._create(model_class, *args, **kwargs)
        instance.clean()
        return instance
    
    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'contact' in kwargs:
            kwargs['organization'] = kwargs['contact'].organization
        return super()._build(model_class, *args, **kwargs)

class ContactNoteMonitoringFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContactNoteMonitoring

    note = factory.SubFactory(ContactNoteFactory)
    user = factory.SubFactory('Apps.core.tests.factories.UserFactory')
    activity_type = 'view'
    description = factory.LazyAttribute(lambda o: f"{o.activity_type.title()} of note for {o.note.contact.name}")
    ip_address = '192.168.1.1'
    user_agent = 'Test Browser'
    metadata = factory.LazyFunction(lambda: {})
    organization = factory.LazyAttribute(lambda o: o.note.organization)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'note' in kwargs:
            kwargs['organization'] = kwargs['note'].organization
        return super()._create(model_class, *args, **kwargs)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'note' in kwargs:
            kwargs['organization'] = kwargs['note'].organization
        return super()._build(model_class, *args, **kwargs)

class ContactNoteNotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContactNoteNotification

    note = factory.SubFactory(ContactNoteFactory)
    user = factory.SubFactory('Apps.core.tests.factories.UserFactory')
    organization = factory.LazyAttribute(lambda o: o.note.organization)
    is_read = False
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'note' in kwargs:
            kwargs['organization'] = kwargs['note'].organization
        return super()._create(model_class, *args, **kwargs)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        if 'organization' not in kwargs and 'note' in kwargs:
            kwargs['organization'] = kwargs['note'].organization
        return super()._build(model_class, *args, **kwargs)