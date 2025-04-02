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

    def __str__(self):
        return self.title 

    class Meta:
        verbose_name = 'Test Document'
        verbose_name_plural = 'Test Documents' 