import pytest
from django.contrib.auth.models import Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
from rest_framework.permissions import SAFE_METHODS
from ..permissions import (
    IsConfigOwnerOrReadOnly,
    CanPerformImportExport,
    CanViewLogs,
    CanManageImportExport
)
from .factories import (
    UserFactory,
    ImportExportConfigFactory,
    ImportExportLogFactory,
    ContentTypeFactory
)
from ..models import ImportExportConfig, ImportExportLog


@pytest.fixture
def request_factory():
    """Fixture for creating API requests."""
    return APIRequestFactory()


@pytest.fixture
def regular_user():
    """Fixture for a regular authenticated user."""
    return UserFactory()


@pytest.fixture
def superuser():
    """Fixture for a superuser."""
    return UserFactory(is_superuser=True)


@pytest.fixture
def user_with_permissions():
    """Fixture for a user with import/export permissions."""
    user = UserFactory()
    content_type = ContentType.objects.get_for_model(ImportExportConfig)
    permission = Permission.objects.get(
        content_type=content_type,
        codename='manage_import_export'
    )
    user.user_permissions.add(permission)
    return user


@pytest.mark.django_db
class TestIsConfigOwnerOrReadOnly:
    """Test cases for IsConfigOwnerOrReadOnly permission."""

    def test_has_permission_unauthenticated(self, request_factory):
        """Test permission for unauthenticated users."""
        request = request_factory.get('/')
        request.user = AnonymousUser()
        permission = IsConfigOwnerOrReadOnly()
        assert permission.has_permission(request, None) is False

    def test_has_permission_authenticated(self, request_factory, regular_user):
        """Test permission for authenticated users."""
        request = request_factory.get('/')
        request.user = regular_user
        permission = IsConfigOwnerOrReadOnly()
        assert permission.has_permission(request, None) is True

    def test_has_object_permission_safe_method(self, request_factory, regular_user):
        """Test object permission for safe methods."""
        request = request_factory.get('/')
        request.user = regular_user
        config = ImportExportConfigFactory()
        permission = IsConfigOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, config) is True

    def test_has_object_permission_owner(self, request_factory, regular_user):
        """Test object permission for owner."""
        request = request_factory.post('/')
        request.user = regular_user
        config = ImportExportConfigFactory(created_by=regular_user)
        permission = IsConfigOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, config) is True

    def test_has_object_permission_non_owner(self, request_factory, regular_user):
        """Test object permission for non-owner."""
        request = request_factory.post('/')
        request.user = regular_user
        config = ImportExportConfigFactory(created_by=UserFactory())
        permission = IsConfigOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, config) is False


@pytest.mark.django_db
class TestCanPerformImportExport:
    """Test cases for CanPerformImportExport permission."""

    def test_has_permission_unauthenticated(self, request_factory):
        """Test permission for unauthenticated users."""
        request = request_factory.get('/')
        request.user = AnonymousUser()
        permission = CanPerformImportExport()
        assert permission.has_permission(request, None) is False

    def test_has_permission_authenticated(self, request_factory, regular_user):
        """Test permission for authenticated users."""
        request = request_factory.get('/')
        request.user = regular_user
        permission = CanPerformImportExport()
        assert permission.has_permission(request, None) is True

    def test_has_object_permission_unauthenticated(self, request_factory):
        """Test object permission for unauthenticated users."""
        request = request_factory.get('/')
        request.user = AnonymousUser()
        config = ImportExportConfigFactory()
        permission = CanPerformImportExport()
        assert permission.has_object_permission(request, None, config) is False

    def test_has_object_permission_authenticated(self, request_factory, regular_user):
        """Test object permission for authenticated users."""
        request = request_factory.get('/')
        request.user = regular_user
        config = ImportExportConfigFactory()
        permission = CanPerformImportExport()
        assert permission.has_object_permission(request, None, config) is True


@pytest.mark.django_db
class TestCanViewLogs:
    """Test cases for CanViewLogs permission."""

    def test_has_permission_unauthenticated(self, request_factory):
        """Test permission for unauthenticated users."""
        request = request_factory.get('/')
        request.user = AnonymousUser()
        permission = CanViewLogs()
        assert permission.has_permission(request, None) is False

    def test_has_permission_authenticated(self, request_factory, regular_user):
        """Test permission for authenticated users."""
        request = request_factory.get('/')
        request.user = regular_user
        permission = CanViewLogs()
        assert permission.has_permission(request, None) is True

    def test_has_object_permission_unauthenticated(self, request_factory):
        """Test object permission for unauthenticated users."""
        request = request_factory.get('/')
        request.user = AnonymousUser()
        log = ImportExportLogFactory()
        permission = CanViewLogs()
        assert permission.has_object_permission(request, None, log) is False

    def test_has_object_permission_authenticated(self, request_factory, regular_user):
        """Test object permission for authenticated users."""
        request = request_factory.get('/')
        request.user = regular_user
        log = ImportExportLogFactory()
        permission = CanViewLogs()
        assert permission.has_object_permission(request, None, log) is True


@pytest.mark.django_db
class TestCanManageImportExport:
    """Test cases for CanManageImportExport permission."""

    def test_has_permission_unauthenticated(self, request_factory):
        """Test permission for unauthenticated user."""
        request = request_factory.get('/')
        request.user = AnonymousUser()
        permission = CanManageImportExport()
        assert permission.has_permission(request, None) is False

    def test_has_permission_superuser(self, request_factory, superuser):
        """Test permission for superuser."""
        request = request_factory.get('/')
        request.user = superuser
        permission = CanManageImportExport()
        assert permission.has_permission(request, None) is True

    def test_has_permission_user_with_permissions(self, request_factory, user_with_permissions):
        """Test permission for user with import/export permissions."""
        request = request_factory.get('/')
        request.user = user_with_permissions
        permission = CanManageImportExport()
        assert permission.has_permission(request, None) is True

    def test_has_permission_regular_user(self, request_factory, regular_user):
        """Test permission for regular user."""
        request = request_factory.get('/')
        request.user = regular_user
        permission = CanManageImportExport()
        assert permission.has_permission(request, None) is False

    def test_has_object_permission_unauthenticated(self, request_factory):
        """Test object permission for unauthenticated user."""
        request = request_factory.get('/')
        request.user = AnonymousUser()
        config = ImportExportConfigFactory()
        permission = CanManageImportExport()
        assert permission.has_object_permission(request, None, config) is False

    def test_has_object_permission_superuser(self, request_factory, superuser):
        """Test object permission for superuser."""
        request = request_factory.get('/')
        request.user = superuser
        config = ImportExportConfigFactory()
        permission = CanManageImportExport()
        assert permission.has_object_permission(request, None, config) is True

    def test_has_object_permission_user_with_permissions(self, request_factory, user_with_permissions):
        """Test object permission for user with import/export permissions."""
        request = request_factory.get('/')
        request.user = user_with_permissions
        config = ImportExportConfigFactory()
        permission = CanManageImportExport()
        assert permission.has_object_permission(request, None, config) is True

    def test_has_object_permission_regular_user(self, request_factory, regular_user):
        """Test object permission for regular user."""
        request = request_factory.get('/')
        request.user = regular_user
        config = ImportExportConfigFactory()
        permission = CanManageImportExport()
        assert permission.has_object_permission(request, None, config) is False

    def test_has_object_permission_with_content_type(self, request_factory, user_with_permissions):
        """Test object permission with content type."""
        request = request_factory.get('/')
        request.user = user_with_permissions
        content_type = ContentTypeFactory()
        permission = CanManageImportExport()
        assert permission.has_object_permission(request, None, content_type) is True 