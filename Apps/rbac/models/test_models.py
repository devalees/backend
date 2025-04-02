"""
Test models for RBAC testing.
"""

from django.conf import settings
from django.db import models
from ..base import RBACModel

class TestDocument(RBACModel):
    """
    A test document model for RBAC testing.
    """
    title = models.CharField(max_length=255)
    content = models.TextField()
    secret_key = models.CharField(max_length=100)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='test_documents'
    )

    def __str__(self):
        return self.title 

    class Meta:
        verbose_name = 'Test Document'
        verbose_name_plural = 'Test Documents'

    def save(self, *args, **kwargs):
        """Save the test document."""
        user = kwargs.pop('user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs) 