from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Contact, ContactGroup, ContactTemplate, ContactMonitoring
from .serializers import ContactSerializer, ContactGroupSerializer, ContactTemplateSerializer
from .cache_manager import ContactCache
import logging

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
