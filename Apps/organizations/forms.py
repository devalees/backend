from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Organization, Department, Team, TeamMember

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': 100}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')

        if name:
            # Check for duplicate names
            if Organization.objects.filter(
                name=name,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError(_('Organization with this name already exists'))

        return cleaned_data

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': 100}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        if organization:
            self.fields['parent'].queryset = Department.objects.filter(
                organization=organization,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        organization = cleaned_data.get('organization')
        parent = cleaned_data.get('parent')

        if name and organization:
            # Check for duplicate names within the same organization
            if Department.objects.filter(
                name=name,
                organization=organization,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError(_('Department with this name already exists in this organization'))

        if parent:
            # Check for circular reference
            current = parent
            while current:
                if current.parent_id == self.instance.pk if self.instance else None:
                    raise ValidationError(_('Circular reference in department hierarchy is not allowed'))
                current = current.parent

            # Check hierarchy depth
            depth = 1
            current = parent
            while current:
                depth += 1
                if depth > 5:
                    raise ValidationError(_('Maximum department hierarchy depth exceeded (5 levels)'))
                current = current.parent

        return cleaned_data

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': 100}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        department = kwargs.pop('department', None)
        super().__init__(*args, **kwargs)
        
        if department:
            self.fields['parent'].queryset = Team.objects.filter(
                department=department,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        department = cleaned_data.get('department')
        parent = cleaned_data.get('parent')

        if name and department:
            # Check for duplicate names within the same department
            if Team.objects.filter(
                name=name,
                department=department,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError(_('Team with this name already exists in this department'))

        if parent:
            # Check if parent team is from the same department
            if parent.department != department:
                raise ValidationError(_('Parent team must be from the same department'))

            # Check for circular reference
            current = parent
            while current:
                if current.parent_id == self.instance.pk if self.instance else None:
                    raise ValidationError(_('Circular reference in team hierarchy is not allowed'))
                current = current.parent

            # Check hierarchy depth
            depth = 1
            current = parent
            while current:
                depth += 1
                if depth > 5:
                    raise ValidationError(_('Maximum team hierarchy depth exceeded (5 levels)'))
                current = current.parent

        return cleaned_data

class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['team', 'user', 'role']
        widgets = {
            'role': forms.TextInput(attrs={'maxlength': 50}),
        }

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        user = cleaned_data.get('user')

        if team and user:
            # Check if user is already a member of this team
            if TeamMember.objects.filter(
                team=team,
                user=user,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError(_('User is already a member of this team'))

            # Check if team is active
            if not team.is_active:
                raise ValidationError(_('Cannot add member to inactive team'))

        return cleaned_data

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role and len(role) > 50:
            raise ValidationError(_('Role cannot exceed 50 characters'))
        return role 