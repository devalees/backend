import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from Apps.documents.models import Document, DocumentVersion, DocumentClassification, DocumentTag

User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        password='testpass',
        email='test@example.com'
    )

@pytest.fixture
def document(user):
    return Document.objects.create(
        title='Test Document',
        description='Test Description',
        created_by=user,
        updated_by=user
    )

@pytest.fixture
def document_version(document, user):
    return DocumentVersion.objects.create(
        document=document,
        version_number=1,
        file=SimpleUploadedFile('test.pdf', b'test content'),
        user=user,
        comment='Initial version',
        branch_name='main'
    )

@pytest.fixture
def document_classification():
    return DocumentClassification.objects.create(
        name='Test Classification',
        description='Test Classification Description'
    )

@pytest.fixture
def document_tag():
    return DocumentTag.objects.create(
        name='Test Tag',
        description='Test Tag Description',
        color='#FF0000'
    )

@pytest.fixture
def mock_elasticsearch():
    with patch('elasticsearch_dsl.connections.connections.create_connection') as mock_conn:
        mock_es = MagicMock()
        mock_conn.return_value = mock_es
        yield mock_es

@pytest.fixture
def mock_signals():
    with patch('Apps.documents.signals.document_post_save') as mock_doc_signal, \
         patch('Apps.documents.signals.document_version_post_save') as mock_ver_signal, \
         patch('elasticsearch_dsl.connections.connections.create_connection') as mock_conn, \
         patch('Apps.documents.search.DocumentIndex.save') as mock_doc_save, \
         patch('Apps.documents.search.DocumentIndex.get') as mock_doc_get, \
         patch('Apps.documents.search.DocumentIndex.delete') as mock_doc_delete, \
         patch('Apps.documents.search.DocumentVersionIndex.save') as mock_ver_save, \
         patch('Apps.documents.search.DocumentVersionIndex.get') as mock_ver_get, \
         patch('Apps.documents.search.DocumentVersionIndex.delete') as mock_ver_delete:
        mock_es = MagicMock()
        mock_conn.return_value = mock_es
        yield mock_doc_signal, mock_ver_signal, mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete

@pytest.mark.django_db
class TestDocument:
    def test_document_creation(self, user, mock_signals):
        """Test document creation."""
        mock_doc_signal, mock_ver_signal, mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_signals
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft'
        )
        assert document.title == 'Test Document'
        assert document.description == 'Test Description'
        assert document.user == user
        assert document.status == 'draft'
        mock_doc_save.assert_called_once()

    def test_document_str(self, user, mock_signals):
        """Test document string representation."""
        mock_doc_signal, mock_ver_signal, mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_signals
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft'
        )
        assert str(document) == 'Test Document'
        mock_doc_save.assert_called_once()

    def test_document_validation(self, user, mock_signals):
        """Test document validation."""
        mock_doc_signal, mock_ver_signal, mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_signals
        with pytest.raises(ValidationError):
            document = Document(
                title='',
                description='Test Description',
                user=user,
                status='draft'
            )
            document.full_clean()

@pytest.mark.django_db
class TestDocumentVersion:
    def test_document_version_creation(self, user, mock_signals):
        """Test document version creation."""
        mock_doc_signal, mock_ver_signal, mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_signals
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft'
        )
        file = SimpleUploadedFile('test.pdf', b'test content')
        version = DocumentVersion.objects.create(
            document=document,
            version_number=2,
            file=file,
            user=user,
            comment='Test comment'
        )
        assert version.document == document
        assert version.version_number == 2
        assert version.file.name.startswith('documents/versions/')
        assert version.file.name.endswith('.pdf')
        assert version.user == user
        assert version.comment == 'Test comment'
        mock_ver_save.assert_called_once()

    def test_document_version_str(self, user, mock_signals):
        """Test document version string representation."""
        mock_doc_signal, mock_ver_signal, mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_signals
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft'
        )
        file = SimpleUploadedFile('test.pdf', b'test content')
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=file,
            user=user,
            comment='Test comment'
        )
        assert str(version) == 'Test Document - main - Version 1'
        mock_ver_save.assert_called_once()

    def test_document_version_validation(self, user, mock_signals):
        """Test document version validation."""
        mock_doc_signal, mock_ver_signal, mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_signals
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft'
        )
        file = SimpleUploadedFile('test.pdf', b'test content')
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=file,
            user=user,
            comment='Test comment'
        )
        assert version.version_number == 1
        mock_ver_save.assert_called_once()

    def test_document_version_branching(self, user, mock_signals):
        """Test document version branching functionality."""
        mock_doc_signal, mock_ver_signal, mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_signals
        
        # Create initial document and version
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft'
        )
        file = SimpleUploadedFile('test.pdf', b'test content')
        initial_version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=file,
            user=user,
            comment='Initial version',
            branch_name='main'
        )
        
        # Create a new branch
        new_branch = initial_version.create_branch(
            branch_name='feature',
            user=user,
            comment='Creating feature branch'
        )
        
        # Verify branch creation
        assert new_branch.branch_name == 'feature'
        assert new_branch.version_number == 1
        assert new_branch.parent_version == initial_version
        assert new_branch.is_current
        
        # Verify original version is no longer current
        initial_version.refresh_from_db()
        assert not initial_version.is_current
        
        # Try to create another version in the feature branch
        next_version_number = DocumentVersion.get_next_version_number(document, 'feature')
        new_version = DocumentVersion.objects.create(
            document=document,
            version_number=next_version_number,
            file=file,
            user=user,
            comment='New version in feature branch',
            branch_name='feature'
        )
        assert new_version.version_number == 2
        assert new_version.branch_name == 'feature'
        
        # Try to create a branch with same name (should fail)
        with pytest.raises(ValidationError):
            initial_version.create_branch(
                branch_name='feature',
                user=user,
                comment='This should fail'
            )

@pytest.mark.django_db
class TestDocumentClassification:
    def test_document_classification_creation(self):
        """Test document classification creation."""
        classification = DocumentClassification.objects.create(
            name='Test Classification',
            description='Test Classification Description'
        )
        assert classification.name == 'Test Classification'
        assert classification.description == 'Test Classification Description'

    def test_document_classification_str(self):
        """Test document classification string representation."""
        classification = DocumentClassification.objects.create(
            name='Test Classification',
            description='Test Classification Description'
        )
        assert str(classification) == 'Test Classification'

    def test_document_classification_validation(self):
        """Test document classification validation."""
        with pytest.raises(ValidationError):
            classification = DocumentClassification(
                name='',
                description='Test Classification Description'
            )
            classification.full_clean()

@pytest.mark.django_db
class TestDocumentTag:
    def test_document_tag_creation(self):
        """Test document tag creation."""
        tag = DocumentTag.objects.create(
            name='Test Tag',
            description='Test Tag Description',
            color='#FF0000'
        )
        assert tag.name == 'Test Tag'
        assert tag.description == 'Test Tag Description'
        assert tag.color == '#FF0000'

    def test_document_tag_str(self):
        """Test document tag string representation."""
        tag = DocumentTag.objects.create(
            name='Test Tag',
            description='Test Tag Description',
            color='#FF0000'
        )
        assert str(tag) == 'Test Tag'

    def test_document_tag_validation(self):
        """Test document tag validation."""
        with pytest.raises(ValidationError):
            tag = DocumentTag(
                name='',
                description='Test Tag Description',
                color='#FF0000'
            )
            tag.full_clean() 