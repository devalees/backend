from django.urls import path
from . import views

app_name = 'entity'

urlpatterns = [
    # Organization URLs
    path('', views.organization_list, name='organization_list'),
    path('create/', views.organization_create, name='organization_create'),
    path('<int:pk>/', views.organization_detail, name='organization_detail'),
    path('<int:pk>/update/', views.organization_update, name='organization_update'),
    path('<int:pk>/delete/', views.organization_delete, name='organization_delete'),
    
    # Department URLs
    path('<int:org_pk>/departments/', views.department_list, name='department_list'),
    path('<int:org_pk>/departments/create/', views.department_create, name='department_create'),
    path('<int:org_pk>/departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('<int:org_pk>/departments/<int:pk>/update/', views.department_update, name='department_update'),
    path('<int:org_pk>/departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Team URLs
    path('<int:org_pk>/departments/<int:dept_pk>/teams/', views.team_list, name='team_list'),
    path('<int:org_pk>/departments/<int:dept_pk>/teams/create/', views.team_create, name='team_create'),
    path('<int:org_pk>/departments/<int:dept_pk>/teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('<int:org_pk>/departments/<int:dept_pk>/teams/<int:pk>/update/', views.team_update, name='team_update'),
    path('<int:org_pk>/departments/<int:dept_pk>/teams/<int:pk>/delete/', views.team_delete, name='team_delete'),
    
    # Team Member URLs
    path('team-members/', views.team_member_list, name='team-member-list'),
    path('team-members/create/', views.team_member_create, name='team-member-create'),
    path('team-members/<int:pk>/', views.team_member_detail, name='team-member-detail'),
    path('team-members/<int:pk>/update/', views.team_member_update, name='team-member-update'),
    path('team-members/<int:pk>/delete/', views.team_member_delete, name='team-member-delete'),
] 