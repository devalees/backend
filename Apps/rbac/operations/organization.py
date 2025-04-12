from typing import Dict, List, Optional, Union
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from Apps.rbac.models import OrganizationContext
from Apps.entity.models import Organization

class OrganizationOperations:
    """Operations for managing organizations"""

    @classmethod
    def create_organization(cls, name: str, description: str, 
                          metadata: Optional[Dict] = None, 
                          parent: Optional[OrganizationContext] = None) -> OrganizationContext:
        """Create a new organization"""
        # If parent is provided, validate it's an OrganizationContext
        if parent and not isinstance(parent, OrganizationContext):
            raise ValidationError("Parent must be an OrganizationContext instance")
        
        try:
            # Create new base organization if no parent
            if not parent:
                entity_org = Organization.objects.create(
                    name=name,
                    description=description,
                    status=Organization.Status.ACTIVE
                )
            else:
                # For child organizations, use parent's organization
                if not hasattr(parent, 'organization') or not parent.organization:
                    raise ValidationError("Parent organization is missing or invalid")
                entity_org = parent.organization
                
            # Create and validate the organization context
            org = OrganizationContext(
                name=name,
                description=description,
                metadata=metadata or {},
                parent=parent,
                organization=entity_org
            )
            
            # Validate the organization context
            org.full_clean()
            
            # If validation passes, save the organization
            org.save()
            return org
            
        except ValidationError as e:
            # Clean up the created organization if we created one and an error occurred
            if not parent and 'entity_org' in locals():
                entity_org.delete()
            raise e

    @classmethod
    def update_organization(cls, org_id: int, **update_data) -> OrganizationContext:
        """Update an existing organization"""
        org = OrganizationContext.objects.get(id=org_id)
        
        # Update entity organization if name or description changed
        if 'name' in update_data or 'description' in update_data:
            entity_org = org.organization
            if 'name' in update_data:
                entity_org.name = update_data['name']
            if 'description' in update_data:
                entity_org.description = update_data['description']
            entity_org.save()
        
        # Update organization context
        for field, value in update_data.items():
            setattr(org, field, value)
        org.full_clean()
        org.save()
        return org

    @classmethod
    def bulk_create_organizations(cls, orgs_data: List[Dict]) -> List[OrganizationContext]:
        """Create multiple organizations at once"""
        orgs = []
        with transaction.atomic():
            for data in orgs_data:
                org = cls.create_organization(**data)
                orgs.append(org)
        return orgs

    @classmethod
    def transfer_organization(cls, org_id: int, new_parent_id: int) -> OrganizationContext:
        """Transfer organization to a new parent"""
        org = OrganizationContext.objects.get(id=org_id)
        new_parent = OrganizationContext.objects.get(id=new_parent_id)
        
        # Validate no circular reference
        if org.id in [p.id for p in new_parent.get_all_parents()]:
            raise ValidationError("Cannot create circular reference in organization hierarchy")
        
        # Validate same base organization
        if org.organization != new_parent.organization:
            raise ValidationError("Cannot transfer organization to a parent in a different organization")
        
        org.parent = new_parent
        org.full_clean()
        org.save()
        return org

    @classmethod
    def archive_organization(cls, org_id: int) -> OrganizationContext:
        """Archive an organization and its children"""
        with transaction.atomic():
            org = OrganizationContext.objects.get(id=org_id)
            
            # Archive base organization
            entity_org = org.organization
            entity_org.status = Organization.Status.INACTIVE
            entity_org.save()
            
            # Archive organization context
            org.is_active = False
            org.deactivated_at = timezone.now()
            org.save()
            
            # Archive all children
            for child in org.get_all_children():
                child.is_active = False
                child.deactivated_at = timezone.now()
                child.save()
            
            return org

    @classmethod
    def restore_organization(cls, org_id: int) -> OrganizationContext:
        """Restore an archived organization"""
        with transaction.atomic():
            org = OrganizationContext.objects.get(id=org_id)
            
            # Restore base organization
            entity_org = org.organization
            entity_org.status = Organization.Status.ACTIVE
            entity_org.save()
            
            # Restore organization context
            org.is_active = True
            org.deactivated_at = None
            org.save()
            
            return org

    @classmethod
    def get_organization_hierarchy(cls, org_id: int) -> Dict:
        """Get complete organization hierarchy as nested dictionary"""
        org = OrganizationContext.objects.get(id=org_id)
        
        def build_hierarchy(node: OrganizationContext) -> Dict:
            return {
                "id": node.id,
                "name": node.name,
                "description": node.description,
                "is_active": node.is_active,
                "children": [
                    build_hierarchy(child) 
                    for child in node.get_all_children()
                ]
            }
        
        return build_hierarchy(org)

    @classmethod
    def validate_organization_structure(cls, organization_id: int) -> None:
        """Validate organization structure for circular references"""
        org = OrganizationContext.objects.get(id=organization_id)
        visited = set()
        current = org

        while current:
            if current.id in visited:
                raise ValidationError("Circular reference detected in organization structure")
            visited.add(current.id)
            current = current.parent

    @classmethod
    @transaction.atomic
    def merge_organizations(cls, source_org_id: int, target_org_id: int) -> OrganizationContext:
        """Merge source organization into target organization"""
        source_org = OrganizationContext.objects.get(id=source_org_id)
        target_org = OrganizationContext.objects.get(id=target_org_id)
        
        # Validate same base organization
        if source_org.organization != target_org.organization:
            raise ValidationError("Cannot merge organizations from different base organizations")
        
        # Transfer all children to target org
        for child in source_org.get_all_children():
            child.parent = target_org
            child.save()
        
        # Archive source org
        source_org.is_active = False
        source_org.deactivated_at = timezone.now()
        source_org.save()
        
        return target_org 