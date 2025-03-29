import factory
from django.utils import timezone
from Apps.project.models import Project, Task
from Apps.users.models import User
from Apps.entity.models import Organization

class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')
    start_date = factory.LazyFunction(timezone.now)
    end_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=30))
    status = 'new'
    priority = 'medium'
    owner = factory.SubFactory('Apps.users.tests.factories.UserFactory')
    organization = factory.SubFactory('Apps.entity.tests.factories.OrganizationFactory')
    created_by = factory.SelfAttribute('owner')
    updated_by = factory.SelfAttribute('owner')

    @factory.post_generation
    def team_members(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for member in extracted:
                self.team_members.add(member)

class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')
    due_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=7))
    status = 'todo'
    priority = 'medium'
    project = factory.SubFactory(ProjectFactory)
    assigned_to = factory.SubFactory('Apps.users.tests.factories.UserFactory')
    created_by = factory.SelfAttribute('assigned_to')
    updated_by = factory.SelfAttribute('assigned_to')
    parent_task = None
