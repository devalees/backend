from elasticsearch_dsl import Document, Text, Keyword, Integer, Date, Boolean
from elasticsearch_dsl.connections import connections
from django.conf import settings

# Create Elasticsearch connection
connections.create_connection(hosts=[settings.ELASTICSEARCH_DSN])

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