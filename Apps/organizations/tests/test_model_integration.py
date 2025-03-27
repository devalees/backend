import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from Apps.organizations.models import Organization, Department, Team, TeamMember
from Apps.users.models import User

@pytest.mark.django_db
class TestDepartmentIntegration:
    @pytest.fixture
    def organization(self):
        return Organization.objects.create(name="Test Org")

    @pytest.fixture
    def department(self, organization):
        return Department.objects.create(name="Test Dept", organization=organization)

    @pytest.fixture
    def team(self, department):
        return Team.objects.create(name="Test Team", department=department)

    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="testuser", password="testpass")

    def test_department_field_constraints(self, organization):
        """Test department field constraints"""
        # Test name length
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(
                name="A" * 101,  # Assuming max length is 100
                organization=organization
            )
        assert "Ensure this value has at most 100 characters" in str(exc_info.value)

        # Test unique name within organization
        Department.objects.create(name="Test Dept", organization=organization)
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(name="Test Dept", organization=organization)
        assert "A department with this name already exists in this organization" in str(exc_info.value)

    def test_department_organization_relationship(self, organization):
        """Test department-organization relationship"""
        # Test department creation
        department = Department.objects.create(name="Test Dept", organization=organization)
        assert department.organization == organization
        assert department in organization.departments.all()

        # Test department deletion
        department.delete()
        assert department not in organization.departments.all()

    def test_department_hierarchy(self, organization):
        """Test department hierarchy"""
        parent = Department.objects.create(name="Parent Dept", organization=organization)
        child = Department.objects.create(name="Child Dept", organization=organization, parent=parent)
        
        assert child.parent == parent
        assert child in parent.children.all()
        assert parent in child.get_parent_departments()

    def test_department_soft_delete(self, organization):
        """Test department soft delete"""
        department = Department.objects.create(name="Test Dept", organization=organization)
        department.delete()
        
        assert not department.is_active
        assert department in Department.objects.all()
        assert department not in Department.objects.filter(is_active=True)

    def test_department_cascade_soft_delete(self, organization):
        """Test department cascade soft delete"""
        parent = Department.objects.create(name="Parent Dept", organization=organization)
        child = Department.objects.create(name="Child Dept", organization=organization, parent=parent)
        
        parent.delete()
        child.refresh_from_db()
        
        assert not child.is_active

    def test_department_reactivation(self, organization):
        """Test department reactivation"""
        department = Department.objects.create(name="Test Dept", organization=organization)
        department.delete()
        
        department.is_active = True
        department.save()
        
        assert department.is_active
        assert department in Department.objects.filter(is_active=True)

    def test_department_organization_constraints(self, organization):
        """Test department-organization constraints"""
        other_org = Organization.objects.create(name="Other Org")
        other_dept = Department.objects.create(name="Other Dept", organization=other_org)
        
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(
                name="Test Dept",
                organization=organization,
                parent=other_dept
            )
        assert "Parent department must belong to the same organization" in str(exc_info.value)

    def test_department_circular_reference(self, organization):
        """Test department circular reference prevention"""
        dept1 = Department.objects.create(name="Dept 1", organization=organization)
        dept2 = Department.objects.create(name="Dept 2", organization=organization)
        dept3 = Department.objects.create(name="Dept 3", organization=organization)
        
        dept2.parent = dept1
        dept2.save()
        dept3.parent = dept2
        dept3.save()
        
        with pytest.raises(ValidationError) as exc_info:
            dept1.parent = dept3
            dept1.save()
        assert "Circular reference detected in department hierarchy" in str(exc_info.value)

    def test_department_max_depth(self, organization):
        """Test department maximum depth constraint"""
        parent = None
        for i in range(5):  # Create 5 levels
            dept = Department.objects.create(
                name=f"Dept {i}",
                organization=organization,
                parent=parent
            )
            parent = dept
        
        with pytest.raises(ValidationError) as exc_info:
            dept = Department(
                name="Too Deep",
                organization=organization,
                parent=parent
            )
            dept.full_clean()
        assert "Department hierarchy cannot exceed 5 levels" in str(exc_info.value) 