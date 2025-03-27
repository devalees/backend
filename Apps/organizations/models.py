from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Organization(models.Model):
    """Organization model representing a company or business unit"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Organizations"

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

    def delete(self, *args, **kwargs):
        """Delete the organization and all its departments"""
        if kwargs.pop('hard_delete', False):
            # Hard delete all departments first
            for department in self.departments.all():
                department.delete(hard_delete=True)
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save(skip_validation=True)
            # Soft delete all departments
            for department in self.departments.all():
                department.delete()

    def clean(self):
        """Validate organization data"""
        if Organization.objects.filter(name=self.name).exclude(pk=self.pk).exists():
            raise ValidationError({'name': 'An organization with this name already exists.'})

class Department(models.Model):
    """Department model representing a division within an organization"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='departments',
        null=False
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Departments"
        unique_together = ['name', 'organization']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the department and validate hierarchy"""
        if kwargs.pop('skip_validation', False):
            super().save(*args, **kwargs)
        else:
            if not self.organization_id:
                raise IntegrityError("Organization is required.")
            self.full_clean()
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete the department and all its sub-departments and teams"""
        if kwargs.pop('hard_delete', False):
            # Hard delete all sub-departments first
            for sub_dept in self.children.all():
                sub_dept.delete(hard_delete=True)
            # Hard delete all teams
            for team in self.teams.all():
                team.delete(hard_delete=True)
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save(skip_validation=True)
            # Soft delete all sub-departments
            for sub_dept in self.children.all():
                sub_dept.delete()
            # Soft delete all teams
            for team in self.teams.all():
                team.delete()

    def clean(self):
        """Validate department data"""
        if not self.organization.is_active:
            raise ValidationError(_('Cannot create department for inactive organization'))

        if self.parent:
            # Check if parent belongs to same organization
            if self.parent.organization != self.organization:
                raise ValidationError({'parent': 'Parent department must belong to the same organization.'})
            
            # Check for circular reference
            if self.pk and self.parent.pk == self.pk:
                raise ValidationError({'parent': 'A department cannot be its own parent.'})
            
            # Check hierarchy depth (max 5 levels)
            depth = 1
            current = self.parent
            while current and current.parent:
                depth += 1
                current = current.parent
            if depth >= 5:
                raise ValidationError({'parent': 'Maximum department hierarchy depth exceeded (5 levels).'})
        
        # Check unique name within organization
        if Department.objects.filter(name=self.name, organization=self.organization).exclude(pk=self.pk).exists():
            raise ValidationError({'name': 'A department with this name already exists in this organization.'})

    def get_hierarchy_path(self):
        """Get the full path of the department in the hierarchy"""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)

    def get_parent_departments(self):
        """Get all parent departments in the hierarchy"""
        parents = []
        current = self.parent
        while current:
            parents.append(current)
            current = current.parent
        return parents

    def get_root_department(self):
        """Get the root department (top-level parent)"""
        current = self
        while current.parent:
            current = current.parent
        return current

    def get_all_sub_departments(self):
        """Get all sub-departments recursively"""
        sub_departments = list(self.children.all())
        for department in self.children.all():
            sub_departments.extend(department.get_all_sub_departments())
        return sub_departments

class Team(models.Model):
    """Team model representing a group within a department"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='teams',
        null=False
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Teams"
        unique_together = ['name', 'department']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the team and validate hierarchy"""
        if kwargs.pop('skip_validation', False):
            super().save(*args, **kwargs)
        else:
            if not self.department_id:
                raise IntegrityError("Department is required.")
            self.full_clean()
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete the team and all its sub-teams"""
        if kwargs.pop('hard_delete', False):
            # Hard delete all sub-teams first
            for sub_team in self.children.all():
                sub_team.delete(hard_delete=True)
            # Hard delete all members
            for member in self.members.all():
                member.delete(hard_delete=True)
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save(skip_validation=True)
            # Soft delete all sub-teams
            for sub_team in self.children.all():
                sub_team.delete()
            # Soft delete all members
            for member in self.members.all():
                member.delete()

    def clean(self):
        """Validate team data"""
        if not self.department.is_active:
            raise ValidationError(_('Cannot create team for inactive department'))

        if self.parent:
            # Check if parent belongs to same department
            if self.parent.department != self.department:
                raise ValidationError({'parent': 'Parent team must belong to the same department.'})
            
            # Check for circular reference
            if self.pk and self.parent.pk == self.pk:
                raise ValidationError({'parent': 'A team cannot be its own parent.'})
            
            # Check hierarchy depth (max 5 levels)
            depth = 1
            current = self.parent
            while current and current.parent:
                depth += 1
                current = current.parent
            if depth >= 5:
                raise ValidationError({'parent': 'Maximum team hierarchy depth exceeded (5 levels).'})
        
        # Check unique name within department
        if Team.objects.filter(name=self.name, department=self.department).exclude(pk=self.pk).exists():
            raise ValidationError({'name': 'A team with this name already exists in this department.'})

    def get_hierarchy_path(self):
        """Get the full path of the team in the hierarchy"""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)

    def get_parent_teams(self):
        """Get all parent teams in the hierarchy"""
        parents = []
        current = self.parent
        while current:
            parents.append(current)
            current = current.parent
        return parents

    def get_root_team(self):
        """Get the root team (top-level parent)"""
        current = self
        while current.parent:
            current = current.parent
        return current

    def get_all_sub_teams(self):
        """Get all sub-teams recursively"""
        sub_teams = list(self.children.all())
        for team in self.children.all():
            sub_teams.extend(team.get_all_sub_teams())
        return sub_teams

class TeamMember(models.Model):
    """TeamMember model representing a user's membership in a team"""
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    role = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Team Members"
        unique_together = ['team', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.team.name}"

    def save(self, *args, **kwargs):
        """Save the team member and validate data"""
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Soft delete the team member"""
        self.is_active = False
        self.save(skip_validation=True)

    def clean(self):
        """Validate team member data"""
        if not self.team.is_active:
            raise ValidationError({'team': 'Cannot add members to an inactive team.'})
        
        if TeamMember.objects.filter(team=self.team, user=self.user).exclude(pk=self.pk).exists():
            raise ValidationError({'user': 'This user is already a member of this team.'})
