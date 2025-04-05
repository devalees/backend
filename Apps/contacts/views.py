from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Contact, ContactGroup, ContactTemplate
from .serializers import ContactSerializer, ContactGroupSerializer, ContactTemplateSerializer

# Create your views here.

class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for Contact model"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter contacts by organization"""
        organization_id = self.request.query_params.get('organization', None)
        if organization_id:
            return Contact.objects.filter(organization_id=organization_id)
        return Contact.objects.all()

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
