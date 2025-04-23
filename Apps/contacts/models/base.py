from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email
from Apps.core.models import TaskAwareModel, TimeStampedModel, UserTrackedModel
from Apps.entity.models import Organization, Department, Team
from Apps.rbac.models import RBACBaseModel
from Apps.filtering.base_model import FilterableAggregatableModel

User = get_user_model()

class ContactsBaseModel(RBACBaseModel, FilterableAggregatableModel, TaskAwareModel, TimeStampedModel, UserTrackedModel):
    """Base model for all contacts app models with common fields"""
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        null=True,  # Temporarily allow null
        blank=True  # Temporarily allow blank
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
