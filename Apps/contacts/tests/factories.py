from factory import (
    Sequence, LazyAttribute, SubFactory, RelatedFactoryList, Faker,
    post_generation
)
from Apps.contacts.models import Contact, ContactGroup
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