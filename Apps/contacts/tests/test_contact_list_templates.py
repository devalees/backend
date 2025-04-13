import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from Apps.contacts.models import ContactListTemplate, ContactList
from Apps.contacts.tests.factories import ContactListTemplateFactory, OrganizationFactory, UserFactory
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

@pytest.mark.django_db
class TestContactListTemplate:
    def test_create_contact_list_template(self):
        """Test creating a contact list template"""
        template = ContactListTemplateFactory()
        assert template.name is not None
        assert template.description is not None
        assert template.organization is not None
        assert template.created_by is not None
        assert template.is_active
        assert template.fields is not None
        assert isinstance(template.fields, dict)

    def test_contact_list_template_str(self):
        """Test string representation of contact list template"""
        template = ContactListTemplateFactory()
        assert str(template) == template.name

    def test_contact_list_template_soft_delete(self):
        """Test soft delete functionality"""
        template = ContactListTemplateFactory()
        template.delete()
        assert not template.is_active
        assert ContactListTemplate.objects.filter(id=template.id).exists()

    def test_contact_list_template_hard_delete(self):
        """Test hard delete functionality"""
        template = ContactListTemplateFactory()
        template.hard_delete()
        assert not ContactListTemplate.objects.filter(id=template.id).exists()

    def test_contact_list_template_validation(self):
        """Test validation of contact list template"""
        # Test required fields
        with pytest.raises(ValidationError):
            template = ContactListTemplateFactory.build(name="", organization=None)
            template.clean()

        # Test unique name constraint
        organization = OrganizationFactory()
        template1 = ContactListTemplateFactory(organization=organization, name="Test Template")
        
        with pytest.raises(ValidationError):
            template2 = ContactListTemplateFactory.build(organization=organization, name="Test Template")
            template2.clean()

        # Test fields validation
        with pytest.raises(ValidationError):
            template = ContactListTemplateFactory.build(fields="not a dict")
            template.clean()

    def test_unique_name_constraint(self):
        """Test that template names must be unique within an organization"""
        org = OrganizationFactory()
        template1 = ContactListTemplateFactory(
            organization=org,
            name='Unique Template 1'
        )
        
        # Try to create another template with the same name
        with pytest.raises(ValidationError):
            ContactListTemplateFactory(
                organization=org,
                name='Unique Template 1'
            )

    def test_create_contact_list_from_template(self):
        """Test creating a contact list from a template"""
        template = ContactListTemplateFactory()
        user = UserFactory()
        
        contact_list = template.create_contact_list(user=user)
        
        assert contact_list.name == template.name
        assert contact_list.description == template.description
        assert contact_list.organization == template.organization
        assert contact_list.created_by == user
        assert contact_list.is_active

    def test_apply_template_to_contact_list(self):
        """Test applying a template to an existing contact list"""
        template = ContactListTemplateFactory()
        contact_list = ContactList.objects.create(
            name="Original Name",
            description="Original Description",
            organization=template.organization,
            created_by=template.created_by
        )
        
        template.apply_template(contact_list)
        
        assert contact_list.name == template.name
        assert contact_list.description == template.description

    def test_template_fields_structure(self):
        """Test the structure of template fields"""
        template = ContactListTemplateFactory()
        
        # Check that fields has the expected structure
        assert 'name' in template.fields
        assert 'description' in template.fields
        assert 'contacts' in template.fields
        
        # Check field properties
        assert template.fields['name'].get('required') is True
        assert template.fields['description'].get('required') is False
        assert template.fields['contacts'].get('required') is False

    def test_template_versioning(self):
        """Test template versioning system"""
        org = OrganizationFactory()
        template = ContactListTemplateFactory(
            organization=org,
            name='Version Test Template'
        )
        
        # Create a new version
        new_version = ContactListTemplateFactory(
            organization=org,
            name='Version Test Template V2',
            parent=template
        )
        
        assert new_version.parent == template
        assert template.children.count() == 1

    def test_template_inheritance(self):
        """Test template inheritance"""
        parent_template = ContactListTemplateFactory()
        child_template = ContactListTemplateFactory(parent=parent_template)
        
        assert child_template.parent == parent_template
        assert parent_template in child_template.get_ancestors()
        assert child_template in parent_template.get_descendants()

    def test_get_ancestors(self):
        """Test getting ancestors of a template"""
        grandparent = ContactListTemplateFactory()
        parent = ContactListTemplateFactory(parent=grandparent)
        child = ContactListTemplateFactory(parent=parent)
        
        ancestors = child.get_ancestors()
        assert grandparent in ancestors
        assert parent in ancestors
        assert len(ancestors) == 2

    def test_get_descendants(self):
        """Test getting descendants of a template"""
        grandparent = ContactListTemplateFactory()
        parent = ContactListTemplateFactory(parent=grandparent)
        child = ContactListTemplateFactory(parent=parent)
        
        descendants = grandparent.get_descendants()
        assert parent in descendants
        assert child in descendants
        assert len(descendants) == 2 