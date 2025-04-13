import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db.utils import IntegrityError
from Apps.contacts.models import Contact, ContactGroup, ContactTemplate, ContactMonitoring, ContactGroupTemplate, ContactGroupMonitoring
from Apps.contacts.tests.factories import ContactFactory, ContactGroupFactory, ContactTemplateFactory, ContactGroupTemplateFactory
from django.contrib.auth import get_user_model
from Apps.entity.models import Organization
from django.db import transaction

User = get_user_model()

@pytest.mark.django_db
class TestContact:
    def test_create_contact(self):
        """Test creating a contact"""
        contact = ContactFactory()
        assert contact.name is not None
        assert contact.email is not None
        assert contact.phone is not None
        assert contact.organization is not None
        assert contact.department is not None
        assert contact.team is not None
        assert contact.created_by is not None
        assert contact.is_active

    def test_contact_str(self):
        """Test string representation of contact"""
        contact = ContactFactory()
        assert str(contact) == contact.name

    def test_contact_soft_delete(self):
        """Test soft delete functionality"""
        contact = ContactFactory()
        contact.delete()
        assert not contact.is_active
        assert Contact.objects.filter(id=contact.id).exists()

    def test_contact_hard_delete(self):
        """Test hard delete functionality"""
        contact = ContactFactory()
        contact.hard_delete()
        assert not Contact.objects.filter(id=contact.id).exists()

    def test_unique_email_constraint(self):
        """Test that email must be unique"""
        contact = ContactFactory()
        with pytest.raises(ValidationError):
            ContactFactory(email=contact.email)

    def test_contact_validation(self):
        """Test contact validation"""
        # Test invalid email
        with pytest.raises(ValidationError):
            contact = ContactFactory(email="invalid-email")
            contact.full_clean()

        # Test invalid phone
        with pytest.raises(ValidationError):
            contact = ContactFactory(phone="invalid-phone")
            contact.full_clean()

@pytest.mark.django_db
class TestContactGroup:
    def test_create_contact_group(self):
        """Test creating a contact group"""
        group = ContactGroupFactory()
        assert group.name is not None
        assert group.description is not None
        assert group.organization is not None
        assert group.created_by is not None
        assert group.is_active

    def test_contact_group_str(self):
        """Test string representation of contact group"""
        group = ContactGroupFactory()
        assert str(group) == group.name

    def test_contact_group_soft_delete(self):
        """Test soft delete functionality"""
        group = ContactGroupFactory()
        group.delete()
        assert not group.is_active
        assert ContactGroup.objects.filter(id=group.id).exists()

    def test_contact_group_hard_delete(self):
        """Test hard delete functionality"""
        group = ContactGroupFactory()
        group.hard_delete()
        assert not ContactGroup.objects.filter(id=group.id).exists()

    def test_add_contact_to_group(self):
        """Test adding a contact to a group"""
        group = ContactGroupFactory()
        contact = ContactFactory()
        group.contacts.add(contact)
        assert contact in group.contacts.all()
        assert group in contact.groups.all()

    def test_remove_contact_from_group(self):
        """Test removing a contact from a group"""
        group = ContactGroupFactory()
        contact = ContactFactory()
        group.contacts.add(contact)
        group.contacts.remove(contact)
        assert contact not in group.contacts.all()
        assert group not in contact.groups.all()

