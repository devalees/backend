from factory import Sequence, SubFactory, Faker, LazyAttribute
from Apps.data_transfer.models import DataTransfer, DataTransferItem
from Apps.core.tests.factories import UserFactory, BaseModelFactory
from Apps.entity.tests.factories import OrganizationFactory
from Apps.contacts.tests.factories import ContactFactory

class DataTransferFactory(BaseModelFactory):
    class Meta:
        model = DataTransfer

    name = Sequence(lambda n: f'Transfer {n}')
    description = Faker('text')
    source_organization = SubFactory(OrganizationFactory)
    destination_organization = SubFactory(OrganizationFactory)
    status = DataTransfer.Status.DRAFT

class DataTransferItemFactory(BaseModelFactory):
    class Meta:
        model = DataTransferItem

    data_transfer = SubFactory(DataTransferFactory)
    contact = LazyAttribute(lambda obj: ContactFactory(organization=obj.data_transfer.source_organization))
    status = DataTransfer.Status.DRAFT 