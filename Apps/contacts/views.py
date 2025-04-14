from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Contact, ContactGroup, ContactTemplate, ContactMonitoring, Communication, CommunicationTemplate, CommunicationMonitoring, ContactList
from .models import ContactNote, ContactNoteNotification, ContactNoteMonitoring
from .serializers import ContactSerializer, ContactGroupSerializer, ContactTemplateSerializer, CommunicationSerializer, CommunicationTemplateSerializer, CommunicationMonitoringSerializer, ContactListSerializer
from .serializers import ContactNoteSerializer, ContactNoteNotificationSerializer, ContactNoteMonitoringSerializer
from .cache_manager import ContactCache, CommunicationCache, ContactNoteCache
import logging
from django.http import Http404, FileResponse
import os
from django.conf import settings

# Set up logger
logger = logging.getLogger(__name__)

# Create your views here.

class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for Contact model"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter contacts by organization and use cache if available"""
        organization_id = self.request.query_params.get('organization', None)
        
        if organization_id:
            try:
                # Convert to integer to ensure type consistency
                org_id = int(organization_id)
                
                # Try to get from cache first
                cached_contacts = ContactCache.get_organization_contacts(org_id)
                if cached_contacts is not None:
                    logger.debug(f"Retrieved {len(cached_contacts)} contacts from cache for org {org_id}")
                    # Since this is already serialized data, we'll handle it in the list method
                    # Just return the base query filtered by organization
                    return Contact.objects.filter(organization_id=org_id, is_active=True)
                
                # If not cached, get from DB and cache
                queryset = Contact.objects.filter(organization_id=org_id, is_active=True)
                # Cache the results for future requests
                ContactCache.set_organization_contacts(org_id, queryset=queryset)
                return queryset
            except (ValueError, TypeError):
                # Invalid organization ID format
                logger.warning(f"Invalid organization ID format: {organization_id}")
                return Contact.objects.none()
            
        return Contact.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        """Get single contact and log view activity"""
        instance = self.get_object()
        
        # Log the view activity
        ContactMonitoring.log_activity(
            contact=instance,
            user=request.user,
            activity_type='view',
            description='API view request',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Try to get from cache
        cached_contact = ContactCache.get_contact(instance.id)
        if cached_contact is not None and isinstance(cached_contact, dict):
            # If already serialized in cache, return directly
            logger.debug(f"Retrieved contact {instance.id} from cache")
            return Response(cached_contact)
        
        # Otherwise, serialize and return
        serializer = self.get_serializer(instance)
        # Store in cache for future requests
        ContactCache.set_contact(instance, include_related=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Set created_by and updated_by on create, and log activity"""
        contact = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        
        # Additional logging beyond what's in the model save method
        logger.info(
            f"Contact {contact.id} created by {self.request.user.username} "
            f"for organization {contact.organization_id}"
        )

    def perform_update(self, serializer):
        """Set updated_by on update and log activity"""
        contact = serializer.save(
            updated_by=self.request.user
        )
        
        # Create an activity record
        ContactMonitoring.log_activity(
            contact=contact,
            user=self.request.user,
            activity_type='update',
            description='API update',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT')
        )
        
        # Additional logging beyond what's in the model save method
        logger.info(
            f"Contact {contact.id} updated by {self.request.user.username} "
            f"for organization {contact.organization_id}"
        )

    def perform_destroy(self, instance):
        """Override destroy to use request data for monitoring"""
        instance.delete(
            user=self.request.user,
            request_meta=self.request.META
        )
        
        # Additional logging
        logger.info(
            f"Contact {instance.id} soft-deleted by {self.request.user.username} "
            f"for organization {instance.organization_id}"
        )

    @action(detail=True, methods=['delete'])
    def hard_delete(self, request, pk=None):
        """Hard delete endpoint"""
        instance = self.get_object()
        
        instance.hard_delete(
            user=request.user,
            request_meta=request.META
        )
        
        # Additional logging
        logger.info(
            f"Contact {pk} hard-deleted by {request.user.username} "
            f"for organization {instance.organization_id}"
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def refresh_cache(self, request):
        """Admin action to refresh contact cache"""
        organization_id = request.query_params.get('organization', None)
        
        if not organization_id:
            return Response(
                {"error": "Organization ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Convert organization_id to integer
        try:
            organization_id = int(organization_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Organization ID must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Refresh organization contacts cache
        ContactCache.invalidate_organization_contacts(organization_id)
        ContactCache.set_organization_contacts(organization_id)
        
        # Log the activity
        logger.info(
            f"Contact cache refreshed for organization {organization_id} "
            f"by {request.user.username}"
        )
        
        return Response(
            {"message": f"Cache refreshed for organization {organization_id}"},
            status=status.HTTP_200_OK
        )

    def list(self, request, *args, **kwargs):
        """List contacts with cache support"""
        organization_id = request.query_params.get('organization', None)
        
        if organization_id:
            try:
                # Convert to integer for cache key consistency
                org_id = int(organization_id)
                
                # Try to get from cache first
                cached_contacts = ContactCache.get_organization_contacts(org_id)
                if cached_contacts is not None:
                    logger.debug(f"Retrieved {len(cached_contacts)} contacts from cache for org {org_id}")
                    return Response(cached_contacts)
            except (ValueError, TypeError):
                # Invalid organization ID format
                logger.warning(f"Invalid organization ID format: {organization_id}")
                return Response(
                    {"error": "Organization ID must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # If not cached or no organization filter, continue with normal flow
        return super().list(request, *args, **kwargs)

class ContactGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactGroup model"""
    queryset = ContactGroup.objects.all()
    serializer_class = ContactGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter contact groups by organization"""
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            return ContactGroup.objects.filter(organization_id=organization_id)
        return ContactGroup.objects.all()

class ContactTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactTemplate model"""
    queryset = ContactTemplate.objects.all()
    serializer_class = ContactTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter templates by organization"""
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            return ContactTemplate.objects.filter(organization_id=organization_id)
        return ContactTemplate.objects.all()

    def perform_create(self, serializer):
        """Set created_by and updated_by on create"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(updated_by=self.request.user)

class CommunicationViewSet(viewsets.ModelViewSet):
    """ViewSet for Communication model"""
    queryset = Communication.objects.all()
    serializer_class = CommunicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter communications by organization, contact, or status"""
        queryset = Communication.objects.filter(is_active=True)
        
        # Filter by organization
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
            
            # Try to get from cache if organization filter is applied
            try:
                org_id = int(organization_id)
                cached_communications = CommunicationCache.get_organization_communications(org_id)
                if cached_communications is not None:
                    logger.debug(f"Retrieved {len(cached_communications)} communications from cache for org {org_id}")
                    # Will return cached data in list method
                    return queryset
            except (ValueError, TypeError):
                # Invalid organization ID format
                logger.warning(f"Invalid organization ID format: {organization_id}")
                return Communication.objects.none()
        
        # Filter by contact
        contact_id = self.request.query_params.get('contact', None)
        if contact_id:
            queryset = queryset.filter(contact_id=contact_id)
            
            # Try to get from cache if contact filter is applied
            try:
                contact_id = int(contact_id)
                cached_communications = CommunicationCache.get_contact_communications(contact_id)
                if cached_communications is not None:
                    logger.debug(f"Retrieved {len(cached_communications)} communications from cache for contact {contact_id}")
                    # Will return cached data in list method
                    return queryset
            except (ValueError, TypeError):
                # Invalid contact ID format
                logger.warning(f"Invalid contact ID format: {contact_id}")
                return Communication.objects.none()
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        # Filter by communication_type
        comm_type = self.request.query_params.get('type', None)
        if comm_type:
            queryset = queryset.filter(communication_type=comm_type)
            
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Get single communication and log view activity"""
        instance = self.get_object()
        
        # Log the view activity
        CommunicationMonitoring.log_activity(
            communication=instance,
            user=request.user,
            activity_type='view',
            description='API view request',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Try to get from cache
        cached_communication = CommunicationCache.get_communication(instance.id)
        if cached_communication is not None and isinstance(cached_communication, dict):
            # If already serialized in cache, return directly
            logger.debug(f"Retrieved communication {instance.id} from cache")
            return Response(cached_communication)
        
        # Otherwise, serialize and return
        serializer = self.get_serializer(instance)
        # Store in cache for future requests
        CommunicationCache.set_communication(instance, include_related=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Set created_by and updated_by on create, and log activity"""
        communication = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        
        # Additional logging beyond what's in the model save method
        logger.info(
            f"Communication {communication.id} created by {self.request.user.username} "
            f"for organization {communication.organization_id}"
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update and log activity"""
        communication = serializer.save(
            updated_by=self.request.user
        )
        
        # Create an activity record
        CommunicationMonitoring.log_activity(
            communication=communication,
            user=self.request.user,
            activity_type='update',
            description='API update',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT')
        )
        
        # Additional logging beyond what's in the model save method
        logger.info(
            f"Communication {communication.id} updated by {self.request.user.username} "
            f"for organization {communication.organization_id}"
        )
    
    def perform_destroy(self, instance):
        """Override destroy to use request data for monitoring"""
        instance.delete(
            user=self.request.user,
            request_meta=self.request.META
        )
        
        # Additional logging
        logger.info(
            f"Communication {instance.id} soft-deleted by {self.request.user.username} "
            f"for organization {instance.organization_id}"
        )
    
    @action(detail=True, methods=['delete'])
    def hard_delete(self, request, pk=None):
        """Hard delete endpoint"""
        instance = self.get_object()
        
        instance.hard_delete(
            user=request.user,
            request_meta=request.META
        )
        
        # Additional logging
        logger.info(
            f"Communication {pk} hard-deleted by {request.user.username} "
            f"for organization {instance.organization_id}"
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def refresh_cache(self, request):
        """Admin action to refresh communication cache"""
        organization_id = request.query_params.get('organization', None)
        
        if not organization_id:
            return Response(
                {"error": "Organization ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Convert organization_id to integer
        try:
            organization_id = int(organization_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Organization ID must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Refresh organization communications cache
        CommunicationCache.invalidate_organization_communications(organization_id)
        CommunicationCache.set_organization_communications(organization_id)
        
        # Log the activity
        logger.info(
            f"Communication cache refreshed for organization {organization_id} "
            f"by {request.user.username}"
        )
        
        return Response(
            {"message": f"Cache refreshed for organization {organization_id}"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send a communication"""
        communication = self.get_object()
        
        # Validate that communication is in draft state
        if communication.status not in ['draft', 'scheduled']:
            return Response(
                {"error": "Only draft or scheduled communications can be sent"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update status to sending
        communication.status = 'sending'
        communication.save(
            user=request.user,
            request_meta=request.META
        )
        
        # Log the send activity
        CommunicationMonitoring.log_activity(
            communication=communication,
            user=request.user,
            activity_type='send',
            description='API send request',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # In a real application, you would add background task to send the communication
        # For demonstration purposes, update to sent state immediately
        communication.status = 'sent'
        communication.save(
            user=request.user,
            request_meta=request.META
        )
        
        return Response(
            {"message": "Communication sent successfully"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """Schedule a communication for later delivery"""
        communication = self.get_object()
        
        # Validate that communication is in draft state
        if communication.status != 'draft':
            return Response(
                {"error": "Only draft communications can be scheduled"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get scheduled_at from request
        scheduled_at = request.data.get('scheduled_at', None)
        if not scheduled_at:
            return Response(
                {"error": "Scheduled date and time is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update status to scheduled
        communication.status = 'scheduled'
        communication.scheduled_at = scheduled_at
        communication.save(
            user=request.user,
            request_meta=request.META
        )
        
        # Log the schedule activity
        CommunicationMonitoring.log_activity(
            communication=communication,
            user=request.user,
            activity_type='schedule',
            description='API schedule request',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        return Response(
            {"message": "Communication scheduled successfully"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scheduled or draft communication"""
        communication = self.get_object()
        
        # Validate that communication can be cancelled
        if communication.status not in ['draft', 'scheduled']:
            return Response(
                {"error": "Only draft or scheduled communications can be cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update status to cancelled
        communication.status = 'cancelled'
        communication.save(
            user=request.user,
            request_meta=request.META
        )
        
        # Log the cancel activity
        CommunicationMonitoring.log_activity(
            communication=communication,
            user=request.user,
            activity_type='cancel',
            description='API cancel request',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        return Response(
            {"message": "Communication cancelled successfully"},
            status=status.HTTP_200_OK
        )
    
    def list(self, request, *args, **kwargs):
        """List communications with cache support"""
        organization_id = request.query_params.get('organization', None)
        contact_id = request.query_params.get('contact', None)
        
        if organization_id:
            try:
                # Convert to integer for cache key consistency
                org_id = int(organization_id)
                
                # Try to get from cache first
                cached_communications = CommunicationCache.get_organization_communications(org_id)
                if cached_communications is not None:
                    logger.debug(f"Retrieved {len(cached_communications)} communications from cache for org {org_id}")
                    return Response(cached_communications)
            except (ValueError, TypeError):
                # Invalid organization ID format
                logger.warning(f"Invalid organization ID format: {organization_id}")
                return Response(
                    {"error": "Organization ID must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif contact_id:
            try:
                # Convert to integer for cache key consistency
                contact_id = int(contact_id)
                
                # Try to get from cache first
                cached_communications = CommunicationCache.get_contact_communications(contact_id)
                if cached_communications is not None:
                    logger.debug(f"Retrieved {len(cached_communications)} communications from cache for contact {contact_id}")
                    return Response(cached_communications)
            except (ValueError, TypeError):
                # Invalid contact ID format
                logger.warning(f"Invalid contact ID format: {contact_id}")
                return Response(
                    {"error": "Contact ID must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # If not cached or no organization/contact filter, continue with normal flow
        return super().list(request, *args, **kwargs)

class CommunicationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for CommunicationTemplate model"""
    queryset = CommunicationTemplate.objects.all()
    serializer_class = CommunicationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter templates by organization"""
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            return CommunicationTemplate.objects.filter(organization_id=organization_id, is_active=True)
        return CommunicationTemplate.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        """Set created_by and updated_by on create"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(
            updated_by=self.request.user
        )
    
    def perform_destroy(self, instance):
        """Override destroy to use soft delete"""
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def create_communication(self, request, pk=None):
        """Create a communication from template"""
        template = self.get_object()
        
        # Get contact ID from request
        contact_id = request.data.get('contact', None)
        if not contact_id:
            return Response(
                {"error": "Contact ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get contact
        try:
            contact = Contact.objects.get(id=contact_id)
        except Contact.DoesNotExist:
            return Response(
                {"error": "Contact not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Create communication
        try:
            communication = template.create_communication(contact, request.user)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Serialize and return
        serializer = CommunicationSerializer(communication)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

class CommunicationMonitoringViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for CommunicationMonitoring model"""
    queryset = CommunicationMonitoring.objects.all()
    serializer_class = CommunicationMonitoringSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter monitoring records by organization, communication, or user"""
        queryset = CommunicationMonitoring.objects.all()
        
        # Filter by organization
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
            
        # Filter by communication
        communication_id = self.request.query_params.get('communication', None)
        if communication_id:
            queryset = queryset.filter(communication_id=communication_id)
            
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Filter by activity type
        activity_type = self.request.query_params.get('activity_type', None)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
            
        return queryset

class ContactListViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactList model"""
    queryset = ContactList.objects.all()
    serializer_class = ContactListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter contact lists by organization"""
        # Start with only active lists
        queryset = ContactList.objects.filter(is_active=True)
        
        # Get the user's organization
        user_org = None
        if hasattr(self.request.user, 'team_memberships'):
            # Get the first active team membership's organization
            team_membership = self.request.user.team_memberships.filter(is_active=True).first()
            if team_membership:
                user_org = team_membership.team.department.organization
        
        # Filter by organization from URL parameters if provided
        organization_id = self.request.query_params.get('organization', None)
        
        if organization_id:
            try:
                # Convert to integer to ensure type consistency
                org_id = int(organization_id)
                queryset = queryset.filter(organization_id=org_id)
                
                # If user doesn't belong to this organization, return empty queryset
                if user_org and user_org.id != org_id:
                    return ContactList.objects.none()
            except (ValueError, TypeError):
                # If organization_id is invalid, return empty queryset
                return ContactList.objects.none()
        elif user_org:
            # If no specific organization requested, filter to user's organization
            queryset = queryset.filter(organization=user_org)
                
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by and updated_by on create"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(
            updated_by=self.request.user
        )
    
    def perform_destroy(self, instance):
        """Override destroy to use soft delete"""
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['delete'])
    def hard_delete(self, request, pk=None):
        """Hard delete a contact list"""
        instance = self.get_object()
        # Use the model's delete method with hard_delete=True instead of default delete()
        instance.delete(hard_delete=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ContactNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactNote model"""
    queryset = ContactNote.objects.all()
    serializer_class = ContactNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter notes by contact, organization, is_active"""
        queryset = ContactNote.objects.filter(is_active=True)
        
        # Filter by contact
        contact_id = self.request.query_params.get('contact', None)
        if contact_id:
            queryset = queryset.filter(contact_id=contact_id)
            
            # Try to get from cache if contact filter is applied
            try:
                contact_id = int(contact_id)
                
                # Use the cache for list view
                if self.action == 'list':
                    cached_notes = ContactNoteCache.get_contact_notes(contact_id)
                    if cached_notes is not None:
                        logger.debug(f"Retrieved {len(cached_notes)} notes from cache for contact {contact_id}")
                        return queryset
            except (ValueError, TypeError):
                # Invalid contact ID format
                logger.warning(f"Invalid contact ID format: {contact_id}")
                return ContactNote.objects.none()
        
        # Filter by organization
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
            
        # Filter by is_private
        include_private = self.request.query_params.get('include_private', 'false').lower() == 'true'
        if not include_private:
            queryset = queryset.filter(is_private=False)
            
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Get single note and log view activity"""
        instance = self.get_object()
        
        # Log the view activity
        ContactNoteMonitoring.log_activity(
            note=instance,
            user=request.user,
            activity_type='view',
            description='API view request',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            organization=instance.organization
        )
        
        # Try to get from cache
        cached_note = ContactNoteCache.get_note(instance.id)
        if isinstance(cached_note, dict):
            # If already serialized in cache, return directly
            logger.debug(f"Retrieved note {instance.id} from cache")
            return Response(cached_note)
        
        # Otherwise, serialize and return
        serializer = self.get_serializer(instance)
        # Store in cache for future requests
        ContactNoteCache.set_note(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Set created_by on create and log activity"""
        note = serializer.save(
            created_by=self.request.user
        )
        
        # Log the activity
        ContactNoteMonitoring.log_activity(
            note=note,
            user=self.request.user,
            activity_type='create',
            description='Note created via API',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT'),
            organization=note.organization
        )
        
        # Cache the note
        ContactNoteCache.set_note(note)
        
        # Invalidate contact notes cache
        list_key = ContactNoteCache.get_note_list_key(note.contact_id)
        ContactNoteCache.delete_note_cache(note.id, note.contact_id)
        
        # Log creation
        logger.info(
            f"Note {note.id} created by {self.request.user.username} "
            f"for contact {note.contact_id} in organization {note.organization_id}"
        )
    
    def perform_update(self, serializer):
        """Update the note and log activity"""
        note = serializer.save()
        
        # Log the activity
        ContactNoteMonitoring.log_activity(
            note=note,
            user=self.request.user,
            activity_type='update',
            description='Note updated via API',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT'),
            organization=note.organization
        )
        
        # Update cache
        ContactNoteCache.set_note(note)
        
        # Invalidate contact notes cache
        ContactNoteCache.delete_note_cache(note.id, note.contact_id)
        
        # Log update
        logger.info(
            f"Note {note.id} updated by {self.request.user.username} "
            f"for contact {note.contact_id} in organization {note.organization_id}"
        )
    
    def perform_destroy(self, instance):
        """Soft delete note and log activity"""
        instance.delete(
            user=self.request.user,
            request_meta=self.request.META
        )
        
        # Invalidate cache
        ContactNoteCache.delete_note_cache(instance.id, instance.contact_id)
        
        # Log deletion
        logger.info(
            f"Note {instance.id} soft-deleted by {self.request.user.username} "
            f"for contact {instance.contact_id} in organization {instance.organization_id}"
        )
    
    @action(detail=True, methods=['delete'])
    def hard_delete(self, request, pk=None):
        """Hard delete endpoint"""
        instance = self.get_object()
        contact_id = instance.contact_id
        
        instance.hard_delete(
            user=request.user,
            request_meta=request.META
        )
        
        # Invalidate cache
        ContactNoteCache.delete_note_cache(int(pk), contact_id)
        
        # Log the hard deletion
        logger.info(
            f"Note {pk} hard-deleted by {request.user.username} "
            f"for contact {contact_id}"
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def download_file(self, request, pk=None):
        """Download the file attachment"""
        note = self.get_object()
        
        if not note.file_attachment:
            return Response(
                {"error": "No file attachment found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log file download activity
        ContactNoteMonitoring.log_activity(
            note=note,
            user=request.user,
            activity_type='attachment_view',
            description='File download',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            organization=note.organization
        )
        
        # Get file path
        file_path = note.file_attachment.path
        
        # Check if file exists
        if not os.path.exists(file_path):
            return Response(
                {"error": "File not found on server"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Open the file in binary mode and return as response
        file_handle = open(file_path, 'rb')
        response = FileResponse(file_handle, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
    
    def list(self, request, *args, **kwargs):
        """List notes with cache support"""
        contact_id = request.query_params.get('contact', None)
        
        if contact_id:
            try:
                # Convert to integer for cache key consistency
                contact_id = int(contact_id)
                
                # Try to get from cache
                cached_notes = ContactNoteCache.get_contact_notes(contact_id)
                if cached_notes is not None:
                    # Serialize the notes
                    serializer = self.get_serializer(cached_notes, many=True)
                    return Response(serializer.data)
            except (ValueError, TypeError):
                # Invalid contact ID format
                logger.warning(f"Invalid contact ID format: {contact_id}")
                return Response(
                    {"error": "Contact ID must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # If not cached or no contact filter, continue with normal flow
        return super().list(request, *args, **kwargs)

class ContactNoteNotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactNoteNotification model"""
    queryset = ContactNoteNotification.objects.all()
    serializer_class = ContactNoteNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter notifications by user, note, is_read"""
        queryset = ContactNoteNotification.objects.all()
        
        # Only show notifications for current user by default
        user_id = self.request.query_params.get('user', self.request.user.id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by note
        note_id = self.request.query_params.get('note', None)
        if note_id:
            queryset = queryset.filter(note_id=note_id)
        
        # Filter by is_read
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            is_read = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create a notification and track metadata"""
        notification = serializer.save()
        
        # Log creation
        logger.info(
            f"Notification {notification.id} created for user {notification.user_id} "
            f"for note {notification.note_id}"
        )
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({"status": "success"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications for current user as read"""
        user_id = request.user.id
        
        # Get all unread notifications for the user
        unread = ContactNoteNotification.objects.filter(user_id=user_id, is_read=False)
        count = unread.count()
        
        # Mark all as read
        unread.update(is_read=True)
        
        return Response({"status": "success", "count": count}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for current user"""
        user_id = request.user.id
        count = ContactNoteNotification.objects.filter(user_id=user_id, is_read=False).count()
        
        return Response({"count": count}, status=status.HTTP_200_OK)

class ContactNoteMonitoringViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ContactNoteMonitoring model (read-only)"""
    queryset = ContactNoteMonitoring.objects.all()
    serializer_class = ContactNoteMonitoringSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter monitoring records by note, user, activity_type"""
        queryset = ContactNoteMonitoring.objects.all()
        
        # Filter by note
        note_id = self.request.query_params.get('note', None)
        if note_id:
            queryset = queryset.filter(note_id=note_id)
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by activity_type
        activity_type = self.request.query_params.get('activity_type', None)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        # Filter by organization
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        return queryset.order_by('-created_at')
