from elasticsearch_dsl import Document, Text, Keyword, Integer, Date, Boolean
from elasticsearch_dsl.connections import connections
from django.conf import settings
import ssl

# Create SSL context if needed
ssl_context = None
if settings.ELASTICSEARCH_USE_SSL:
    ssl_context = ssl.create_default_context()
    if hasattr(settings, 'ELASTICSEARCH_SSL_CONTEXT'):
        # Use custom SSL context settings if available
        if settings.ELASTICSEARCH_SSL_CONTEXT.get('check_hostname') is not None:
            ssl_context.check_hostname = settings.ELASTICSEARCH_SSL_CONTEXT.get('check_hostname')
        if settings.ELASTICSEARCH_SSL_CONTEXT.get('verify_mode') is not None:
            verify_mode = settings.ELASTICSEARCH_SSL_CONTEXT.get('verify_mode')
            if verify_mode == 'CERT_NONE':
                ssl_context.verify_mode = ssl.CERT_NONE
            elif verify_mode == 'CERT_OPTIONAL':
                ssl_context.verify_mode = ssl.CERT_OPTIONAL
            elif verify_mode == 'CERT_REQUIRED':
                ssl_context.verify_mode = ssl.CERT_REQUIRED

# Create Elasticsearch connection
connections.create_connection(
    hosts=[settings.ELASTICSEARCH_DSN],
    basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
    verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS,
    ssl_context=ssl_context
)

class DocumentIndex(Document):
    """
    Elasticsearch document index for documents.
    """
    title = Text(analyzer='standard')
    description = Text(analyzer='standard')
    user_id = Integer()
    status = Keyword()
    created_at = Date()
    updated_at = Date()
    is_deleted = Boolean()

    class Index:
        name = 'documents_documents'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    def save(self, **kwargs):
        skip_signal = kwargs.pop('skip_signal', False)
        if not skip_signal:
            return super().save(**kwargs)
        return super().save(**kwargs)

    def update(self, **kwargs):
        skip_signal = kwargs.pop('skip_signal', False)
        if not skip_signal:
            return super().update(**kwargs)
        return super().update(**kwargs)

    def delete(self, **kwargs):
        skip_signal = kwargs.pop('skip_signal', False)
        if not skip_signal:
            return super().delete(**kwargs)
        return super().delete(**kwargs)

class DocumentVersionIndex(Document):
    """
    Elasticsearch document index for document versions.
    """
    document_id = Integer()
    version_number = Integer()
    user_id = Integer()
    comment = Text(analyzer='standard')
    created_at = Date()
    updated_at = Date()
    is_current = Boolean()

    class Index:
        name = 'documents_versions'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    def save(self, **kwargs):
        skip_signal = kwargs.pop('skip_signal', False)
        if not skip_signal:
            return super().save(**kwargs)
        return super().save(**kwargs)

    def update(self, **kwargs):
        skip_signal = kwargs.pop('skip_signal', False)
        if not skip_signal:
            return super().update(**kwargs)
        return super().update(**kwargs)

    def delete(self, **kwargs):
        skip_signal = kwargs.pop('skip_signal', False)
        if not skip_signal:
            return super().delete(**kwargs)
        return super().delete(**kwargs) 