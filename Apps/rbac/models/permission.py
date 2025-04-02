"""
Permission models for RBAC.
"""

from django.db import models
from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from ..base import RBACModel

class RBACPermission(RBACModel):
    """
    Model-level permission for RBAC.
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text=_('Content type this permission applies to.')
    )
    codename = models.CharField(
        _('codename'),
        max_length=100,
        help_text=_('Permission codename.')
    )
    name = models.CharField(
        _('name'),
        max_length=255,
        help_text=_('Permission name.')
    )
    permission_type = models.CharField(
        max_length=50,
        choices=[
            ('read', 'Read'),
            ('write', 'Write'),
            ('delete', 'Delete'),
            ('view', 'View'),
            ('change', 'Change'),
            ('add', 'Add')
        ],
        help_text=_('Permission type.')
    )
    field_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_('Field name this permission applies to.')
    )

    class Meta:
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        unique_together = [['content_type', 'codename']]
        ordering = ['content_type__app_label', 'content_type__model', 'codename']

    def __str__(self):
        return f"{self.name} ({self.content_type.model})"

    def clean(self):
        """
        Validate the permission.
        """
        if not self.content_type:
            raise ValidationError(_('Content type is required.'))
        if not self.codename:
            raise ValidationError(_('Codename is required.'))
        if not self.name:
            raise ValidationError(_('Name is required.'))
        super().clean()

class FieldPermission(RBACModel):
    """
    Model for storing field-level permissions.
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='field_permissions'
    )
    field_name = models.CharField(max_length=255)
    permission_type = models.CharField(
        max_length=10,
        choices=[('read', 'Read'), ('write', 'Write')]
    )

    class Meta:
        unique_together = ('content_type', 'field_name', 'permission_type')
        ordering = ['content_type', 'field_name']

    def clean(self):
        super().clean()
        if not self.content_type_id:
            raise ValidationError(_('Content type is required.'))
        
        try:
            model_class = self.content_type.model_class()
            if not model_class:
                raise ValidationError(_('Invalid content type.'))
            
            # Check if field exists in model
            try:
                model_class._meta.get_field(self.field_name)
            except FieldDoesNotExist:
                raise ValidationError(_(f'Field {self.field_name} does not exist in {model_class.__name__}.'))
        except ContentType.DoesNotExist:
            raise ValidationError(_('Invalid content type.'))

    def __str__(self):
        return f"{self.permission_type} {self.field_name} ({self.content_type.model})" 