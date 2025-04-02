import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from unittest.mock import patch

from ..models import Document, DocumentVersion

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', email='testuser@example.com', password='testpass')

@pytest.fixture
def another_user(db):
    return User.objects.create_user(username='anotheruser', email='anotheruser@example.com', password='testpass')

@pytest.fixture
def document(user):
    doc = Document.objects.create(
        title='Test Document',
        file=SimpleUploadedFile('test.txt', b'Initial content'),
        user=user
    )
    return doc

@pytest.fixture
def main_version(document, user):
    version = DocumentVersion.objects.create(
        document=document,
        version_number=1,
        file=SimpleUploadedFile('test_v1.txt', b'Version 1 content'),
        user=user,
        comment='Initial version',
        is_current=True,
        branch_name='main'
    )
    return version

@pytest.fixture
@patch('Apps.documents.signals.document_post_save')
def disable_signals(mock_signal):
    return mock_signal

class TestVersionBranching:
    def test_create_branch(self, main_version, another_user):
        """Test creating a new branch from an existing version."""
        feature_version = main_version.create_branch(
            branch_name='feature',
            user=another_user,
            comment='Starting feature work'
        )

        assert feature_version.branch_name == 'feature'
        assert feature_version.version_number == 1
        assert feature_version.parent_version == main_version
        assert feature_version.is_current
        assert feature_version.user == another_user
        assert feature_version.document == main_version.document

    def test_create_duplicate_branch(self, main_version, another_user):
        """Test that creating a branch with an existing name raises an error."""
        main_version.create_branch('feature', another_user)
        
        with pytest.raises(ValidationError) as exc:
            main_version.create_branch('feature', another_user)
        assert 'Branch feature already exists' in str(exc.value)

    def test_merge_branches(self, main_version, another_user):
        """Test merging a branch back into main."""
        # Create feature branch
        feature_version = main_version.create_branch('feature', another_user)
        
        # Make changes in feature branch
        feature_v2 = DocumentVersion.objects.create(
            document=feature_version.document,
            version_number=2,
            file=SimpleUploadedFile('feature_v2.txt', b'Feature changes'),
            user=another_user,
            comment='Feature changes',
            branch_name='feature',
            parent_version=feature_version,
            is_current=True
        )
        
        # Merge feature branch back to main
        merged_version = feature_v2.merge_to(main_version, another_user)
        
        assert merged_version.branch_name == 'main'
        assert merged_version.version_number == 2
        assert merged_version.parent_version == main_version
        assert merged_version.is_current
        assert feature_v2.merged_to == merged_version

    def test_merge_different_documents(self, main_version, another_user):
        """Test that merging versions from different documents raises an error."""
        # Create another document and version
        other_doc = Document.objects.create(
            title='Other Document',
            file=SimpleUploadedFile('other.txt', b'Other content'),
            user=another_user
        )
        other_version = DocumentVersion.objects.create(
            document=other_doc,
            version_number=1,
            file=SimpleUploadedFile('other_v1.txt', b'Other version'),
            user=another_user,
            is_current=True
        )
        
        with pytest.raises(ValidationError) as exc:
            main_version.merge_to(other_version, another_user)
        assert 'Cannot merge versions from different documents' in str(exc.value)

    def test_branch_history(self, main_version, another_user):
        """Test getting the history of versions in a branch."""
        # Create multiple versions in main branch
        v2 = DocumentVersion.objects.create(
            document=main_version.document,
            version_number=2,
            file=SimpleUploadedFile('main_v2.txt', b'Main v2'),
            user=another_user,
            comment='Main v2',
            branch_name='main',
            parent_version=main_version,
            is_current=True
        )
        
        history = v2.get_branch_history()
        versions = list(history)
        
        assert len(versions) == 2
        assert versions[0] == main_version
        assert versions[1] == v2
        assert all(v.branch_name == 'main' for v in versions)

    def test_current_version_per_branch(self, main_version, another_user):
        """Test that each branch maintains its own current version."""
        # Create feature branch
        feature_version = main_version.create_branch('feature', another_user)
        
        # Create new version in main
        main_v2 = DocumentVersion.objects.create(
            document=main_version.document,
            version_number=2,
            file=SimpleUploadedFile('main_v2.txt', b'Main v2'),
            user=another_user,
            comment='Main v2',
            branch_name='main',
            parent_version=main_version,
            is_current=True
        )
        
        # Create new version in feature
        feature_v2 = DocumentVersion.objects.create(
            document=feature_version.document,
            version_number=2,
            file=SimpleUploadedFile('feature_v2.txt', b'Feature v2'),
            user=another_user,
            comment='Feature v2',
            branch_name='feature',
            parent_version=feature_version,
            is_current=True
        )
        
        # Set is_current flags using update()
        DocumentVersion.objects.filter(pk=main_v2.pk).update(is_current=True)
        DocumentVersion.objects.filter(pk=feature_v2.pk).update(is_current=True)
        DocumentVersion.objects.filter(pk=main_version.pk).update(is_current=False)
        DocumentVersion.objects.filter(pk=feature_version.pk).update(is_current=False)
        
        # Refresh instances from database
        main_version.refresh_from_db()
        feature_version.refresh_from_db()
        main_v2.refresh_from_db()
        feature_v2.refresh_from_db()
        
        # Verify current versions
        main_current = DocumentVersion.objects.get(
            document=main_version.document,
            branch_name='main',
            is_current=True
        )
        feature_current = DocumentVersion.objects.get(
            document=feature_version.document,
            branch_name='feature',
            is_current=True
        )
        
        assert main_current == main_v2
        assert feature_current == feature_v2
        assert not main_version.is_current  # Original main version should not be current
        assert not feature_version.is_current  # Original feature version should not be current 