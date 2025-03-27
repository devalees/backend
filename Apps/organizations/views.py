from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .models import Organization, Department, Team, TeamMember
from .forms import OrganizationForm, DepartmentForm, TeamForm, TeamMemberForm

@login_required
def organization_list(request):
    """List all organizations"""
    organizations = Organization.objects.filter(is_active=True)
    return render(request, 'organizations/organization_list.html', {
        'organizations': organizations
    })

@login_required
def organization_detail(request, pk):
    """Show organization details"""
    organization = get_object_or_404(Organization, pk=pk, is_active=True)
    return render(request, 'organizations/organization_detail.html', {
        'organization': organization
    })

@login_required
def organization_create(request):
    """Create a new organization"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if not name:
            return HttpResponseBadRequest('Organization name is required')
            
        if Organization.objects.filter(name=name).exists():
            return HttpResponseBadRequest('Organization with this name already exists')
            
        organization = Organization.objects.create(
            name=name,
            description=description
        )
        messages.success(request, 'Organization created successfully.')
        return redirect('organizations:organization_detail', pk=organization.pk)
    return render(request, 'organizations/organization_form.html')

@login_required
def organization_update(request, pk):
    """Update an organization"""
    organization = get_object_or_404(Organization, pk=pk, is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name')
        if not name:
            return HttpResponseBadRequest('Organization name is required')
            
        if Organization.objects.filter(name=name).exclude(pk=pk).exists():
            return HttpResponseBadRequest('Organization with this name already exists')
            
        organization.name = name
        organization.description = request.POST.get('description')
        organization.save()
        messages.success(request, 'Organization updated successfully.')
        return redirect('organizations:organization_detail', pk=organization.pk)
    return render(request, 'organizations/organization_form.html', {
        'organization': organization
    })

@login_required
def organization_delete(request, pk):
    """Soft delete an organization"""
    organization = get_object_or_404(Organization, pk=pk, is_active=True)
    if request.method == 'POST':
        organization.is_active = False
        organization.save()
        messages.success(request, 'Organization deleted successfully.')
        return redirect('organizations:organization_list')
    return render(request, 'organizations/organization_confirm_delete.html', {
        'organization': organization
    })

@login_required
def department_list(request, org_pk):
    """List all departments in an organization"""
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    departments = Department.objects.filter(organization=organization, is_active=True)
    return render(request, 'organizations/department_list.html', {
        'organization': organization,
        'departments': departments
    })

@login_required
def department_detail(request, org_pk, pk):
    """Show department details"""
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    department = get_object_or_404(Department, pk=pk, organization=organization, is_active=True)
    return render(request, 'organizations/department_detail.html', {
        'organization': organization,
        'department': department
    })

@login_required
def department_create(request, org_pk):
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        parent_id = request.POST.get('parent')
        
        if not name:
            return HttpResponseBadRequest('Department name is required')
            
        if Department.objects.filter(name=name, organization=organization).exists():
            return HttpResponseBadRequest('Department with this name already exists in this organization')
        
        parent = None
        if parent_id:
            parent = get_object_or_404(Department, pk=parent_id, organization=organization, is_active=True)
            # Check for circular reference
            current = parent
            while current:
                if current.parent_id == parent_id:
                    return HttpResponseBadRequest('Circular reference in department hierarchy is not allowed')
                current = current.parent
        
        department = Department.objects.create(
            name=name,
            description=description,
            organization=organization,
            parent=parent
        )
        messages.success(request, 'Department created successfully.')
        return redirect('organizations:department_detail', org_pk=organization.pk, pk=department.pk)
    return render(request, 'organizations/department_form.html', {
        'organization': organization
    })

@login_required
def department_update(request, org_pk, pk):
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    department = get_object_or_404(Department, pk=pk, organization=organization, is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        parent_id = request.POST.get('parent')
        
        if not name:
            return HttpResponseBadRequest('Department name is required')
            
        if Department.objects.filter(name=name, organization=organization).exclude(pk=pk).exists():
            return HttpResponseBadRequest('Department with this name already exists in this organization')
            
        department.name = name
        department.description = description
        
        if parent_id:
            parent = get_object_or_404(Department, pk=parent_id, organization=organization, is_active=True)
            department.parent = parent
        else:
            department.parent = None
            
        try:
            department.save()
            messages.success(request, 'Department updated successfully.')
            return redirect('organizations:department_detail', org_pk=organization.pk, pk=department.pk)
        except ValidationError as e:
            return HttpResponseBadRequest(str(e))
            
    return render(request, 'organizations/department_form.html', {
        'organization': organization,
        'department': department
    })

@login_required
def department_delete(request, org_pk, pk):
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    department = get_object_or_404(Department, pk=pk, organization=organization, is_active=True)
    
    if request.method == 'POST':
        # Check if department has active teams
        if Team.objects.filter(department=department, is_active=True).exists():
            return HttpResponseBadRequest('Cannot delete department with active teams')
            
        department.is_active = False
        department.save()
        messages.success(request, 'Department deleted successfully.')
        return redirect('organizations:department_list', org_pk=organization.pk)
    return render(request, 'organizations/department_confirm_delete.html', {
        'organization': organization,
        'department': department
    })

@login_required
def team_list(request, org_pk, dept_pk):
    """List all teams in a department"""
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    department = get_object_or_404(Department, pk=dept_pk, organization=organization, is_active=True)
    teams = Team.objects.filter(department=department, is_active=True)
    return render(request, 'organizations/team_list.html', {
        'organization': organization,
        'department': department,
        'teams': teams
    })

@login_required
def team_detail(request, org_pk, dept_pk, pk):
    """Show team details"""
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    department = get_object_or_404(Department, pk=dept_pk, organization=organization, is_active=True)
    team = get_object_or_404(Team, pk=pk, department=department, is_active=True)
    return render(request, 'organizations/team_detail.html', {
        'organization': organization,
        'department': department,
        'team': team
    })

@login_required
def team_create(request, org_pk, dept_pk):
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    department = get_object_or_404(Department, pk=dept_pk, organization=organization, is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        parent_id = request.POST.get('parent')
        
        if not name:
            return HttpResponseBadRequest('Team name is required')
            
        if Team.objects.filter(name=name, department=department).exists():
            return HttpResponseBadRequest('Team with this name already exists in this department')
        
        if parent_id:
            try:
                parent = Team.objects.get(pk=parent_id, is_active=True)
                if parent.department_id != department.id:
                    return HttpResponseBadRequest('Parent team must be from the same department')
            except Team.DoesNotExist:
                return HttpResponseBadRequest('Parent team not found')
        else:
            parent = None
            
        try:
            team = Team.objects.create(
                name=name,
                description=description,
                department=department,
                parent=parent
            )
            messages.success(request, 'Team created successfully.')
            return redirect('organizations:team_detail', org_pk=organization.pk, dept_pk=department.pk, pk=team.pk)
        except ValidationError as e:
            return HttpResponseBadRequest(str(e))
            
    return render(request, 'organizations/team_form.html', {
        'organization': organization,
        'department': department
    })

@login_required
def team_update(request, org_pk, dept_pk, pk):
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    department = get_object_or_404(Department, pk=dept_pk, organization=organization, is_active=True)
    team = get_object_or_404(Team, pk=pk, department=department, is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if not name:
            return HttpResponseBadRequest('Team name is required')
            
        if Team.objects.filter(name=name, department=department).exclude(pk=pk).exists():
            return HttpResponseBadRequest('Team with this name already exists in this department')
            
        parent_id = request.POST.get('parent')
        if parent_id:
            parent = get_object_or_404(Team, pk=parent_id, department=department, is_active=True)
            # Check for circular reference
            current = parent
            while current:
                if current.parent_id == team.pk:
                    return HttpResponseBadRequest('Circular reference in team hierarchy is not allowed')
                current = current.parent
            team.parent = parent
        else:
            team.parent = None
            
        team.name = name
        team.description = request.POST.get('description')
        team.save()
        messages.success(request, 'Team updated successfully.')
        return redirect('organizations:team_detail', org_pk=organization.pk, dept_pk=department.pk, pk=team.pk)
    return render(request, 'organizations/team_form.html', {
        'organization': organization,
        'department': department,
        'team': team
    })

@login_required
def team_delete(request, org_pk, dept_pk, pk):
    organization = get_object_or_404(Organization, pk=org_pk, is_active=True)
    department = get_object_or_404(Department, pk=dept_pk, organization=organization, is_active=True)
    team = get_object_or_404(Team, pk=pk, department=department, is_active=True)
    
    if request.method == 'POST':
        # Check if team has active sub-teams
        if Team.objects.filter(parent=team, is_active=True).exists():
            return HttpResponseBadRequest('Cannot delete team with active sub-teams')
            
        team.is_active = False
        team.save()
        messages.success(request, 'Team deleted successfully.')
        return redirect('organizations:team_list', org_pk=organization.pk, dept_pk=department.pk)
    return render(request, 'organizations/team_confirm_delete.html', {
        'organization': organization,
        'department': department,
        'team': team
    })

@login_required
def team_member_list(request):
    """List all team members"""
    team_members = TeamMember.objects.filter(
        team__department__organization__is_active=True,
        team__department__is_active=True,
        team__is_active=True,
        is_active=True
    ).select_related('team', 'team__department', 'team__department__organization', 'user')
    
    context = {
        'team_members': team_members,
    }
    return render(request, 'organizations/team_member_list.html', context)

@login_required
def team_member_create(request):
    """Create a new team member"""
    if request.method == 'POST':
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            try:
                team_member = form.save()
                messages.success(request, _('Team member created successfully.'))
                return redirect('organizations:team-member-detail', pk=team_member.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = TeamMemberForm()
    
    context = {
        'form': form,
    }
    return render(request, 'organizations/team_member_form.html', context)

@login_required
def team_member_detail(request, pk):
    """View team member details"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    
    context = {
        'team_member': team_member,
    }
    return render(request, 'organizations/team_member_detail.html', context)

