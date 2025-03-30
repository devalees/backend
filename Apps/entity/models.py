from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _
from Apps.core.models import BaseModel

User = get_user_model()

class ActiveManager(models.Manager):
    """Manager that filters out inactive objects by default"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Organization(BaseModel):
    """Organization model representing a company or business unit"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Entity'
        verbose_name_plural = 'Entities'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the organization and validate data"""
        skip_validation = kwargs.pop('skip_validation', False)
        validate_unique = kwargs.pop('validate_unique', True)
        if skip_validation:
            super().save(*args, **kwargs)
        else:
            if validate_unique:
                self.full_clean()
            super().save(*args, **kwargs)

    def hard_delete(self):
        """Hard delete the organization and all its departments"""
        self.delete(hard_delete=True)

    def delete(self, *args, **kwargs):
        """Delete the organization and all its departments"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            with transaction.atomic():
                # Delete all departments first
                for department in self.departments.all():
                    department.delete(hard_delete=True)
                # Then delete self using the parent's delete method
                models.Model.delete(self, *args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def clean(self):
        """Validate organization data"""
        # Check name length
        if len(self.name) > 255:
            raise ValidationError({"name": ["Organization name cannot exceed 255 characters"]})

        # Check name uniqueness
        if Organization.objects.exclude(pk=self.pk).filter(name=self.name).exists():
            raise ValidationError({"name": ["Organization with this name already exists"]})

class Department(BaseModel):
    """Department model representing a division within an organization"""
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    description = models.TextField(null=True, blank=True)

    # Add managers
    objects = models.Manager()  # Default manager that includes all objects
    active_objects = ActiveManager()  # Custom manager that filters out inactive objects

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Departments"
        unique_together = ['name', 'organization']

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    def save(self, *args, **kwargs):
        """Save the department and validate hierarchy"""
        if kwargs.pop('skip_validation', False):
            super().save(*args, **kwargs)
        else:
            if not self.organization_id:
                raise IntegrityError("Organization is required.")
            self.full_clean()
            super().save(*args, **kwargs)

    def hard_delete(self):
        """Hard delete the department and all its child departments"""
        with transaction.atomic():
            # Delete all child departments first
            for child in self.children.all():
                child.hard_delete()
            # Then delete self using the parent's delete method
            models.Model.delete(self)

    def delete(self, *args, **kwargs):
        """Delete the department and all its child departments"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            self.hard_delete()
        else:
            self.is_active = False
            self.save()

    def clean(self):
        """Validate department data"""
        # Check name length
        if len(self.name) > 255:
            raise ValidationError({"name": ["Department name cannot exceed 255 characters"]})

        # Check parent department
        if self.parent and self.parent.organization != self.organization:
            raise ValidationError("Parent department must belong to the same organization")

        # Check for circular reference
        if self.pk and self.parent:
            current = self.parent
            while current:
                if current.pk == self.pk:
                    raise ValidationError("Cannot set a department as its own parent or ancestor")
                current = current.parent

class Team(BaseModel):
    """Team model representing a group within a department"""
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teams')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_teams')
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Teams"
        unique_together = ['name', 'department']

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    def hard_delete(self):
        """Hard delete the team"""
        models.Model.delete(self)

    def delete(self, *args, **kwargs):
        """Delete the team"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            self.hard_delete()
        else:
            self.is_active = False
            self.save()

    def clean(self):
        """Validate team data"""
        # Check name length
        if len(self.name) > 255:
            raise ValidationError({"name": ["Team name cannot exceed 255 characters"]})

        # Check parent team
        if self.parent and self.parent.department != self.department:
            raise ValidationError("Parent team must belong to the same department")

class TeamMember(BaseModel):
    """TeamMember model representing a user's membership in a team"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=50, default='Member', blank=False)

    class Meta:
        unique_together = ('team', 'user')
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'
        ordering = ['team__name', 'user__username']

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"

    def clean(self):
        """Validate team member data"""
        # Check if user is already a member of this team
        if TeamMember.objects.exclude(pk=self.pk).filter(team=self.team, user=self.user).exists():
            raise ValidationError("User is already a member of this team")

        # Ensure role is not empty
        if not self.role:
            self.role = 'Member'
