from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, ContactGroupViewSet, ContactTemplateViewSet, CommunicationViewSet, CommunicationTemplateViewSet, CommunicationMonitoringViewSet, ContactListViewSet
from .views import ContactNoteViewSet, ContactNoteNotificationViewSet, ContactNoteMonitoringViewSet

# Main contacts router
router = DefaultRouter()
router.register(r'', ContactViewSet)
router.register(r'groups', ContactGroupViewSet)
router.register(r'templates', ContactTemplateViewSet)
router.register(r'communications', CommunicationViewSet)
router.register(r'communication-templates', CommunicationTemplateViewSet)
router.register(r'communication-activities', CommunicationMonitoringViewSet)
router.register(r'lists', ContactListViewSet, basename='contactlist')

# Notes router
notes_router = DefaultRouter()
notes_router.register(r'', ContactNoteViewSet, basename='contact-notes')

# Note notifications and monitoring routers
note_notifications_router = DefaultRouter()
note_notifications_router.register(r'', ContactNoteNotificationViewSet, basename='contact-note-notifications')

note_monitoring_router = DefaultRouter()
note_monitoring_router.register(r'', ContactNoteMonitoringViewSet, basename='contact-note-monitoring')

# API v1 patterns for note operations
api_v1_patterns = [
    path('notes/notifications/', ContactNoteNotificationViewSet.as_view({'get': 'list'}), name='contact-note-notifications-api'),
    path('notes/monitoring/', ContactNoteMonitoringViewSet.as_view({'get': 'list'}), name='contact-note-monitoring-api'),
]

urlpatterns = [
    # Main contacts endpoints
    path('', include(router.urls)),
    
    # Note endpoints
    path('notes/', include(notes_router.urls)),
    path('note-notifications/', include(note_notifications_router.urls)),
    path('note-activities/', include(note_monitoring_router.urls)),
    
    # Special note endpoints
    path('notes/<int:pk>/download/', ContactNoteViewSet.as_view({'get': 'download_file'}), name='contact-note-download-file'),
    path('notes/<int:pk>/hard_delete/', ContactNoteViewSet.as_view({'delete': 'hard_delete'}), name='contact-note-hard-delete'),
    
    # API v1 endpoints
    path('api/v1/', include(api_v1_patterns)),
] 