import os
import uuid
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils import timezone

class DocumentStorage(FileSystemStorage):
    """
    Custom storage class for document files.
    Implements organization by date and document ID.
    """
    def __init__(self, location=None, base_url=None):
        super().__init__(location=location or settings.MEDIA_ROOT, base_url=base_url)

    def get_upload_path(self, name, user):
        """Generate a unique path for uploaded files."""
        now = timezone.now()
        return os.path.join('documents', str(now.year), str(now.month), str(user.id), name)

    def get_available_name(self, name, max_length=None):
        """Generate a unique name for the file."""
        if max_length is None:
            max_length = 255

        # Split the path into directory and filename
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        
        # If the file doesn't exist, return the original name
        if not self.exists(name):
            return name

        # Generate a new name using UUID
        max_attempts = 10  # Safety limit to prevent infinite loops
        attempt = 0
        
        while attempt < max_attempts:
            # Generate a unique identifier
            unique_id = uuid.uuid4().hex[:8]
            new_file_name = f"{file_root}_{unique_id}{file_ext}"
            
            # Check if the new name would exceed max_length
            if len(new_file_name) > max_length:
                # Truncate the name while preserving the extension
                new_file_name = f"{file_root}_{unique_id[:max_length-len(file_ext)-1]}{file_ext}"
            
            # Reconstruct the full path if there was a directory
            if dir_name:
                new_name = os.path.join(dir_name, new_file_name)
            else:
                new_name = new_file_name
            
            # Check if the new name exists
            if not self.exists(new_name):
                return new_name
                
            attempt += 1
            
        # If we've exhausted all attempts, raise an error
        raise ValueError(f"Could not generate a unique name for {name} after {max_attempts} attempts")

    def get_valid_name(self, name):
        """
        Returns a filename, based on the provided filename, that's suitable for use
        in the target storage system.
        """
        return name

    def save(self, name, content, max_length=None):
        """Save the file with a unique name."""
        if name is None:
            name = content.name

        if max_length is None:
            max_length = 255

        name = self.get_available_name(name, max_length)
        return super().save(name, content)

# Create a default storage instance
document_storage = DocumentStorage() 