from factory.django import DjangoModelFactory
from factory import Sequence, LazyAttribute, PostGenerationMethodCall, LazyFunction, SubFactory, Faker
from django.contrib.auth import get_user_model
from Apps.core.models import BaseModel
from django.utils import timezone

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = Sequence(lambda n: f'user{n}')
    email = Sequence(lambda n: f'user{n}@example.com')
    password = 'testpass123'
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the _create method to handle email validation and password setting"""
        if 'email' in kwargs and kwargs['email'] is None:
            raise ValueError('Email is required')
        if 'email' in kwargs:
            kwargs['email'] = kwargs['email'].lower()
        manager = cls._get_manager(model_class)
        if 'password' in kwargs:
            password = kwargs.pop('password')
        else:
            password = 'testpass123'
        user = manager.create(*args, **kwargs)
        user.set_password(password)
        user.save()
        return user

class BaseModelFactory(DjangoModelFactory):
    class Meta:
        abstract = True
        model = BaseModel

    created_at = LazyFunction(timezone.now)
    updated_at = LazyFunction(timezone.now)
    created_by = SubFactory(UserFactory)
    updated_by = SubFactory(UserFactory)
    is_active = True 