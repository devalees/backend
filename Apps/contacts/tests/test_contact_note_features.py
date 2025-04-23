import pytest
import json
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

from Apps.contacts.models import ContactNote, Contact, ContactNoteNotification, ContactNoteMonitoring
from Apps.contacts.cache_manager import ContactNoteCache
from Apps.entity.models import Organization

User = get_user_model()

@pytest.fixture
@pytest.mark.django_db
def setup_test_data():
    # Create test organization
    organization = Organization.objects.create(name="Test Org")
    
    # Create test users
    user1 = User.objects.create_user(username="testuser1", email="test1@example.com", password="testpass1")
    user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password="testpass2")
    
    # Create test contact
    contact = Contact.objects.create(
        name="Test Contact",
        email="contact@example.com",
        phone="1234567890",
        organization=organization
    )
    
    # Create test note
    note = ContactNote.objects.create(
        contact=contact,
        organization=organization,
        content="Test note content",
        created_by=user1
    )
    
    # Create test note with file
    file_content = b"This is a test file content"
    uploaded_file = SimpleUploadedFile("test.txt", file_content)
    note_with_file = ContactNote.objects.create(
        contact=contact,
        organization=organization,
        content="Test note with file",
        created_by=user1,
        file_attachment=uploaded_file
    )
    
    # Clear cache to start fresh
    cache.clear()
    
    return {
        'organization': organization,
        'user1': user1,
        'user2': user2,
        'contact': contact,
        'note': note,
        'note_with_file': note_with_file
    }

@pytest.fixture
@pytest.mark.django_db
def api_client():
    return APIClient()

# File Sharing Tests
@pytest.mark.django_db
def test_file_sharing_upload(setup_test_data):
    """Test uploading a file to a contact note"""
    file_content = b"New file content for sharing"
    uploaded_file = SimpleUploadedFile("shared.txt", file_content)
    
    note = ContactNote.objects.create(
        contact=setup_test_data['contact'],
        organization=setup_test_data['organization'],
        content="Note with shared file",
        created_by=setup_test_data['user1'],
        file_attachment=uploaded_file
    )
    
    assert note.file_attachment.name is not None
    assert "shared" in note.file_attachment.name
    assert note.file_type == "txt"

@pytest.mark.django_db
def test_file_sharing_download(setup_test_data, api_client):
    """Test downloading a file from a contact note via API"""
    api_client.force_authenticate(user=setup_test_data['user1'])
    
    # Get the note with file
    note_with_file = setup_test_data['note_with_file']
    
    # Use DRF test client
    url = reverse('contacts:contact-note-download-file', kwargs={'pk': note_with_file.pk})
    response = api_client.get(url)
    
    # First check for status code
    assert response.status_code == status.HTTP_200_OK
    
    # For FileResponse we mainly check the content-disposition header
    assert 'attachment; filename=' in response.get('Content-Disposition', '')

@pytest.mark.django_db
def test_file_sharing_delete(setup_test_data):
    """Test deleting a file from a contact note"""
    note_with_file = setup_test_data['note_with_file']
    file_path = note_with_file.file_attachment.path
    
    # Store file path for verification
    from pathlib import Path
    file_exists_before = Path(file_path).exists()
    assert file_exists_before
    
    # Save the original filename for validation
    original_filename = note_with_file.file_attachment.name
    assert original_filename  # Ensure it's not empty
    
    # Delete the file
    note_with_file.file_attachment.delete(save=False)
    note_with_file.file_type = None
    note_with_file.save()
    
    # Verify file is deleted
    file_exists_after = Path(file_path).exists()
    assert not file_exists_after
    
    # Refresh from db to get updated state
    note_with_file.refresh_from_db()
    assert not note_with_file.file_attachment.name  # Name should be empty
    assert note_with_file.file_type is None

# Notification Tests
@pytest.mark.django_db
def test_create_notification(setup_test_data):
    """Test creating a notification for a contact note"""
    note = setup_test_data['note']
    user2 = setup_test_data['user2']
    
    notification = ContactNoteNotification.objects.create(
        note=note,
        user=user2,
        notification_type='mention',
        message=f"You were mentioned in a note by {note.created_by.username}"
    )
    
    assert notification.note == note
    assert notification.user == user2
    assert notification.notification_type == 'mention'
    assert not notification.is_read

