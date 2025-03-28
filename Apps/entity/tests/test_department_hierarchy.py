import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from Apps.entity.models import Organization, Department
from Apps.users.models import User

@pytest.mark.django_db
class TestDepartmentHierarchy:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def organization(self, user):
        return Organization.objects.create(
            name='Test Org',
            created_by=user
        )

    @pytest.fixture
    def parent_department(self, organization, user):
        return Department.objects.create(
            name='Engineering',
            organization=organization,
            description='Main Engineering Department',
            created_by=user
        )

    def test_create_sub_department(self, parent_department, organization, user):
        """Test creating a sub-department"""
        sub_department = Department.objects.create(
            name='Frontend Engineering',
            organization=organization,
            parent=parent_department,
            description='Frontend Engineering Sub-department',
            created_by=user
        )
        assert sub_department.parent == parent_department
        assert sub_department in parent_department.children.all()
        assert str(sub_department) == 'Frontend Engineering'

    def test_department_hierarchy_depth(self, parent_department, organization, user):
        """Test department hierarchy depth limit"""
        # Create first level sub-department
        sub_dept1 = Department.objects.create(
            name='Level 1 Department',
            organization=organization,
            parent=parent_department,
            created_by=user
        )
        # Create second level sub-department
        sub_dept2 = Department.objects.create(
            name='Level 2 Department',
            organization=organization,
            parent=sub_dept1,
            created_by=user
        )
        # Create third level sub-department
        sub_dept3 = Department.objects.create(
            name='Level 3 Department',
            organization=organization,
            parent=sub_dept2,
            created_by=user
        )
        # Create fourth level sub-department
        sub_dept4 = Department.objects.create(
            name='Level 4 Department',
            organization=organization,
            parent=sub_dept3,
            created_by=user
        )
        
        # Create fifth level sub-department - this should fail based on model validation
        dept5 = Department(
            name='Level 5 Department',
            organization=organization,
            parent=sub_dept4,
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            dept5.full_clean()
        assert "Department hierarchy cannot exceed 5 levels" in str(exc_info.value)

    def test_department_circular_reference(self, parent_department, organization, user):
        """Test preventing circular references in department hierarchy"""
        sub_department = Department.objects.create(
            name='Sub Department',
            organization=organization,
            parent=parent_department,
            created_by=user
        )
        # Try to make parent department a child of its sub-department
        parent_department.parent = sub_department
        with pytest.raises(ValidationError):
            parent_department.full_clean()

    def test_department_organization_consistency(self, parent_department, user):
        """Test that sub-departments must belong to the same organization as parent"""
        other_organization = Organization.objects.create(name='Other Org', created_by=user)
        department = Department(
            name='Invalid Department',
            organization=other_organization,
            parent=parent_department,
            created_by=user
        )
        with pytest.raises(ValidationError):
            department.full_clean()

    def test_department_hierarchy_representation(self, parent_department, organization, user):
        """Test string representation of department hierarchy"""
        sub_department = Department.objects.create(
            name='Sub Department',
            organization=organization,
            parent=parent_department,
            created_by=user
        )
        assert str(sub_department) == 'Sub Department'
        assert sub_department.get_hierarchy_path() == 'Engineering > Sub Department'

    def test_department_hierarchy_queries(self, parent_department, organization, user):
        """Test department hierarchy query methods"""
        sub_dept1 = Department.objects.create(
            name='Sub Department 1',
            organization=organization,
            parent=parent_department,
            created_by=user
        )
        sub_dept2 = Department.objects.create(
            name='Sub Department 2',
            organization=organization,
            parent=parent_department,
            created_by=user
        )
        # Test getting all sub-departments
        assert set(parent_department.children.all()) == {sub_dept1, sub_dept2}
        # Test getting all parent departments
        assert sub_dept1.get_parent_departments() == [parent_department]
        # Test getting root department
        assert sub_dept1.get_root_department() == parent_department

    def test_department_hierarchy_deletion(self, parent_department, organization, user):
        """Test department hierarchy deletion behavior"""
        sub_department = Department.objects.create(
            name='Sub Department',
            organization=organization,
            parent=parent_department,
            created_by=user
        )
        # Delete parent department
        parent_department.delete()
        # Verify sub-department is also soft deleted
        sub_department.refresh_from_db()
        assert not sub_department.is_active 