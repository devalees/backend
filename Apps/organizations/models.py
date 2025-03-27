from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class ActiveManager(models.Manager):
    """Manager that filters out inactive objects by default"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Organization(models.Model):
    """Organization model representing a company or business unit"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

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
        super().clean()
        
        # Check name length
        if len(self.name) > 100:
            raise ValidationError({"name": ["Organization name cannot exceed 100 characters"]})

class Department(models.Model):
    """Department model representing a division within an organization"""
    
    name = models.CharField(max_length=100)
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
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Add managers
    objects = models.Manager()  # Default manager that includes all objects
    active_objects = ActiveManager()  # Custom manager that filters out inactive objects

    class Meta:
        unique_together = ('name', 'organization')
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        default_manager_name = 'active_objects'  # Make active_objects the default manager

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
        super().clean()
        
        # Check if organization is active
        if self.organization and not self.organization.is_active:
            raise ValidationError("Cannot create department for inactive organization")

        # Check for self-parenting
        if self.parent == self:
            raise ValidationError("Department cannot be its own parent")

        # Check if parent department belongs to the same organization
        if self.parent and self.parent.organization != self.organization:
            raise ValidationError("Parent department must belong to the same organization")

        # Check for existing department name within the same organization
        if Department.objects.filter(
            name=self.name,
            organization=self.organization
        ).exclude(pk=self.pk).exists():
            raise ValidationError({"name": ["A department with this name already exists in this organization"]})

        # Check for circular references and hierarchy depth
        if self.parent:
            current = self.parent
            visited = {self.pk} if self.pk else set()
            depth = 1  # Initialize depth to 1 since we're counting levels (current level is 1)

            # Count the number of ancestors
            while current:
                if current.pk in visited:
                    raise ValidationError("Circular reference detected in department hierarchy")
                visited.add(current.pk)
                current = current.parent
                depth += 1

            # Check if adding this department would exceed the maximum depth
            if depth > 5:  # Maximum of 5 levels in hierarchy
                raise ValidationError({"__all__": ["Department hierarchy cannot exceed 5 levels"]})

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
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teams')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_teams')
    description = models.TextField(null=True, blank=True)
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
            for sub_team in self.sub_teams.all():
                sub_team.delete(hard_delete=True)
            # Hard delete all members
            for member in self.members.all():
                member.delete(hard_delete=True)
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save(skip_validation=True)
            # Soft delete all sub-teams
            for sub_team in self.sub_teams.all():
                sub_team.delete()
            # Soft delete all members
            for member in self.members.all():
                member.delete()

    def clean(self):
        """Validate team data"""
        super().clean()
        
        # Check if department is active
        if self.department and not self.department.is_active:
            raise ValidationError("Cannot create team for inactive department")

        # Check for self-parenting
        if self.parent == self:
            raise ValidationError("Team cannot be its own parent")

        # Check if parent team belongs to the same department
        if self.parent and self.parent.department != self.department:
            raise ValidationError("Parent team must belong to the same department")

        # Check for existing team name within the same department
        if Team.objects.filter(
            name=self.name,
            department=self.department
        ).exclude(pk=self.pk).exists():
            raise ValidationError({"name": ["A team with this name already exists in this department"]})

        # Check for circular references and hierarchy depth
        if self.parent:
            current = self.parent
            visited = {self.pk} if self.pk else set()
            depth = 0  # Initialize depth to 0 since we're counting ancestors

            # Count the number of ancestors
            while current:
                if current.pk in visited:
                    raise ValidationError("Circular reference detected in team hierarchy")
                visited.add(current.pk)
                current = current.parent
                depth += 1

            # Check if adding this team would exceed the maximum depth
            if depth >= 3:  # We're at level 4 (current level + 3 ancestors)
                raise ValidationError({"__all__": ["Maximum team hierarchy depth exceeded"]})

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
        sub_teams = list(self.sub_teams.all())
        for team in self.sub_teams.all():
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
    role = models.CharField(max_length=50, default='Member')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('team', 'user')
        verbose_name = 'Team Member'
        verbose_name_plural = 'Team Members'

    def __str__(self):
        return f'{self.user.username} - {self.team.name} ({self.role})'

    def save(self, *args, **kwargs):
        """Save the team member and validate data"""
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Soft delete the team member"""
        self.is_active = False
        self.save()

    def clean(self):
        """Validate team member data"""
        if not self.team.is_active:
            raise ValidationError({'team': 'Cannot add members to an inactive team.'})
        
        if TeamMember.objects.filter(team=self.team, user=self.user).exclude(pk=self.pk).exists():
            raise ValidationError({'user': 'This user is already a member of this team.'})