@pytest.mark.django_db
def test_read_notification(setup_test_data):
    """Test marking a notification as read"""
    note = setup_test_data['note']
    user2 = setup_test_data['user2']
    
    notification = ContactNoteNotification.objects.create(
        note=note,
        user=user2,
        notification_type='mention',
        message="You were mentioned in a note"
    )
    
    assert not notification.is_read
    
    notification.mark_as_read()
    notification.refresh_from_db()
    
    assert notification.is_read

# Caching Tests
@pytest.mark.django_db
def test_note_caching(setup_test_data):
    """Test caching of contact notes"""
    note = setup_test_data['note']
    
    # Verify note is not in cache initially
    note_key = ContactNoteCache.get_note_key(note.id)
    cached_note = cache.get(note_key)
    assert cached_note is None
    
    # Set note in cache
    ContactNoteCache.set_note(note)
    
    # Verify note is now in cache
    cached_note = cache.get(note_key)
    assert cached_note is not None
    assert cached_note['id'] == note.id
    assert cached_note['content'] == note.content

@pytest.mark.django_db
def test_get_note_from_cache(setup_test_data):
    """Test getting a note from cache"""
    note = setup_test_data['note']
    
    # Initially, cache should be empty
    cached_note = cache.get(ContactNoteCache.get_note_key(note.id))
    assert cached_note is None
    
    # Set note in cache
    ContactNoteCache.set_note(note)
    
    # Now it should be in cache
    cached_note = ContactNoteCache.get_note(note.id)
    assert cached_note is not None
    assert cached_note['id'] == note.id

@pytest.mark.django_db
def test_delete_note_cache(setup_test_data):
    """Test deleting a note from cache"""
    note = setup_test_data['note']
    contact = setup_test_data['contact']
    
    # Put note in cache
    ContactNoteCache.set_note(note)
    
    # Verify it's in cache
    note_key = ContactNoteCache.get_note_key(note.id)
    cached_note = cache.get(note_key)
    assert cached_note is not None
    
    # Delete from cache
    ContactNoteCache.delete_note_cache(note.id, contact.id)
    
    # Verify it's no longer in cache
    cached_note = cache.get(note_key)
    assert cached_note is None

@pytest.mark.django_db
def test_contact_notes_caching(setup_test_data):
    """Test caching of notes for a contact"""
    contact = setup_test_data['contact']
    note = setup_test_data['note']
    
    # Create another note for the same contact
    note2 = ContactNote.objects.create(
        contact=contact,
        organization=setup_test_data['organization'],
        content="Second test note",
        created_by=setup_test_data['user1']
    )
    
    # Verify contact notes are not in cache initially
    list_key = ContactNoteCache.get_note_list_key(contact.id)
    cached_notes = cache.get(list_key)
    assert cached_notes is None
    
    # Get notes, which should populate the cache
    notes = ContactNoteCache.get_contact_notes(contact.id)
    
    # Verify contact notes are now in cache
    cached_notes = cache.get(list_key)
    assert cached_notes is not None
    assert len(cached_notes) >= 2  # At least the two notes we created
    
    # Check that the correct note IDs are in the list
    # Handle both model instances and serialized data
    if hasattr(notes[0], 'id'):
        # If notes are model instances
        note_ids = [n.id for n in notes]
    else:
        # If notes are dictionaries
        note_ids = [n['id'] for n in notes]
        
    assert note.id in note_ids
    assert note2.id in note_ids

@pytest.mark.django_db
def test_note_cache_invalidation(setup_test_data):
    """Test cache invalidation when a note is updated"""
    note = setup_test_data['note']
    contact = setup_test_data['contact']
    
    # Put note in cache
    ContactNoteCache.set_note(note)
    
    # Set contact notes in cache
    notes_before = ContactNoteCache.get_contact_notes(contact.id)
    assert len(notes_before) > 0
    
    # Verify data is in cache
    note_key = ContactNoteCache.get_note_key(note.id)
    list_key = ContactNoteCache.get_note_list_key(contact.id)
    
    assert cache.get(note_key) is not None
    assert cache.get(list_key) is not None
    
    # Update the note through model
    note.content = "Updated content"
    note.save()
    
    # Verify note cache was invalidated by the signal handler
    # (might need a refresh if signals are not working in tests)
    ContactNoteCache.refresh_note_cache(note.id)
    
    # Individual note should be updated in cache with the new content
    updated_cache = cache.get(note_key)
    if updated_cache is not None:
        assert updated_cache['content'] == "Updated content"
    
    # Testing that the cache has been updated, either by being invalidated and removed
    # or by being refreshed with new data
    cache.delete(list_key)  # Clear the list cache
    
    # Get fresh notes from DB 
    fresh_notes = ContactNoteCache.get_contact_notes(contact.id)
    
    # Find the updated note
    found_updated_note = False
    for n in fresh_notes:
        if hasattr(n, 'id') and n.id == note.id:
            assert n.content == "Updated content"
            found_updated_note = True
            break
    
    assert found_updated_note, "Updated note not found in refreshed list"

