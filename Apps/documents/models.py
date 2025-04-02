from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from .storage import document_storage

User = get_user_model()

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    `created_at` and `updated_at` fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Document(TimeStampedModel):
    """
    Model representing a document in the system.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('approved', 'Approved'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=255, blank=False)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    file = models.FileField(upload_to='documents/%Y/%m/%d/', storage=document_storage, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='documents')
    classification = models.ForeignKey('DocumentClassification', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField('DocumentTag', blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if not self.title:
            raise ValidationError('Title is required')

    def compare_versions(self, version1, version2):
        """
        Compare two versions of the document.
        
        Args:
            version1 (DocumentVersion): First version to compare
            version2 (DocumentVersion): Second version to compare
            
        Returns:
            dict: Dictionary containing comparison results
        """
        if version1.document != self or version2.document != self:
            raise ValueError("Versions must belong to the same document")
            
        return {
            'version_numbers': (version1.version_number, version2.version_number),
            'creation_times': (version1.created_at, version2.created_at),
            'file_sizes': (version1.file.size, version2.file.size),
            'comments': (version1.comment, version2.comment),
            'users': (version1.user, version2.user)
        }

    def restore_version(self, version, skip_index=False):
        """
        Restore the document to a previous version.
        
        Args:
            version (DocumentVersion): The version to restore to
            skip_index (bool): If True, skip updating the Elasticsearch index (useful for testing)
        
        Returns:
            Document: The updated document instance
        
        Raises:
            ValueError: If the version does not belong to this document
        """
        if version.document_id != self.id:
            raise ValueError("Cannot restore version from a different document")
        
        self.current_version = version
        self.last_modified = timezone.now()
        self.save()
        
        if not skip_index:
            # Update Elasticsearch index
            from .search import DocumentIndex
            doc = DocumentIndex(
                meta={'id': self.id},
                title=self.title,
                content=self.current_version.content,
                file_type=self.file_type,
                last_modified=self.last_modified
            )
            doc.save()
        
        return self

    def get_version_history(self):
        """
        Get the complete version history of the document.
        
        Returns:
            QuerySet: Ordered queryset of all versions
        """
        return self.versions.order_by('version_number')

class DocumentVersionManager(models.Manager):
    def create(self, **kwargs):
        # Create the instance but don't save it yet
        instance = self.model(**kwargs)
        
        # If is_current is True, set all other versions in the same branch to False
        if instance.is_current:
            self.filter(
                document=instance.document,
                branch_name=instance.branch_name,
                is_current=True
            ).update(is_current=False)
        
        # Now save the instance
        instance.save(force_insert=True)
        return instance

class DocumentVersion(TimeStampedModel):
    """
    Model representing a version of a document.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    file = models.FileField(upload_to='documents/versions/%Y/%m/%d/', storage=document_storage)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    comment = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)
    branch_name = models.CharField(max_length=100, default='main')
    parent_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='branches')
    merged_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='merged_from')

    objects = models.Manager()

    class Meta:
        ordering = ['-version_number']
        unique_together = [
            ['document', 'branch_name', 'version_number']  # Version numbers are unique within a branch
        ]
        indexes = [
            models.Index(fields=['document', 'version_number']),
            models.Index(fields=['is_current']),
            models.Index(fields=['branch_name']),
        ]

    def __str__(self):
        return f'{self.document.title} - {self.branch_name} - Version {self.version_number}'

    def clean(self):
        if self.version_number < 1:
            raise ValidationError('Version number must be greater than 0')
        if self.parent_version and self.parent_version.document != self.document:
            raise ValidationError('Parent version must belong to the same document')
        if self.merged_to and self.merged_to.document != self.document:
            raise ValidationError('Merged to version must belong to the same document')

    def save(self, *args, **kwargs):
        """
        Override save method to handle is_current flag and version numbers.
        """
        # Set version number for new instances
        if not self.pk and not self.version_number:
            latest_version = DocumentVersion.objects.filter(
                document=self.document,
                branch_name=self.branch_name
            ).order_by('-version_number').first()
            self.version_number = (latest_version.version_number + 1) if latest_version else 1

        # Handle is_current flag within a transaction
        with transaction.atomic():
            # If this version is being set as current, update other versions in the SAME branch
            if self.is_current:
                DocumentVersion.objects.filter(
                    document=self.document,
                    branch_name=self.branch_name,
                    is_current=True
                ).exclude(pk=self.pk).update(is_current=False)

            # Save the instance
            super().save(*args, **kwargs)

            # Refresh the instance to get the latest state
            if self.pk:
                self.refresh_from_db()

    @classmethod
    def get_next_version_number(cls, document, branch_name):
        """
        Get the next version number for a document in a specific branch.
        
        Args:
            document (Document): The document instance
            branch_name (str): The branch name
            
        Returns:
            int: The next version number
        """
        last_version = cls.objects.filter(
            document=document,
            branch_name=branch_name
        ).order_by('-version_number').first()
        
        return (last_version.version_number + 1) if last_version else 1

    def _handle_branch_creation(self, branch_name, user, comment=''):
        """
        Internal method to handle the creation of a new branch.
        This method should be called within a transaction.
        
        Args:
            branch_name (str): Name of the new branch
            user (User): User creating the branch
            comment (str): Optional comment for the branch creation
            
        Returns:
            DocumentVersion: The new version in the branch
        """
        print(f"Before update - Original version {self.pk} is_current: {self.is_current}")
        
        # First, set this version as not current using update to bypass save() logic
        DocumentVersion.objects.filter(pk=self.pk).update(is_current=False)
        
        # Refresh the instance from the database to reflect the update
        self.refresh_from_db()
        
        print(f"After update - Original version {self.pk} is_current: {self.is_current}")
        
        # Create the new version in the branch
        new_version = DocumentVersion.objects.create(
            document=self.document,
            version_number=1,  # Always start a new branch at version 1
            file=self.file,
            user=user,
            comment=comment or f'Created branch {branch_name} from {self.branch_name} version {self.version_number}',
            branch_name=branch_name,
            parent_version=self,
            is_current=True  # New branch's first version is always current
        )
        
        print(f"After create - New version {new_version.pk} is_current: {new_version.is_current}")
        print(f"After create - Original version {self.pk} is_current: {DocumentVersion.objects.get(pk=self.pk).is_current}")
        
        # Refresh both instances from database
        self.refresh_from_db()
        new_version.refresh_from_db()
        
        print(f"After refresh - New version {new_version.pk} is_current: {new_version.is_current}")
        print(f"After refresh - Original version {self.pk} is_current: {self.is_current}")
        
        return new_version

    def create_branch(self, branch_name, user, comment=''):
        """
        Create a new branch from this version.
        
        Args:
            branch_name (str): Name of the new branch
            user (User): User creating the branch
            comment (str): Optional comment for the new version
            
        Returns:
            DocumentVersion: The newly created version in the new branch
            
        Raises:
            ValidationError: If a branch with the given name already exists
        """
        # Check if branch already exists
        if DocumentVersion.objects.filter(document=self.document, branch_name=branch_name).exists():
            raise ValidationError(f'Branch {branch_name} already exists')

        # Create new version in the new branch within a transaction
        with transaction.atomic():
            # First, set this version as not current using update to bypass save() logic
            DocumentVersion.objects.filter(pk=self.pk).update(is_current=False)
            
            # Refresh the instance from the database
            self.refresh_from_db()

            # Create the new version in the new branch
            new_version = DocumentVersion.objects.create(
                document=self.document,
                version_number=1,  # Start with version 1 in the new branch
                file=self.file,  # Copy the file from the current version
                user=user,
                comment=comment or f'Created branch {branch_name}',
                is_current=True,  # This will be the current version in the new branch
                branch_name=branch_name,
                parent_version=self
            )

            # Ensure the new version is current and the original version is not
            DocumentVersion.objects.filter(pk=new_version.pk).update(is_current=True)
            DocumentVersion.objects.filter(pk=self.pk).update(is_current=False)

            # Refresh both instances from the database
            self.refresh_from_db()
            new_version.refresh_from_db()

            return new_version

    def merge_to(self, target_version, user, comment=''):
        """
        Merge this version into another branch.
        
        Args:
            target_version (DocumentVersion): Version to merge into
            user (User): User performing the merge
            comment (str): Optional comment for the merge
            
        Returns:
            DocumentVersion: The new version created by the merge
            
        Raises:
            ValidationError: If versions are not from the same document
        """
        if self.document != target_version.document:
            raise ValidationError('Cannot merge versions from different documents')
            
        # Get the next version number for the target branch
        next_version = 1
        latest_version = DocumentVersion.objects.filter(
            document=self.document,
            branch_name=target_version.branch_name
        ).order_by('-version_number').first()
        if latest_version:
            next_version = latest_version.version_number + 1
            
        # Create new version in the target branch
        merged_version = DocumentVersion.objects.create(
            document=self.document,
            version_number=next_version,
            file=self.file,
            user=user,
            comment=comment or f'Merged from {self.branch_name} version {self.version_number}',
            branch_name=target_version.branch_name,
            parent_version=target_version,
            is_current=True
        )
        
        # Update the merged_to reference
        self.merged_to = merged_version
        self.save()
        
        return merged_version

    def get_branch_history(self):
        """
        Get the complete history of versions in this branch.
        
        Returns:
            QuerySet: Ordered queryset of all versions in the branch
        """
        return DocumentVersion.objects.filter(
            document=self.document,
            branch_name=self.branch_name
        ).order_by('version_number')

class DocumentClassification(TimeStampedModel):
    """
    Model for classifying documents into categories.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if not self.name:
            raise ValidationError('Name is required')

class DocumentTag(TimeStampedModel):
    """
    Model for tagging documents with keywords.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#000000')  # Hex color code

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if not self.name:
            raise ValidationError('Name is required')
