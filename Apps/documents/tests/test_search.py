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
    def test_document_index_creation(self, user, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft'
        )
        index = DocumentIndex(meta={'id': document.id})
        index.title = document.title
        index.description = document.description
        index.user_id = document.user.id
        index.status = document.status
        index.created_at = document.created_at
        index.updated_at = document.updated_at
        index.is_deleted = document.is_deleted

        index.save()
        assert mock_doc_save.call_count == 2
        assert mock_doc_save.call_args_list == [
            call(skip_signal=True),
            call()
        ]

    def test_document_index_update(self, user, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft'
        )
        mock_doc_get.return_value = DocumentIndex(meta={'id': document.id})
        index = DocumentIndex.get(id=document.id)
        index.title = 'Updated Title'
        index.description = 'Updated Description'
        index.save()
        assert mock_doc_save.call_count == 2
        assert mock_doc_save.call_args_list == [
            call(skip_signal=True),
            call()
        ]

    def test_document_index_deletion(self, user, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
        document = Document.objects.create(
            title='Test Document',
            description='Test Description',
            user=user,
            status='draft'
        )
        index = DocumentIndex(meta={'id': document.id})
        index.delete()
        mock_doc_delete.assert_called_once()

@pytest.mark.django_db
class TestDocumentVersionIndex:
    def test_document_version_index_creation(self, user, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
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
        index = DocumentVersionIndex(meta={'id': version.id})
        index.document_id = version.document.id
        index.version_number = version.version_number
        index.user_id = version.user.id
        index.comment = version.comment
        index.created_at = version.created_at
        index.updated_at = version.updated_at
        index.is_current = version.is_current

        index.save()
        assert mock_ver_save.call_count == 2
        assert mock_ver_save.call_args_list == [
            call(skip_signal=True),
            call()
        ]

    def test_document_version_index_update(self, user, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
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
        mock_ver_get.return_value = DocumentVersionIndex(meta={'id': version.id})
        index = DocumentVersionIndex.get(id=version.id)
        index.version_number = 2
        index.comment = 'Updated comment'
        index.save()
        assert mock_ver_save.call_count == 2
        assert mock_ver_save.call_args_list == [
            call(skip_signal=True),
            call()
        ]

    def test_document_version_index_deletion(self, user, mock_elasticsearch):
        mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete = mock_elasticsearch
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
        index = DocumentVersionIndex(meta={'id': version.id})
        index.delete()
        mock_ver_delete.assert_called_once() 