# This file is intentionally left empty.
# It's used by pytest to automatically discover tests in this directory. 

import pytest
from elasticsearch import Elasticsearch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock

from Apps.entity.models import Organization
from Apps.documents.models import Document, DocumentVersion, DocumentClassification, DocumentTag

User = get_user_model()

@pytest.fixture(scope="session")
def es_client():
    """
    Create an Elasticsearch client for testing that uses HTTP instead of HTTPS.
    This fixture will be available for all test functions in the documents app.
    """
    # Create a client using HTTP instead of HTTPS to avoid SSL issues during tests
    es = Elasticsearch(
        ['http://localhost:9201'],
        verify_certs=False,
        basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD) if hasattr(settings, 'ELASTICSEARCH_USERNAME') else None
    )
    
    # Create test index if it doesn't exist
    test_index = f"{settings.ELASTICSEARCH_INDEX_PREFIX}test"
    if not es.indices.exists(index=test_index):
        es.indices.create(
            index=test_index,
            mappings={
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "tags": {"type": "keyword"}
                }
            }
        )
    
    yield es
    
    # Clean up test index
    if es.indices.exists(index=test_index):
        es.indices.delete(index=test_index)

@pytest.fixture
def organization():
    """Fixture to create an organization for testing"""
    return Organization.objects.create(name='Test Organization')

@pytest.fixture
def user():
    """Fixture to create a user for testing"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='password'
    )

@pytest.fixture
def document(user, organization):
    """Fixture to create a document for testing"""
    doc = Document.objects.create(
        title='Test Document',
        description='Test Description',
        user=user,
        organization=organization
    )
    return doc

@pytest.fixture
def document_version(document, user):
    """Fixture to create a document version for testing"""
    version = DocumentVersion.objects.create(
        document=document,
        version_number=1,
        file=SimpleUploadedFile('test.pdf', b'test content'),
        user=user,
        organization=document.organization
    )
    return version

@pytest.fixture
def document_classification(organization):
    """Fixture to create a document classification for testing"""
    return DocumentClassification.objects.create(
        name='Test Classification',
        description='Test Description',
        organization=organization
    )

@pytest.fixture
def document_tag(organization):
    """Fixture to create a document tag for testing"""
    return DocumentTag.objects.create(
        name='Test Tag',
        color='#FF0000',
        organization=organization
    )

@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch calls for testing"""
    with patch('elasticsearch_dsl.connections.create_connection') as mock_es:
        with patch('Apps.documents.search.DocumentIndex.save') as mock_doc_save:
            with patch('Apps.documents.search.DocumentIndex.get') as mock_doc_get:
                with patch('Apps.documents.search.DocumentIndex.delete') as mock_doc_delete:
                    with patch('Apps.documents.search.DocumentVersionIndex.save') as mock_ver_save:
                        with patch('Apps.documents.search.DocumentVersionIndex.get') as mock_ver_get:
                            with patch('Apps.documents.search.DocumentVersionIndex.delete') as mock_ver_delete:
                                yield mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete

@pytest.fixture
def mock_signals():
    """Mock signals for testing"""
    with patch('Apps.documents.signals.document_post_save') as mock_doc_signal:
        with patch('Apps.documents.signals.document_version_post_save') as mock_ver_signal:
            with patch('elasticsearch_dsl.connections.create_connection') as mock_es:
                with patch('Apps.documents.search.DocumentIndex.save') as mock_doc_save:
                    with patch('Apps.documents.search.DocumentIndex.get') as mock_doc_get:
                        with patch('Apps.documents.search.DocumentIndex.delete') as mock_doc_delete:
                            with patch('Apps.documents.search.DocumentVersionIndex.save') as mock_ver_save:
                                with patch('Apps.documents.search.DocumentVersionIndex.get') as mock_ver_get:
                                    with patch('Apps.documents.search.DocumentVersionIndex.delete') as mock_ver_delete:
                                        yield mock_doc_signal, mock_ver_signal, mock_es, mock_doc_save, mock_doc_get, mock_doc_delete, mock_ver_save, mock_ver_get, mock_ver_delete 