@pytest.mark.django_db
class TestContactGroupHierarchy:
    """Test cases for ContactGroup hierarchy functionality"""
    
    def test_create_parent_child_relationship(self):
        """Test creating a parent-child relationship between groups"""
        parent_group = ContactGroupFactory()
        child_group = ContactGroupFactory()
        
        # Set parent-child relationship
        child_group.parent = parent_group
        child_group.save()
        
        # Verify relationship
        assert child_group.parent == parent_group
        assert child_group in parent_group.children.all()
        
    def test_multiple_level_hierarchy(self):
        """Test creating a multi-level hierarchy"""
        grandparent = ContactGroupFactory()
        parent = ContactGroupFactory()
        child = ContactGroupFactory()
        
        # Set up hierarchy
        parent.parent = grandparent
        parent.save()
        child.parent = parent
        child.save()
        
        # Verify relationships
        assert parent.parent == grandparent
        assert child.parent == parent
        assert child in parent.children.all()
        assert parent in grandparent.children.all()
        
    def test_circular_reference_prevention(self):
        """Test that circular references are prevented"""
        group_a = ContactGroupFactory()
        group_b = ContactGroupFactory()
        
        # Set up initial relationship
        group_b.parent = group_a
        group_b.save()
        
        # Attempt to create circular reference
        with pytest.raises(ValidationError):
            group_a.parent = group_b
            group_a.full_clean()
            
    def test_self_reference_prevention(self):
        """Test that self-references are prevented"""
        group = ContactGroupFactory()
        
        # Attempt to set parent to self
        with pytest.raises(ValidationError):
            group.parent = group
            group.full_clean()
            
    def test_get_ancestors(self):
        """Test getting all ancestors of a group"""
        level1 = ContactGroupFactory()
        level2 = ContactGroupFactory(parent=level1)
        level3 = ContactGroupFactory(parent=level2)
        
        # Get ancestors
        ancestors = level3.get_ancestors()
        
        # Verify ancestors
        assert len(ancestors) == 2
        assert level2 in ancestors
        assert level1 in ancestors
        
    def test_get_descendants(self):
        """Test getting all descendants of a group"""
        parent = ContactGroupFactory()
        child1 = ContactGroupFactory(parent=parent)
        child2 = ContactGroupFactory(parent=parent)
        grandchild = ContactGroupFactory(parent=child1)
        
        # Get descendants
        descendants = parent.get_descendants()
        
        # Verify descendants
        assert len(descendants) == 3
        assert child1 in descendants
        assert child2 in descendants
        assert grandchild in descendants
        
    def test_delete_cascades_to_children(self):
        """Test that deleting a parent group cascades to children"""
        parent = ContactGroupFactory()
        child1 = ContactGroupFactory(parent=parent)
        child2 = ContactGroupFactory(parent=parent)
        
        # Delete parent with hard_delete=True to actually delete from database
        parent.delete(hard_delete=True)
        
        # Verify children are also deleted
        assert not ContactGroup.objects.filter(id=child1.id).exists()
        assert not ContactGroup.objects.filter(id=child2.id).exists()
        
    def test_move_group_in_hierarchy(self):
        """Test moving a group to a different parent"""
        original_parent = ContactGroupFactory()
        new_parent = ContactGroupFactory()
        child = ContactGroupFactory(parent=original_parent)
        
        # Move child to new parent
        child.parent = new_parent
        child.save()
        
        # Verify new relationship
        assert child.parent == new_parent
        assert child not in original_parent.children.all()
        assert child in new_parent.children.all()

