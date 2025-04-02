from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Document, DocumentVersion
from .search import DocumentIndex, DocumentVersionIndex

@receiver(post_save, sender=Document)
def document_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for document post-save events.
    Indexes documents in Elasticsearch.
    """
    if created:
        DocumentIndex(
            meta={'id': instance.id},
            title=instance.title,
            description=instance.description,
            user_id=instance.user.id,
            status=instance.status,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
            is_deleted=instance.is_deleted
        ).save(skip_signal=True)
    else:
        try:
            doc = DocumentIndex.get(id=instance.id)
            doc.title = instance.title
            doc.description = instance.description
            doc.user_id = instance.user.id
            doc.status = instance.status
            doc.updated_at = instance.updated_at
            doc.is_deleted = instance.is_deleted
            doc.save(skip_signal=True)
        except:
            # If document doesn't exist in index, create it
            DocumentIndex(
                meta={'id': instance.id},
                title=instance.title,
                description=instance.description,
                user_id=instance.user.id,
                status=instance.status,
                created_at=instance.created_at,
                updated_at=instance.updated_at,
                is_deleted=instance.is_deleted
            ).save(skip_signal=True)

@receiver(post_delete, sender=Document)
def document_post_delete(sender, instance, **kwargs):
    """
    Signal handler for document post-delete events.
    Removes document from Elasticsearch index.
    """
    try:
        doc = DocumentIndex.get(id=instance.id)
        doc.delete(skip_signal=True)
    except:
        pass

@receiver(post_save, sender=DocumentVersion)
def document_version_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for document version post-save events.
    Indexes document versions in Elasticsearch.
    """
    if created:
        DocumentVersionIndex(
            meta={'id': instance.id},
            document_id=instance.document.id,
            version_number=instance.version_number,
            user_id=instance.user.id,
            comment=instance.comment,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
            is_current=instance.is_current
        ).save(skip_signal=True)
    else:
        try:
            doc = DocumentVersionIndex.get(id=instance.id)
            doc.document_id = instance.document.id
            doc.version_number = instance.version_number
            doc.user_id = instance.user.id
            doc.comment = instance.comment
            doc.updated_at = instance.updated_at
            doc.is_current = instance.is_current
            doc.save(skip_signal=True)
        except:
            # If version doesn't exist in index, create it
            DocumentVersionIndex(
                meta={'id': instance.id},
                document_id=instance.document.id,
                version_number=instance.version_number,
                user_id=instance.user.id,
                comment=instance.comment,
                created_at=instance.created_at,
                updated_at=instance.updated_at,
                is_current=instance.is_current
            ).save(skip_signal=True)

@receiver(post_delete, sender=DocumentVersion)
def document_version_post_delete(sender, instance, **kwargs):
    """
    Signal handler for document version post-delete events.
    Removes version from Elasticsearch index.
    """
    try:
        doc = DocumentVersionIndex.get(id=instance.id)
        doc.delete(skip_signal=True)
    except:
        pass 