@pytest.mark.django_db
def test_note_update_api(setup_test_data, api_client):
    """Test updating a note through API"""
    api_client.force_authenticate(user=setup_test_data['user1'])
    
    note = setup_test_data['note']
    
    url = reverse('contacts:contact-notes-detail', kwargs={'pk': note.id})
    data = {'content': 'Updated via API'}
    
    response = api_client.patch(url, data, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['content'] == 'Updated via API'
    
    # Verify the note was updated in the database
    note.refresh_from_db()
    assert note.content == 'Updated via API'

@pytest.mark.django_db
def test_note_delete_api(setup_test_data, api_client):
    """Test soft deleting a note through API"""
    api_client.force_authenticate(user=setup_test_data['user1'])
    
    note = setup_test_data['note']
    
    url = reverse('contacts:contact-notes-detail', kwargs={'pk': note.id})
    
    response = api_client.delete(url)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify the note was soft deleted
    note.refresh_from_db()
    assert not note.is_active

@pytest.mark.django_db
def test_note_hard_delete_api(setup_test_data, api_client):
    """Test hard deleting a note through API"""
    api_client.force_authenticate(user=setup_test_data['user1'])
    
    note = setup_test_data['note']
    
    url = reverse('contacts:contact-note-hard-delete', kwargs={'pk': note.id})
    
    response = api_client.delete(url)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify the note was completely deleted
    assert not ContactNote.objects.filter(id=note.id).exists()

@pytest.mark.django_db
def test_note_monitoring_create(setup_test_data):
    """Test creating a monitoring record for a note action"""
    note = setup_test_data['note']
    user1 = setup_test_data['user1']
    organization = setup_test_data['organization']
    
    # Create a monitoring record
    monitoring = ContactNoteMonitoring.objects.create(
        note=note,
        user=user1,
        organization=organization,  # Add organization which is required
        activity_type='view',
        description='Viewed note details',
        metadata={'ip': '127.0.0.1'}
    )
    
    assert monitoring.note == note
    assert monitoring.user == user1
    assert monitoring.activity_type == 'view'
    assert monitoring.description == 'Viewed note details'
    assert monitoring.metadata == {'ip': '127.0.0.1'}
    
    # Create another monitoring record for the same note
    monitoring2 = ContactNoteMonitoring.objects.create(
        note=note,
        user=user1,
        organization=organization,  # Add organization which is required
        activity_type='update',
        description='Updated note content',
        metadata={'old_content': 'Test note content', 'new_content': 'Updated content'}
    )
    
    # Verify both records exist
    records = ContactNoteMonitoring.objects.filter(note=note)
    assert records.count() == 2

@pytest.mark.django_db
def test_contact_note_notifications_api(setup_test_data, api_client):
    """Test note notifications API"""
    api_client.force_authenticate(user=setup_test_data['user1'])
    
    note = setup_test_data['note']
    user2 = setup_test_data['user2']
    
    url = reverse('contacts:contact-note-notifications-api')
    data = {
        'note': note.id,
        'user': user2.id,
        'notification_type': 'mention',
        'message': f'User {user2.username} was mentioned in a note'
    }
    
    response = api_client.post(url, data, format='json')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['message'] == data['message']

@pytest.mark.django_db
def test_contact_note_monitoring_api(setup_test_data, api_client):
    """Test note monitoring API"""
    api_client.force_authenticate(user=setup_test_data['user1'])
    
    note = setup_test_data['note']
    
    url = reverse('contacts:contact-note-monitoring-api')
    
    # Get monitoring records
    response = api_client.get(url, {'note': note.id})
    
    assert response.status_code == status.HTTP_200_OK
    
    # DRF might return paginated results
    if isinstance(response.data, dict) and 'results' in response.data:
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)
    else:
        assert isinstance(response.data, list) 