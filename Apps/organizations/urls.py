from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    # Organization URLs
    path('organizations/', views.organization_list, name='organization_list'),
    path('organizations/<int:pk>/', views.organization_detail, name='organization_detail'),
    path('organizations/create/', views.organization_create, name='organization_create'),
    path('organizations/<int:pk>/update/', views.organization_update, name='organization_update'),
    path('organizations/<int:pk>/delete/', views.organization_delete, name='organization_delete'),
    
    # Department URLs
    path('organizations/<int:org_pk>/departments/', views.department_list, name='department_list'),
    path('organizations/<int:org_pk>/departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('organizations/<int:org_pk>/departments/create/', views.department_create, name='department_create'),
    path('organizations/<int:org_pk>/departments/<int:pk>/update/', views.department_update, name='department_update'),
    path('organizations/<int:org_pk>/departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Team URLs
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/', views.team_list, name='team_list'),
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/create/', views.team_create, name='team_create'),
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/<int:pk>/update/', views.team_update, name='team_update'),
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/<int:pk>/delete/', views.team_delete, name='team_delete'),
    
    # Team Member URLs
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/<int:team_pk>/members/', views.team_member_list, name='team_member_list'),
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/<int:team_pk>/members/<int:pk>/', views.team_member_detail, name='team_member_detail'),
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/<int:team_pk>/members/create/', views.team_member_create, name='team_member_create'),
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/<int:team_pk>/members/<int:pk>/update/', views.team_member_update, name='team_member_update'),
    path('organizations/<int:org_pk>/departments/<int:dept_pk>/teams/<int:team_pk>/members/<int:pk>/delete/', views.team_member_delete, name='team_member_delete'),
] 