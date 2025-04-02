"""
User role model for RBAC.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..base import RBACModel

class UserRole(RBACModel):
    """
    Links users to roles.
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='user_roles',
        help_text=_('User this role is assigned to.')
    )
    role = models.ForeignKey(
        'rbac.Role',
        on_delete=models.CASCADE,
        related_name='user_roles',
        help_text=_('Role assigned to the user.')
    )
    expiry_date = models.DateTimeField(
        _('expiry date'),
        null=True,
        blank=True,
        help_text=_('When this role assignment expires.')
    )

    class Meta:
        verbose_name = _('user role')
        verbose_name_plural = _('user roles')
        unique_together = [['user', 'role']]
        ordering = ['user__username', 'role__name']

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

    def clean(self):
        """
        Validate the user role.
        """
        if not self.user_id:
            raise ValidationError(_('User is required.'))
        if not self.role_id:
            raise ValidationError(_('Role is required.'))
        if self.expiry_date and self.expiry_date < timezone.now():
            raise ValidationError(_('Expiry date cannot be in the past.'))
        super().clean()

    def is_expired(self):
        """
        Check if the role assignment has expired.
        """
        if self.expiry_date:
            return self.expiry_date < timezone.now()
        return False 