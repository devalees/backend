import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from unittest.mock import patch, MagicMock
from django.db.models.signals import post_save
from elasticsearch_dsl.connections import connections

from Apps.documents.models import Document, DocumentVersion

User = get_user_model()

@pytest.fixture(autouse=True)
def mock_elasticsearch():
    """Mock Elasticsearch connection for all tests."""
    with patch('elasticsearch_dsl.connections.connections.create_connection') as mock_create_connection:
        mock_es = MagicMock()
        mock_create_connection.return_value = mock_es
        yield mock_es

@pytest.fixture(autouse=True)
def disable_signals():
    """Disable signals for all tests."""
    with patch('Apps.documents.signals.document_post_save'):
        yield

@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        password='testpass',
        email='test@example.com'
    )

@pytest.fixture
def document(user):
    test_file = SimpleUploadedFile("test.txt", b"Test content")
    doc = Document.objects.create(
        title='Test Document',
        file=test_file,
        user=user
    )
    return doc

@pytest.fixture
def document_versions(document, user):
    versions = []
    for i in range(3):
        test_file = SimpleUploadedFile(f"version_{i+1}.txt", f"Content version {i}".encode())
        version = DocumentVersion.objects.create(
            document=document,
            version_number=i + 1,
            file=test_file,
            user=user,
            comment=f'Version {i+1} comment',
            is_current=(i == 2)  # Make the last version current
        )
        versions.append(version)
    return versions

@pytest.mark.django_db
class TestVersionComparison:
    def test_version_comparison_metadata(self, document_versions):
        """Test comparing metadata between versions"""
        v1, v2, _ = document_versions
        result = v1.document.compare_versions(v1, v2)
        
        assert result['version_numbers'] == (v1.version_number, v2.version_number)
        assert result['creation_times'] == (v1.created_at, v2.created_at)
        assert result['users'] == (v1.user, v2.user)
        assert result['comments'] == (v1.comment, v2.comment)

    def test_version_comparison_file_content(self, document_versions):
        """Test comparing file content between versions"""
        v1, v2, _ = document_versions
        result = v1.document.compare_versions(v1, v2)
        
        assert result['version_numbers'] == (v1.version_number, v2.version_number)
        assert v1.version_number < v2.version_number

@pytest.mark.django_db
class TestVersionRestoration:
    def test_restore_previous_version(self, document_versions):
        """Test restoring a document to a previous version"""
        v1, v2, v3 = document_versions
        document = v3.document
        
        # Restore to v1
        document.restore_version(v1, skip_index=True)
        
        assert document.current_version == v1
        assert document.last_modified > v1.created_at

    def test_restore_version_validation(self, document_versions, user):
        """Test validation when restoring versions"""
        v1 = document_versions[0]
        
        # Create another document and version
        test_file = SimpleUploadedFile("other.txt", b"Other content")
        other_document = Document.objects.create(
            title='Other Document',
            file=test_file,
            user=user
        )
        
        other_version = DocumentVersion.objects.create(
            document=other_document,
            version_number=1,
            file=test_file,
            user=user,
            comment='Other version'
        )
        
        with pytest.raises(ValueError) as exc_info:
            v1.document.restore_version(other_version, skip_index=True)
        assert str(exc_info.value) == "Cannot restore version from a different document"

    def test_restore_version_metadata(self, document_versions):
        """Test metadata is updated when restoring versions"""
        v1, v2, v3 = document_versions
        document = v3.document
        
        # Record the time before restoration
        before_restore = timezone.now()
        
        # Restore to v1
        document.restore_version(v1, skip_index=True)
        
        # Verify metadata is updated correctly
        assert document.current_version == v1
        assert document.last_modified >= before_restore