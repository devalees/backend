import uuid
import os
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

# Use the original RBACBaseModel directly
from Apps.rbac.models import RBACBaseModel
from Apps.rbac.managers import OrganizationIsolationManager
from .storage import document_storage

User = get_user_model()

class Document(RBACBaseModel):
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
        app_label = 'documents'

    def __str__(self):
        return self.title

    def clean(self):
        # Call parent's clean method to validate organization field
        super().clean()
        
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

class DocumentVersion(RBACBaseModel):
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

    # Use both manager types
    objects = models.Manager()
    rbac_objects = OrganizationIsolationManager()

    class Meta:
        ordering = ['-version_number']
        unique_together = [
            ['document', 'branch_name', 'version_number', 'organization']  # Version numbers are unique within a branch and organization
        ]
        indexes = [
            models.Index(fields=['document', 'version_number']),
            models.Index(fields=['is_current']),
            models.Index(fields=['branch_name']),
        ]
        app_label = 'documents'

    def __str__(self):
        return f'{self.document.title} - {self.branch_name} - Version {self.version_number}'

    def clean(self):
        # Call parent's clean method to validate organization field
        super().clean()
        
        if self.version_number < 1:
            raise ValidationError('Version number must be greater than 0')
        if self.parent_version and self.parent_version.document != self.document:
            raise ValidationError('Parent version must belong to the same document')

    def save(self, *args, **kwargs):
        # Ensure organization is consistent with document's organization
        if hasattr(self, 'document') and self.document and not self.organization_id:
            self.organization = self.document.organization
        
        # Version-specific save logic
        if not self.pk:  # New version being created
            # If this version is marked as current, ensure no other version in this branch is current
            if self.is_current:
                print(f"Before update - Original version {self.version_number} is_current: {self.is_current}")
                DocumentVersion.objects.filter(
                    document=self.document,
                    branch_name=self.branch_name,
                    is_current=True
                ).update(is_current=False)
                print(f"After update - Original version {self.version_number} is_current: {self.is_current}")
        
        # Call parent's save method
        super().save(*args, **kwargs)

    @classmethod
    def get_next_version_number(cls, document, branch_name):
        """
        Get the next available version number for a specific document branch.
        
        Args:
            document (Document): The document
            branch_name (str): The branch name
            
        Returns:
            int: Next version number
        """
        latest_version = cls.objects.filter(
            document=document,
            branch_name=branch_name
        ).order_by('-version_number').first()
        
        if latest_version:
            return latest_version.version_number + 1
        else:
            return 1

    def _handle_branch_creation(self, branch_name, user, comment=''):
        """
        Internal method to handle branch creation logic.
        
        Returns:
            DocumentVersion: The new version in the branch
        """
        # Get the file content from the current version
        file_content = self.file.read()
        temp_file = SimpleUploadedFile(
            name=os.path.basename(self.file.name),
            content=file_content
        )
        
        # Create the new branch version
        new_version = DocumentVersion(
            document=self.document,
            version_number=1,  # First version in the branch
            file=temp_file,
            user=user,
            comment=comment or f"Created branch '{branch_name}' from {self.branch_name} version {self.version_number}",
            is_current=True,
            branch_name=branch_name,
            parent_version=self,
            organization=self.organization  # Ensure organization is set correctly
        )
        new_version.save()
        
        return new_version

    def create_branch(self, branch_name, user, comment=''):
        """
        Create a new branch from this version.
        
        Args:
            branch_name (str): Name of the new branch
            user (User): User creating the branch
            comment (str): Optional comment for the branch creation
            
        Returns:
            DocumentVersion: The new version in the branch
            
        Raises:
            ValidationError: If a branch with the same name already exists
        """
        # Check if branch already exists
        if self.document.versions.filter(branch_name=branch_name).exists():
            raise ValidationError(f"Branch '{branch_name}' already exists for this document")
        
        with transaction.atomic():
            return self._handle_branch_creation(branch_name, user, comment)
    
    def merge_to(self, target_version, user, comment=''):
        """
        Merge this version into the target version's branch.
        
        Args:
            target_version (DocumentVersion): The target version to merge into
            user (User): User performing the merge
            comment (str): Optional comment for the merge
            
        Returns:
            DocumentVersion: The new version in the target branch
            
        Raises:
            ValidationError: If versions are not mergeable
        """
        # Validate merge
        if self.document_id != target_version.document_id:
            raise ValidationError("Cannot merge versions from different documents")
        
        if self.branch_name == target_version.branch_name:
            raise ValidationError("Cannot merge versions in the same branch")

        if self.organization_id != target_version.organization_id:
            raise ValidationError("Cannot merge versions from different organizations")
        
        with transaction.atomic():
            # Get the next version number in the target branch
            next_version = self.get_next_version_number(self.document, target_version.branch_name)
            
            # Get the file content from this version
            file_content = self.file.read()
            temp_file = SimpleUploadedFile(
                name=os.path.basename(self.file.name),
                content=file_content
            )
            
            # Create the new merged version
            merge_comment = comment or f"Merged from {self.branch_name} version {self.version_number}"
            merged_version = DocumentVersion(
                document=self.document,
                version_number=next_version,
                file=temp_file,
                user=user,
                comment=merge_comment,
                is_current=True,
                branch_name=target_version.branch_name,
                parent_version=target_version,
                organization=self.organization  # Ensure organization is set correctly
            )
            merged_version.save()
            
            # Update this version to reference the merged version
            self.merged_to = merged_version
            self.save(update_fields=['merged_to'])
            
            return merged_version

    def get_branch_history(self):
        """
        Get the history of the branch this version belongs to.
        
        Returns:
            QuerySet: Ordered queryset of versions in this branch
        """
        return self.document.versions.filter(
            branch_name=self.branch_name,
            organization=self.organization
        ).order_by('version_number')

class DocumentClassification(RBACBaseModel):
    """
    Model for classifying documents into categories.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        # Add unique_together constraint including organization
        unique_together = ['name', 'organization']
        # Add app_label to ensure consistency with RBAC
        app_label = 'documents'

    def __str__(self):
        return self.name

    def clean(self):
        # Call parent's clean method to validate organization field
        super().clean()
        
        if not self.name:
            raise ValidationError('Name is required')

class DocumentTag(RBACBaseModel):
    """
    Model for tagging documents with keywords.
    """
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#000000')  # Hex color code

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
        # Add unique_together constraint including organization
        unique_together = ['name', 'organization']
        # Add app_label to ensure consistency with RBAC
        app_label = 'documents'

    def __str__(self):
        return self.name

    def clean(self):
        # Call parent's clean method to validate organization field
        super().clean()
        
        if not self.name:
            raise ValidationError('Name is required')
        if len(self.color) != 7 or not self.color.startswith('#'):
            raise ValidationError('Color must be a valid HEX color code (e.g., #FF0000)')
