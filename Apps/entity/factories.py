import factory
from django.contrib.auth import get_user_model
from factory import Faker
from factory.django import DjangoModelFactory

from Apps.entity.models import Organization, Department, Team, TeamMember

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Faker('user_name')
    email = Faker('email')
    password = factory.PostGenerationMethodCall('set_password', 'password123')

class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    name = Faker('company')
    description = Faker('text')
    status = Organization.Status.ACTIVE

class DepartmentFactory(DjangoModelFactory):
    class Meta:
        model = Department

    name = Faker('word')
    description = Faker('text')
    organization = factory.SubFactory(OrganizationFactory)

class TeamFactory(DjangoModelFactory):
    class Meta:
        model = Team

    name = Faker('word')
    description = Faker('text')
    department = factory.SubFactory(DepartmentFactory)

    @factory.post_generation
    def organization(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.department.organization = extracted
            self.department.save()

class TeamMemberFactory(DjangoModelFactory):
    class Meta:
        model = TeamMember

    user = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)
    role = TeamMember.Role.MEMBER
    is_active = True 