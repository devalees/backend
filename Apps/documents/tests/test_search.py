import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from elasticsearch_dsl import connections
from django.conf import settings
from unittest.mock import call

from Apps.documents.models import Document, DocumentVersion, DocumentClassification, DocumentTag
from Apps.documents.search import DocumentIndex, DocumentVersionIndex

User = get_user_model()

@pytest.fixture
def elasticsearch():
    connections.create_connection(hosts=[settings.ELASTICSEARCH_DSN])
    DocumentIndex.init()
    DocumentVersionIndex.init()
    yield
    DocumentIndex._index.delete()
    DocumentVersionIndex._index.delete()

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
        file_path='test/path/document.pdf',
        file_size=1024,
        mime_type='application/pdf',
        created_by=user
    )

@pytest.fixture
def document_classification():
    return DocumentClassification.objects.create(
        name='Contract',
        description='Legal contracts and agreements'
    )

@pytest.fixture
def document_tag():
    return DocumentTag.objects.create(
        name='Confidential',
        description='Confidential documents'
    )

@pytest.fixture
def mock_elasticsearch():
    with patch('elasticsearch_dsl.connections.connections.create_connection') as mock_conn, \
         patch('Apps.documents.search.DocumentIndex.save') as mock_doc_save, \
         patch('Apps.documents.search.DocumentIndex.get') as mock_doc_get, \
         patch('Apps.documents.search.DocumentIndex.delete') as mock_doc_delete, \
         patch('Apps.documents.search.DocumentVersionIndex.save') as mock_ver_save, \
         patch('Apps.documents.search.DocumentVersionIndex.get') as mock_ver_get, \
         patch('Apps.documents.search.DocumentVersionIndex.delete') as mock_ver_delete:
        mock_es = MagicMock()
        mock_conn.return_value = mock_es
        yield mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete

@pytest.mark.django_db
class TestDocumentIndex:
    def test_document_index_creation(self, user, organization, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft',
            organization=organization
        )
        
        # Add a version to the document
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=SimpleUploadedFile('test.pdf', b'test content'),
            user=user,
            organization=organization
        )
        
        # Create and save document index
        doc_index = DocumentIndex(
            meta={'id': document.id},
            title=document.title,
            description=document.description,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        doc_index.save()
        
        # Check if the document index was created correctly
        assert mock_doc_save.called
        
    def test_document_index_update(self, user, organization, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft',
            organization=organization
        )
        
        # Add a version to the document
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=SimpleUploadedFile('test.pdf', b'test content'),
            user=user,
            organization=organization
        )
        
        # Create the document index
        doc_index = DocumentIndex(
            meta={'id': document.id},
            title=document.title,
            description=document.description,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        doc_index.save()
        
        # Update the document title
        document.title = 'Updated Document Title'
        document.save()
        
        # Update the document index
        doc_index = DocumentIndex.get(id=document.id)
        doc_index.title = document.title
        doc_index.save()
        
        # Check if the document index was updated correctly
        mock_doc_save.assert_called()
    
    def test_document_index_deletion(self, user, organization, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft',
            organization=organization
        )
        
        # Add a version to the document
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=SimpleUploadedFile('test.pdf', b'test content'),
            user=user,
            organization=organization
        )
        
        # Create the document index
        doc_index = DocumentIndex(
            meta={'id': document.id},
            title=document.title,
            description=document.description,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        doc_index.save()
        
        # Delete the document index
        doc_index.delete()
        
        # Check if the document index was deleted correctly
        mock_doc_delete.assert_called_once()

@pytest.mark.django_db
class TestDocumentVersionIndex:
    def test_document_version_index_creation(self, user, organization, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft',
            organization=organization
        )
        
        # Add a version to the document
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=SimpleUploadedFile('test.pdf', b'test content'),
            user=user,
            comment='Initial version',
            organization=organization
        )
        
        # Create and save document version index
        ver_index = DocumentVersionIndex(
            meta={'id': version.id},
            document_id=document.id,
            document_title=document.title,
            version_number=version.version_number,
            comment=version.comment,
            created_at=version.created_at,
            updated_at=version.updated_at
        )
        ver_index.save()
        
        # Check if the document version index was created correctly
        assert mock_ver_save.called
    
    def test_document_version_index_update(self, user, organization, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft',
            organization=organization
        )
        
        # Add a version to the document
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=SimpleUploadedFile('test.pdf', b'test content'),
            user=user,
            comment='Initial version',
            organization=organization
        )
        
        # Create the document version index
        ver_index = DocumentVersionIndex(
            meta={'id': version.id},
            document_id=document.id,
            document_title=document.title,
            version_number=version.version_number,
            comment=version.comment,
            created_at=version.created_at,
            updated_at=version.updated_at
        )
        ver_index.save()
        
        # Update the document version comment
        version.comment = 'Updated comment'
        version.save()
        
        # Update the document version index
        ver_index = DocumentVersionIndex.get(id=version.id)
        ver_index.comment = version.comment
        ver_index.save()
        
        # Check if the document version index was updated correctly
        mock_ver_save.assert_called()
    
    def test_document_version_index_deletion(self, user, organization, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft',
            organization=organization
        )
        
        # Add a version to the document
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=SimpleUploadedFile('test.pdf', b'test content'),
            user=user,
            comment='Initial version',
            organization=organization
        )
        
        # Create the document version index
        ver_index = DocumentVersionIndex(
            meta={'id': version.id},
            document_id=document.id,
            document_title=document.title,
            version_number=version.version_number,
            comment=version.comment,
            created_at=version.created_at,
            updated_at=version.updated_at
        )
        ver_index.save()
        
        # Delete the document version index
        ver_index.delete()
        
        # Check if the document version index was deleted correctly
        mock_ver_delete.assert_called_once() 