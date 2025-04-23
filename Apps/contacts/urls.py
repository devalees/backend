from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContactViewSet, ContactGroupViewSet, ContactTemplateViewSet,
    CommunicationViewSet, CommunicationTemplateViewSet,
    CommunicationMonitoringViewSet, ContactListViewSet,
    ContactNoteViewSet, ContactNoteNotificationViewSet,
    ContactNoteMonitoringViewSet
)

# Define the app name for namespacing
app_name = 'contacts'

# Main contacts router
router = DefaultRouter()
router.register(r'contacts', ContactViewSet)
router.register(r'groups', ContactGroupViewSet)
router.register(r'templates', ContactTemplateViewSet)
router.register(r'communications', CommunicationViewSet)
router.register(r'communication-templates', CommunicationTemplateViewSet)
router.register(r'communication-activities', CommunicationMonitoringViewSet)
router.register(r'lists', ContactListViewSet, basename='contactlist')

# Notes router
notes_router = DefaultRouter()
notes_router.register(r'notes', ContactNoteViewSet, basename='contact-notes')
notes_router.register(r'note-notifications', ContactNoteNotificationViewSet, basename='contact-note-notifications')
notes_router.register(r'note-monitoring', ContactNoteMonitoringViewSet, basename='contact-note-monitoring')

urlpatterns = [
    # Include all router URLs
    path('', include(router.urls)),
    path('', include(notes_router.urls)),
    
    # Special note endpoints
    path('notes/<int:pk>/download/', 
         ContactNoteViewSet.as_view({'get': 'download_file'}),
         name='contact-note-download-file'),
    path('notes/<int:pk>/hard-delete/', 
         ContactNoteViewSet.as_view({'delete': 'hard_delete'}),
         name='contact-note-hard-delete'),
    
    # API v1 endpoints
    path('api/v1/', include((router.urls, 'api-v1'))),
    path('api/v1/', include((notes_router.urls, 'api-v1-notes'))),
    
    # Note notification and monitoring endpoints
    path('api/v1/note-notifications/', 
         ContactNoteNotificationViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='contact-note-notifications-api'),
    path('api/v1/note-monitoring/', 
         ContactNoteMonitoringViewSet.as_view({'get': 'list'}),
         name='contact-note-monitoring-api'),
] 