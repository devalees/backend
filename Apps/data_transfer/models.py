from django.db import models
from django.core.exceptions import ValidationError
from Apps.core.models import BaseModel
from Apps.entity.models import Organization
from Apps.contacts.models import Contact
from django.utils.translation import gettext_lazy as _

class DataTransfer(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')

    VALID_TRANSITIONS = {
        Status.DRAFT: [Status.IN_PROGRESS, Status.CANCELLED],
        Status.IN_PROGRESS: [Status.COMPLETED, Status.CANCELLED],
        Status.COMPLETED: [Status.CANCELLED],
        Status.CANCELLED: [],
    }

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    source_organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='source_transfers'
    )
    destination_organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='destination_transfers'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    def clean(self):
        if self.source_organization == self.destination_organization:
            raise ValidationError('Source and destination organizations cannot be the same.')
        
        if not self._state.adding:
            old_instance = DataTransfer.objects.get(pk=self.pk)
            old_status = old_instance.status
            new_status = self.status

            if old_status != new_status and new_status not in self.VALID_TRANSITIONS[old_status]:
                raise ValidationError(f'Invalid status transition from {old_status} to {new_status}')

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

class DataTransferItem(BaseModel):
    data_transfer = models.ForeignKey(
        DataTransfer,
        on_delete=models.CASCADE,
        related_name='items'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='transfer_items'
    )
    status = models.CharField(
        max_length=20,
        choices=DataTransfer.Status.choices,
        default=DataTransfer.Status.DRAFT
    )

    def clean(self):
        if self.contact.organization != self.data_transfer.source_organization:
            raise ValidationError('Contact must belong to the source organization.')

    def __str__(self):
        return f"{self.data_transfer.name} - {self.contact.name}"

    class Meta:
        unique_together = ('data_transfer', 'contact') 