@login_required
def team_member_update(request, pk):
    """Update a team member"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, instance=team_member)
        if form.is_valid():
            try:
                updated_member = form.save()
                messages.success(request, _('Team member updated successfully.'))
                return redirect('organizations:team-member-detail', pk=updated_member.pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = TeamMemberForm(instance=team_member)
    
    context = {
        'form': form,
        'team_member': team_member,
    }
    return render(request, 'organizations/team_member_form.html', context)

@login_required
def team_member_delete(request, pk):
    """Delete a team member"""
    team_member = get_object_or_404(TeamMember, pk=pk)
    
    if request.method == 'POST':
        try:
            team_member.delete()
            messages.success(request, _('Team member deleted successfully.'))
            return redirect('organizations:team-member-list')
        except ValidationError as e:
            messages.error(request, str(e))
    
    context = {
        'team_member': team_member,
    }
    return render(request, 'organizations/team_member_confirm_delete.html', context)

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organizations/organization_list.html'
    context_object_name = 'organizations'

    def get_queryset(self):
        return Organization.objects.filter(is_active=True)

class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = 'organizations/organization_detail.html'
    context_object_name = 'organization'

    def get_queryset(self):
        return Organization.objects.filter(is_active=True)

class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'organizations/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        return Department.objects.filter(
            organization_id=self.kwargs['org_pk'],
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = Organization.objects.get(pk=self.kwargs['org_pk'])
        return context

class DepartmentDetailView(LoginRequiredMixin, DetailView):
    model = Department
    template_name = 'organizations/department_detail.html'
    context_object_name = 'department'

    def get_queryset(self):
        return Department.objects.filter(
            organization_id=self.kwargs['org_pk'],
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = Organization.objects.get(pk=self.kwargs['org_pk'])
        return context

class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = 'organizations/team_list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        return Team.objects.filter(
            department_id=self.kwargs['dept_pk'],
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = Organization.objects.get(pk=self.kwargs['org_pk'])
        context['department'] = Department.objects.get(pk=self.kwargs['dept_pk'])
        return context

class TeamDetailView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = 'organizations/team_detail.html'
    context_object_name = 'team'

    def get_queryset(self):
        return Team.objects.filter(
            department_id=self.kwargs['dept_pk'],
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = Organization.objects.get(pk=self.kwargs['org_pk'])
        context['department'] = Department.objects.get(pk=self.kwargs['dept_pk'])
        return context
