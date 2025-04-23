from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Contact, ContactGroup, ContactTemplate, ContactMonitoring, Communication, CommunicationTemplate, CommunicationMonitoring, ContactList
from .models import ContactNote, ContactNoteNotification, ContactNoteMonitoring
from .serializers import ContactSerializer, ContactGroupSerializer, ContactTemplateSerializer, CommunicationSerializer, CommunicationTemplateSerializer, CommunicationMonitoringSerializer, ContactListSerializer
from .serializers import ContactNoteSerializer, ContactNoteNotificationSerializer, ContactNoteMonitoringSerializer
from .cache_manager import ContactCache, CommunicationCache, ContactNoteCache
from .throttling import ContactRateThrottle, ContactCreateRateThrottle, ContactNoteRateThrottle, get_rate_limit_headers
# Import filtering utils
from Apps.filtering.filters import apply_filters, get_available_filters
from Apps.filtering.aggregations import apply_aggregations, get_available_aggregations
# Import RBAC permissions
from Apps.rbac.permissions import RBACPermission
import logging
from django.http import Http404, FileResponse
import os
from django.conf import settings
from django.utils import timezone

# Set up logger
logger = logging.getLogger(__name__)

@extend_schema_view(
    list=extend_schema(
        summary="List contacts",
        description="Get a list of all contacts for the authenticated user's organization",
        parameters=[
            OpenApiParameter(
                name="organization",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter contacts by organization ID"
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search contacts by name or email"
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order contacts by field (prefix with - for descending)"
            ),
            # Add documentation for filtering parameters
            OpenApiParameter(
                name="filters",
                type=OpenApiTypes.OBJECT,
                location=OpenApiParameter.QUERY,
                description="JSON-formatted filter criteria"
            ),
            # Add documentation for aggregation parameters
            OpenApiParameter(
                name="aggregate",
                type=OpenApiTypes.OBJECT,
                location=OpenApiParameter.QUERY,
                description="JSON-formatted aggregation criteria"
            )
        ],
        responses={
            200: ContactSerializer(many=True),
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            429: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                "Success Response",
                value=[{
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "organization": 1,
                    "organization_name": "Example Org",
                    "is_active": True
                }]
            )
        ]
    ),
    create=extend_schema(
        summary="Create contact",
        description="Create a new contact",
        request=ContactSerializer,
        responses={
            201: ContactSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            429: OpenApiTypes.OBJECT
        }
    ),
    retrieve=extend_schema(
        summary="Get contact",
        description="Get a specific contact by ID",
        responses={
            200: ContactSerializer,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            429: OpenApiTypes.OBJECT
        }
    ),
    update=extend_schema(
        summary="Update contact",
        description="Update a specific contact",
        request=ContactSerializer,
        responses={
            200: ContactSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            429: OpenApiTypes.OBJECT
        }
    ),
    partial_update=extend_schema(
        summary="Partially update contact",
        description="Partially update a specific contact",
        request=ContactSerializer,
        responses={
            200: ContactSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            429: OpenApiTypes.OBJECT
        }
    ),
    destroy=extend_schema(
        summary="Delete contact",
        description="Delete a specific contact",
        responses={
            204: None,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            429: OpenApiTypes.OBJECT
        }
    )
)
class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for Contact model"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermission]
    throttle_classes = [ContactRateThrottle]
    
    def get_throttles(self):
        """Get appropriate throttle class based on action"""
        if self.action == 'create':
            return [ContactCreateRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        """
        Filter contacts by organization and apply filtering capabilities.
        Uses cache when appropriate.
        """
        queryset = Contact.objects.filter(is_active=True)
        
        # Apply RBAC filtering - automatically filter to user's organization(s)
        # The RBACPermission will restrict access, but we also filter here for efficiency
        
        # Get organizations the user belongs to through team membership
        from Apps.entity.models import TeamMember
        user_orgs = TeamMember.objects.filter(
            user=self.request.user,
            is_active=True
        ).values_list('team__department__organization', flat=True).distinct()
        
        # Filter contacts by user's organizations
        queryset = queryset.filter(organization__in=user_orgs)
        
        # Apply filters from request
        if 'filters' in self.request.query_params:
            queryset = apply_filters(queryset, self.request.query_params.get('filters'))
            
        # Default organization filter if not already applied
        if 'organization' in self.request.query_params:
            try:
                org_id = int(self.request.query_params.get('organization'))
                # Verify user belongs to this organization
                if org_id in user_orgs:
                    queryset = queryset.filter(organization_id=org_id)
                    
                    # Try to get from cache if no other filters are applied
                    if len(self.request.query_params) == 1:
                        cached_contacts = ContactCache.get_organization_contacts(org_id)
                        if cached_contacts is not None:
                            logger.debug(f"Retrieved {len(cached_contacts)} contacts from cache for org {org_id}")
                            # Return DB queryset - we'll handle the cache in list()
                            return queryset
                        
                        # If not cached, cache the results for future requests
                        ContactCache.set_organization_contacts(org_id, queryset=queryset)
                else:
                    # User doesn't belong to the requested organization
                    logger.warning(f"User {self.request.user.id} attempted to access contacts from organization {org_id} to which they don't belong")
                    return Contact.objects.none()
            except (ValueError, TypeError):
                logger.warning(f"Invalid organization ID format: {self.request.query_params.get('organization')}")
                return Contact.objects.none()
            
        return queryset

    def list(self, request, *args, **kwargs):
        """
        List contacts with rate limit headers and support for aggregations
        """
        # Check if we're doing aggregation
        if 'aggregate' in request.query_params:
            queryset = self.get_queryset()
            aggregation_results = apply_aggregations(queryset, request.query_params.get('aggregate'))
            return Response(aggregation_results)
            
        # Standard list view with rate limit headers
        response = super().list(request, *args, **kwargs)
        rate_limit_headers = get_rate_limit_headers(request, self)
        for key, value in rate_limit_headers.items():
            response.headers[key] = value
        return response
            
    @action(detail=False, methods=['get'])
    def available_filters(self, request):
        """Return the available filters for Contact model"""
        filters = get_available_filters(Contact)
        return Response(filters)
        
    @action(detail=False, methods=['get'])
    def available_aggregations(self, request):
        """Return the available aggregations for Contact model"""
        aggregations = get_available_aggregations(Contact)
        return Response(aggregations)

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
            response = Response(cached_contact)
            # Replace response.headers.update with individual header setting
            rate_limit_headers = get_rate_limit_headers(request, self)
            for key, value in rate_limit_headers.items():
                response.headers[key] = value
            return response
        
        # Otherwise, serialize and return
        serializer = self.get_serializer(instance)
        # Store in cache for future requests
        ContactCache.set_contact(instance, include_related=True)
        response = Response(serializer.data)
        # Replace response.headers.update with individual header setting
        rate_limit_headers = get_rate_limit_headers(request, self)
        for key, value in rate_limit_headers.items():
            response.headers[key] = value
        return response

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

class ContactGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactGroup model"""
    queryset = ContactGroup.objects.all()
    serializer_class = ContactGroupSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermission]

    def get_queryset(self):
        """
        Filter contact groups with RBAC and filtering support
        """
        queryset = ContactGroup.objects.filter(is_active=True)
        
        # Superusers can see all contact groups
        if self.request.user.is_superuser:
            return queryset
            
        # Apply filters from query parameters
        if 'filters' in self.request.query_params:
            queryset = apply_filters(queryset, self.request.query_params.get('filters'))
            
        # Default organization filter if not already applied
        if 'organization' in self.request.query_params:
            try:
                org_id = int(self.request.query_params.get('organization'))
                queryset = queryset.filter(organization_id=org_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid organization ID format: {self.request.query_params.get('organization')}")
                return ContactGroup.objects.none()
                
        return queryset
        
    def list(self, request, *args, **kwargs):
        """List contact groups with aggregation support"""
        # Check if we're doing aggregation
        if 'aggregate' in request.query_params:
            queryset = self.get_queryset()
            aggregation_results = apply_aggregations(queryset, request.query_params.get('aggregate'))
            return Response(aggregation_results)
            
        # Standard list response
        return super().list(request, *args, **kwargs)
        
    def perform_create(self, serializer):
        """Set created_by and updated_by on create"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(updated_by=self.request.user)
        
    @action(detail=False, methods=['get'])
    def available_filters(self, request):
        """Return the available filters for ContactGroup model"""
        filters = get_available_filters(ContactGroup)
        return Response(filters)
        
    @action(detail=False, methods=['get'])
    def available_aggregations(self, request):
        """Return the available aggregations for ContactGroup model"""
        aggregations = get_available_aggregations(ContactGroup)
        return Response(aggregations)

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
        
        # Superusers can see all contact lists
        if self.request.user.is_superuser:
            return queryset
            
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
        """Filter notes by organization and contact"""
        queryset = ContactNote.objects.filter(is_active=True).select_related(
            'contact', 'organization', 'created_by'
        )
        
        organization_id = self.request.query_params.get('organization', None)
        contact_id = self.request.query_params.get('contact', None)
        
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        if contact_id:
            queryset = queryset.filter(contact_id=contact_id)
            
            # Try to get from cache if filtering by contact
            try:
                cached_notes = ContactNoteCache.get_contact_notes(int(contact_id))
                if cached_notes is not None:
                    logger.debug(f"Retrieved notes from cache for contact {contact_id}")
                    return queryset  # Return DB queryset since we'll use cached data in list()
            except (ValueError, TypeError):
                logger.warning(f"Invalid contact ID format: {contact_id}")
                
        return queryset

    def list(self, request, *args, **kwargs):
        """List notes with cache support"""
        contact_id = request.query_params.get('contact', None)
        organization_id = request.query_params.get('organization', None)
        
        if contact_id and organization_id:
            try:
                contact_id = int(contact_id)
                # Try to get from cache first
                cached_notes = ContactNoteCache.get_contact_notes(contact_id)
                if cached_notes is not None:
                    logger.debug(f"Retrieved notes from cache for contact {contact_id}")
                    return Response(cached_notes)
            except (ValueError, TypeError):
                logger.warning(f"Invalid contact ID format: {contact_id}")
                return Response(
                    {"error": "Contact ID must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # If not cached or no contact filter, continue with normal flow
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Get single note with cache support"""
        instance = self.get_object()
        
        # Try to get from cache
        cached_note = ContactNoteCache.get_note(instance.id)
        if cached_note is not None and isinstance(cached_note, dict):
            logger.debug(f"Retrieved note {instance.id} from cache")
            return Response(cached_note)
        
        # Log the view activity
        ContactNoteMonitoring.log_activity(
            note=instance,
            user=request.user,
            activity_type='view',
            description='Note viewed via API',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            organization=instance.organization
        )
        
        # Otherwise, serialize and return
        serializer = self.get_serializer(instance)
        # Store in cache for future requests
        ContactNoteCache.set_note(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create note and handle file attachments"""
        # Get file attachment if present
        file_attachment = self.request.FILES.get('file_attachment', None)
        
        # Create the note
        note = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            file_attachment=file_attachment
        )
        
        # Set file type if file was attached
        if file_attachment:
            extension = os.path.splitext(file_attachment.name)[1].lower().replace('.', '')
            note.file_type = extension
            note.save()
            
            # Log file attachment
            ContactNoteMonitoring.log_activity(
                note=note,
                user=self.request.user,
                activity_type='attachment_upload',
                description=f'File uploaded: {file_attachment.name}',
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT'),
                organization=note.organization
            )
        
        # Create monitoring record
        ContactNoteMonitoring.log_activity(
            note=note,
            user=self.request.user,
            activity_type='create',
            description='Note created via API',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT'),
            organization=note.organization
        )
        
        # Process mentions and create notifications
        self._process_mentions(note)
        
        # Cache the new note
        ContactNoteCache.set_note(note)
        # Invalidate contact notes cache
        ContactNoteCache.invalidate_contact_notes(note.contact_id)
        
        logger.info(f"Note {note.id} created for contact {note.contact_id}")

    def _process_mentions(self, note):
        """Process @mentions in note content and create notifications"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Simple @username mention detection
        mentioned_usernames = [
            word[1:] for word in note.content.split() 
            if word.startswith('@') and len(word) > 1
        ]
        
        # Create notifications for mentioned users
        for username in mentioned_usernames:
            try:
                user = User.objects.get(username=username)
                ContactNoteNotification.objects.create(
                    note=note,
                    user=user,
                    notification_type='mention',
                    message=f"You were mentioned in a note by {note.created_by.username}"
                )
                logger.info(f"Created mention notification for user {username} in note {note.id}")
            except User.DoesNotExist:
                logger.warning(f"Mentioned user {username} not found")
                continue

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
            activity_type='attachment_download',
            description='File downloaded',
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
        
        logger.info(f"File downloaded from note {note.id} by user {request.user.username}")
        return response

    def perform_update(self, serializer):
        """Update the note and log activity"""
        note = serializer.save(updated_by=self.request.user)
        
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
        
        # Process mentions for any new @mentions
        self._process_mentions(note)
        
        # Update cache
        ContactNoteCache.set_note(note)
        # Invalidate contact notes cache
        ContactNoteCache.delete_note_cache(note.id, note.contact_id)
        
        logger.info(f"Note {note.id} updated by {self.request.user.username}")
    
    def perform_destroy(self, serializer):
        """Soft delete note and log activity"""
        instance = self.get_object()
        
        # Log the activity before deletion
        ContactNoteMonitoring.log_activity(
            note=instance,
            user=self.request.user,
            activity_type='soft_delete',
            description='Note soft-deleted via API',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT'),
            organization=instance.organization
        )
        
        # Soft delete
        instance.is_active = False
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()
        
        # Invalidate caches
        ContactNoteCache.delete_note_cache(instance.id, instance.contact_id)
        
        logger.info(f"Note {instance.id} soft-deleted by {self.request.user.username}")
    
    @action(detail=True, methods=['delete'])
    def hard_delete(self, request, pk=None):
        """Permanently delete a note"""
        instance = self.get_object()
        
        # Log the activity before deletion
        ContactNoteMonitoring.log_activity(
            note=instance,
            user=request.user,
            activity_type='hard_delete',
            description='Note permanently deleted via API',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            organization=instance.organization
        )
        
        # Store IDs before deletion
        note_id = instance.id
        contact_id = instance.contact_id
        
        # Delete file if exists
        if instance.file_attachment:
            try:
                instance.file_attachment.delete(save=False)
            except Exception as e:
                logger.error(f"Error deleting file for note {note_id}: {str(e)}")
        
        # Hard delete the instance using the model's hard_delete method
        instance.hard_delete(user=request.user, request_meta=request.META)
        
        # Invalidate caches
        ContactNoteCache.delete_note_cache(note_id, contact_id)
        
        logger.info(f"Note {note_id} permanently deleted by {request.user.username}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class ContactNoteNotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactNoteNotification model"""
    queryset = ContactNoteNotification.objects.all()
    serializer_class = ContactNoteNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter notifications by user"""
        return ContactNoteNotification.objects.filter(
            user=self.request.user
        ).select_related('note', 'user').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """List notifications with pagination and filters"""
        queryset = self.get_queryset()
        
        # Filter by read status
        is_read = request.query_params.get('is_read', None)
        if is_read is not None:
            is_read = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read)
            
        # Filter by notification type
        notification_type = request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
            
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create notification"""
        notification = serializer.save()
        logger.info(f"Notification created for user {notification.user.username}")

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user"""
        self.get_queryset().update(is_read=True)
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

class ContactNoteMonitoringViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ContactNoteMonitoring model (read-only)"""
    queryset = ContactNoteMonitoring.objects.all()
    serializer_class = ContactNoteMonitoringSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter monitoring records by organization and note"""
        queryset = ContactNoteMonitoring.objects.all().select_related(
            'note', 'user', 'note__contact', 'note__organization'
        ).order_by('-created_at')
        
        # Filter by organization
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            queryset = queryset.filter(note__organization_id=organization_id)
            
        # Filter by note
        note_id = self.request.query_params.get('note', None)
        if note_id:
            queryset = queryset.filter(note_id=note_id)
            
        # Filter by activity type
        activity_type = self.request.query_params.get('activity_type', None)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
            
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
            
        return queryset

    def list(self, request, *args, **kwargs):
        """List monitoring records with pagination"""
        queryset = self.get_queryset()
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def activity_summary(self, request):
        """Get summary of activities by type"""
        organization_id = request.query_params.get('organization', None)
        if not organization_id:
            return Response(
                {"error": "Organization ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        queryset = self.get_queryset().filter(note__organization_id=organization_id)
        
        # Get counts by activity type
        from django.db.models import Count
        summary = queryset.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response(summary)

    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """Get activity summary by user"""
        organization_id = request.query_params.get('organization', None)
        if not organization_id:
            return Response(
                {"error": "Organization ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        queryset = self.get_queryset().filter(note__organization_id=organization_id)
        
        # Get counts by user
        from django.db.models import Count
        summary = queryset.values(
            'user__id', 'user__username'
        ).annotate(
            activity_count=Count('id')
        ).order_by('-activity_count')
        
        return Response(summary)
