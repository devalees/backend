from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from ..base import RBACModel
from ..mixins import RBACModelMixin

User = get_user_model()

# TestDocument model has been moved to Apps/rbac/models.py