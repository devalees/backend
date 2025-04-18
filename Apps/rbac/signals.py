from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Role

@receiver(m2m_changed, sender=Role.permissions.through)
def handle_role_permissions_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Handle changes to role permissions"""
    pass  # Cache functionality removed 