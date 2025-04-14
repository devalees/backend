import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from Apps.contacts.models import ContactNote, Contact
from Apps.entity.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
@pytest.mark.django_db
def organization():
    return Organization.objects.create(name="Test Org")

@pytest.fixture
@pytest.mark.django_db
def user():
    return User.objects.create_user(username="testuser", email="test@example.com", password="testpass")

@pytest.fixture
@pytest.mark.django_db
def contact(organization):
    return Contact.objects.create(
        name="Test Contact",
        email="contact@example.com",
        phone="1234567890",
        organization=organization
    )

@pytest.fixture
@pytest.mark.django_db
def contact_note(contact, organization, user):
    return ContactNote.objects.create(
        contact=contact,
        organization=organization,
        content="Test note content",
        created_by=user
    )

@pytest.mark.django_db
def test_contact_note_creation(contact, organization, user):
    note = ContactNote.objects.create(
        contact=contact,
        organization=organization,
        content="Test note content",
        created_by=user
    )
    assert note.content == "Test note content"
    assert note.contact == contact
    assert note.organization == organization
    assert note.created_by == user

@pytest.mark.django_db
def test_note_validation(contact, organization, user):
    # Test empty content and no attachment
    with pytest.raises(ValidationError):
        note = ContactNote(
            contact=contact,
            organization=organization,
            created_by=user
        )
        note.clean()

@pytest.mark.django_db
def test_note_with_file_attachment(contact, organization, user):
    file_content = b"test file content"
    uploaded_file = SimpleUploadedFile("test.txt", file_content)
    
    note = ContactNote.objects.create(
        contact=contact,
        organization=organization,
        created_by=user,
        file_attachment=uploaded_file
    )
    
    # Check if "test" is in the filename rather than the exact suffix
    assert "test" in note.file_attachment.name
    assert note.file_type == "txt"

@pytest.mark.django_db
def test_note_str_representation(contact_note):
    expected_str = f'Note for {contact_note.contact} - {contact_note.created_at}'
    assert str(contact_note) == expected_str

@pytest.mark.django_db
def test_note_ordering(contact, organization, user):
    note1 = ContactNote.objects.create(
        contact=contact,
        organization=organization,
        content="First note",
        created_by=user
    )
    note2 = ContactNote.objects.create(
        contact=contact,
        organization=organization,
        content="Second note",
        created_by=user
    )
    
    notes = ContactNote.objects.filter(contact=contact)
    assert notes[0] == note2  # Most recent first
    assert notes[1] == note1

@pytest.mark.django_db
def test_private_note(contact, organization, user):
    private_note = ContactNote.objects.create(
        contact=contact,
        organization=organization,
        content="Private note content",
        created_by=user,
        is_private=True
    )
    assert private_note.is_private

@pytest.mark.django_db
def test_note_hard_delete(contact_note, user):
    file_content = b"test file content"
    uploaded_file = SimpleUploadedFile("test.txt", file_content)
    contact_note.file_attachment = uploaded_file
    contact_note.save()
    
    # Store file path for verification
    file_path = contact_note.file_attachment.path
    
    # Hard delete the note
    contact_note.hard_delete(user=user)
    
    # Verify note is deleted
    assert not ContactNote.objects.filter(id=contact_note.id).exists()
    
    # Verify file is deleted
    from pathlib import Path
    assert not Path(file_path).exists()

@pytest.mark.django_db
def test_note_soft_delete(contact_note, user):
    # Soft delete the note
    contact_note.delete(user=user)
    
    # Verify note is marked as inactive
    updated_note = ContactNote.objects.get(id=contact_note.id)
    assert not updated_note.is_active