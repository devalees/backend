import factory
from django.contrib.auth import get_user_model
from Apps.entity.models import Organization, Department, Team, TeamMember
from Apps.users.tests.factories import UserFactory

class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f'Organization {n}')
    description = factory.Faker('text')
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute('created_by')

class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Department

    name = factory.Sequence(lambda n: f'Department {n}')
    description = factory.Faker('text')
    organization = factory.SubFactory(OrganizationFactory)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute('created_by')

class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f'Team {n}')
    description = factory.Faker('text')
    department = factory.SubFactory(DepartmentFactory)
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute('created_by')

class TeamMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamMember

    team = factory.SubFactory(TeamFactory)
    user = factory.SubFactory(UserFactory)
    role = 'Member'
    created_by = factory.SelfAttribute('user')
    updated_by = factory.SelfAttribute('user') 