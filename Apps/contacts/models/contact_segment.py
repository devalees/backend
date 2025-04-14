from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .base import ContactsBaseModel
from .contact_list import ContactList

class ContactSegment(ContactsBaseModel):
    """ContactSegment model for defining segments within a contact list based on filter criteria"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    contact_list = models.ForeignKey(
        ContactList,
        on_delete=models.CASCADE,
        related_name='segments'
    )
    filter_criteria = models.JSONField(
        help_text="JSON structure defining the filter criteria for the segment"
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Contact Segment'
        verbose_name_plural = 'Contact Segments'
        ordering = ['name']
        unique_together = ['name', 'contact_list']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def hard_delete(self, user=None, request_meta=None):
        """Permanently delete the contact segment"""
        super().delete()
    
    def delete(self, *args, **kwargs):
        """Soft delete the contact segment"""
        self.is_active = False
        self.save()
    
    def clean(self):
        """Validate the contact segment"""
        if not self.name:
            raise ValidationError({'name': _('Name is required')})
        
        if self.contact_list is None:
            raise ValidationError({'contact_list': _('Contact list is required')})
        
        # Validate filter criteria
        if not isinstance(self.filter_criteria, dict):
            raise ValidationError({'filter_criteria': _('Filter criteria must be a dictionary')})
        
        # Validate filter criteria structure
        self._validate_filter_criteria(self.filter_criteria)
        
        # Validate metadata is a dictionary
        if not isinstance(self.metadata, dict):
            raise ValidationError({'metadata': _('Metadata must be a dictionary')})
    
    def _validate_filter_criteria(self, criteria):
        """Validate the structure of filter criteria"""
        # Check for simple criteria
        if 'field' in criteria and 'operator' in criteria and 'value' in criteria:
            return
        
        # Check for complex criteria with AND/OR operators
        if 'operator' in criteria and criteria['operator'] in ['and', 'or']:
            if 'criteria' not in criteria or not isinstance(criteria['criteria'], list):
                raise ValidationError({
                    'filter_criteria': _('Complex criteria must have a list of sub-criteria')
                })
            
            # Validate each sub-criteria
            for sub_criteria in criteria['criteria']:
                self._validate_filter_criteria(sub_criteria)
        else:
            raise ValidationError({
                'filter_criteria': _('Invalid filter criteria structure')
            })
    
    def get_matching_contacts(self):
        """Get contacts that match the filter criteria"""
        contacts = self.contact_list.contacts.all()
        return self._apply_filter_criteria(contacts, self.filter_criteria)
    
    def _apply_filter_criteria(self, contacts, criteria):
        """Apply filter criteria to a queryset of contacts"""
        # Handle simple criteria
        if 'field' in criteria and 'operator' in criteria and 'value' in criteria:
            field = criteria['field']
            operator = criteria['operator']
            value = criteria['value']
            
            filter_kwargs = {}
            if operator == 'equals':
                filter_kwargs[field] = value
            elif operator == 'contains':
                filter_kwargs[f"{field}__icontains"] = value
            elif operator == 'startswith':
                filter_kwargs[f"{field}__istartswith"] = value
            elif operator == 'endswith':
                filter_kwargs[f"{field}__iendswith"] = value
            elif operator == 'gt':
                filter_kwargs[f"{field}__gt"] = value
            elif operator == 'gte':
                filter_kwargs[f"{field}__gte"] = value
            elif operator == 'lt':
                filter_kwargs[f"{field}__lt"] = value
            elif operator == 'lte':
                filter_kwargs[f"{field}__lte"] = value
            elif operator == 'in':
                filter_kwargs[f"{field}__in"] = value
            else:
                return contacts.none()
                
            return contacts.filter(**filter_kwargs)
        
        # Handle complex criteria with AND/OR operators
        if 'operator' in criteria and criteria['operator'] in ['and', 'or'] and 'criteria' in criteria:
            sub_criteria = criteria['criteria']
            
            if not sub_criteria:
                return contacts
            
            # Start with all contacts for OR, none for AND
            if criteria['operator'] == 'or':
                result = contacts.none()
            else:  # 'and'
                result = contacts.all()
            
            # Apply each sub-criteria
            for sub_criteria_item in sub_criteria:
                sub_result = self._apply_filter_criteria(contacts, sub_criteria_item)
                
                if criteria['operator'] == 'and':
                    result = result.filter(id__in=sub_result.values_list('id', flat=True))
                else:  # 'or'
                    result = result.union(sub_result)
            
            return result.distinct()
        
        return contacts.none()