@pytest.mark.django_db
class TestContactGroupTemplate:
    """Test cases for ContactGroup template functionality"""
    
    def test_create_group_from_template(self):
        """Test creating a group from a template"""
        template = ContactGroupTemplateFactory()
        group = ContactGroup.create_from_template(template)
        
        # Verify group was created with template properties
        assert group.name == template.name
        assert group.description == template.description
        assert group.organization == template.organization
        
    def test_template_fields_validation(self):
        """Test validation of template fields"""
        # Test with valid fields
        template = ContactGroupTemplateFactory()
        template.full_clean()  # Should not raise
        
        # Test with invalid fields (not a dict)
        with pytest.raises(ValidationError):
            template = ContactGroupTemplateFactory()
            template.fields = "not a dict"
            template.full_clean()
            
        # Test with missing required property
        with pytest.raises(ValidationError):
            template = ContactGroupTemplateFactory()
            del template.fields['name']['required']
            template.full_clean()
            
    def test_template_unique_constraint(self):
        """Test unique constraint for name within organization"""
        # Create a template
        template1 = ContactGroupTemplateFactory(name="Unique Template")
        
        # Try to create another with same name and org
        with pytest.raises(ValidationError):
            template2 = ContactGroupTemplateFactory.build(
                name="Unique Template",
                organization=template1.organization
            )
            template2.full_clean()
            
    def test_apply_template_to_existing_group(self):
        """Test applying a template to an existing group"""
        template = ContactGroupTemplateFactory()
        group = ContactGroupFactory()
        
        # Apply template
        group.apply_template(template)
        
        # Verify group was updated with template properties
        assert group.name == template.name
        assert group.description == template.description
        
    def test_template_inheritance(self):
        """Test template inheritance"""
        parent_template = ContactGroupTemplateFactory()
        child_template = ContactGroupTemplateFactory(parent=parent_template)
        
        # Verify child template inherits from parent
        assert child_template.parent == parent_template
        assert child_template in parent_template.children.all()
        
    def test_template_versioning(self):
        """Test template versioning"""
        template = ContactGroupTemplateFactory()
        initial_version = template.version
        
        # Update template
        template.name = "Updated Name"
        template.save()
        
        # Verify version was incremented
        assert template.version > initial_version
        
    def test_template_soft_delete(self):
        """Test soft delete functionality"""
        template = ContactGroupTemplateFactory()
        template.delete()
        assert not template.is_active
        assert ContactGroupTemplate.objects.filter(id=template.id).exists()
        
    def test_template_hard_delete(self):
        """Test hard delete functionality"""
        template = ContactGroupTemplateFactory()
        template.hard_delete()
        assert not ContactGroupTemplate.objects.filter(id=template.id).exists()

@pytest.mark.django_db
class TestContactTemplate:
    """Test cases for ContactTemplate model"""
    
    def test_create_contact_template(self):
        """Test creating a contact template"""
        template = ContactTemplateFactory()
        
        assert template.name is not None
        assert template.description is not None
        assert template.organization is not None
        assert template.created_by is not None
        assert template.updated_by is not None
        assert template.fields is not None
        assert template.is_active
        
    def test_template_str(self):
        """Test string representation of template"""
        template = ContactTemplateFactory(name="Test Template")
        assert str(template) == "Test Template"
        
    def test_template_soft_delete(self):
        """Test soft delete functionality"""
        template = ContactTemplateFactory()
        template.delete()
        assert not template.is_active
        assert ContactTemplate.objects.filter(id=template.id).exists()
        
    def test_template_hard_delete(self):
        """Test hard delete functionality"""
        template = ContactTemplateFactory()
        template.hard_delete()
        assert not ContactTemplate.objects.filter(id=template.id).exists()
        
    def test_template_fields_validation(self):
        """Test fields validation in more detail"""
        # Test with valid fields
        template = ContactTemplateFactory()
        template.full_clean()  # Should not raise
        
        # Test with invalid fields (not a dict)
        with pytest.raises(ValidationError):
            template = ContactTemplateFactory()
            template.fields = "not a dict"
            template.full_clean()
        
        # Test with invalid field type
        with pytest.raises(ValidationError):
            template = ContactTemplateFactory()
            template.fields['name']['type'] = 'invalid_type'
            template.full_clean()
            
        # Test with missing required property
        with pytest.raises(ValidationError):
            template = ContactTemplateFactory()
            del template.fields['name']['required']
            template.full_clean()
            
        # Test with non-boolean required
        with pytest.raises(ValidationError):
            template = ContactTemplateFactory()
            template.fields['name']['required'] = "not a boolean"
            template.full_clean()
            
    def test_unique_organization_constraint(self):
        """Test unique constraint for name within organization"""
        # Create a template
        template1 = ContactTemplateFactory(name="Unique Template")
    
        # Try to create another with same name and org
        with pytest.raises(ValidationError):
            template2 = ContactTemplateFactory.build(
                name="Unique Template",
                organization=template1.organization
            )
            # Use full_clean() to trigger validation before database insert
            template2.full_clean() 