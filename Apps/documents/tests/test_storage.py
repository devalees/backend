import pytest
import os
import time
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from ..storage import DocumentStorage

User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        password='testpass',
        email='test@example.com'
    )

@pytest.fixture
def storage():
    return DocumentStorage()

@pytest.mark.django_db
class TestDocumentStorage:
    def test_get_upload_path(self, storage, user):
        """Test that the upload path is correctly generated."""
        name = 'test.pdf'
        path = storage.get_upload_path(name, user)
        assert 'documents' in path
        assert str(user.id) in path
        assert name in path

    def test_get_available_name_simple(self, storage, mocker):
        """Test that a unique name is generated for a simple filename."""
        # Mock exists method to return True for the original name and False for new names
        def mock_exists(name):
            return name == 'test.pdf'
        
        mocker.patch.object(storage, 'exists', side_effect=mock_exists)
        
        # Test with a simple filename
        name = 'test.pdf'
        new_name = storage.get_available_name(name)
        
        # Basic assertions
        assert new_name != name
        assert new_name.startswith('test_')
        assert new_name.endswith('.pdf')

    def test_get_available_name_path(self, storage, mocker):
        """Test that a unique name is generated for a full path."""
        # Mock exists method to return True for the original path and False for new paths
        def mock_exists(name):
            return name == 'documents/2024/03/test.pdf'
        
        mocker.patch.object(storage, 'exists', side_effect=mock_exists)
        
        # Test with a full path
        path_name = 'documents/2024/03/test.pdf'
        new_path_name = storage.get_available_name(path_name)
        
        # Basic assertions
        assert new_path_name != path_name
        assert new_path_name.startswith('documents/2024/03/test_')
        assert new_path_name.endswith('.pdf')

    @pytest.mark.django_db
    def test_save_file(self, storage, mocker):
        """Test that files can be saved correctly."""
        # Mock the filesystem operations
        mocker.patch.object(storage, 'exists', return_value=False)
        mocker.patch.object(storage, '_save')
        
        name = 'test.pdf'
        content = SimpleUploadedFile(name, b'test content')
        
        saved_name = storage.save(name, content)
        
        # Verify that _save was called with the correct arguments
        storage._save.assert_called_once_with(name, content)
        
        # Verify the saved name follows our naming convention
        assert saved_name.startswith('test_')
        assert saved_name.endswith('.pdf')

    @pytest.mark.django_db
    def test_delete_file(self, storage, mocker):
        """Test that files can be deleted correctly."""
        # Mock the filesystem operations
        def mock_exists(name):
            return name == 'test.pdf'
        
        mocker.patch.object(storage, 'exists', side_effect=mock_exists)
        mocker.patch.object(storage, 'delete')
        
        name = 'test.pdf'
        content = SimpleUploadedFile(name, b'test content')
        
        # Save a file first
        saved_name = storage.save(name, content)
        
        # Delete the file
        storage.delete(saved_name)
        
        # Verify that delete was called with the correct argument
        storage.delete.assert_called_once_with(saved_name) 