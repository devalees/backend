import pytest
from django.test import TestCase
from django.db import connection
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import migrations
from Apps.entity.models import Organization, Department, Team

class TestOrganizationModelConstraints(TestCase):
    """Test suite for Organization model constraints and validations."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.org_data = {
            'name': 'Test Organization',
            'description': 'Test Description',
            'is_active': True,
            'created_by': self.user
        }

    def test_organization_creation(self):
        """Test that an organization can be created with valid data."""
        org = Organization.objects.create(**self.org_data)
        self.assertEqual(org.name, self.org_data['name'])
        self.assertEqual(org.description, self.org_data['description'])
        self.assertTrue(org.is_active)
        self.assertIsNotNone(org.created_at)
        self.assertIsNotNone(org.updated_at)

    def test_unique_name_constraint(self):
        """Test that organization names must be unique."""
        org1 = Organization.objects.create(**self.org_data)
        org2 = Organization(**self.org_data)
        with self.assertRaises(IntegrityError):
            org2.save(validate_unique=False)

    def test_name_max_length(self):
        """Test that organization name cannot exceed max length."""
        self.org_data['name'] = 'A' * 201  # Exceeds max_length of 200
        org = Organization(**self.org_data)
        with self.assertRaises(ValidationError):
            org.full_clean()

    def test_description_optional(self):
        """Test that description is optional."""
        self.org_data['description'] = None
        org = Organization.objects.create(**self.org_data)
        self.assertIsNone(org.description)

    def test_migrations_in_sync(self):
        """Test that all model changes have corresponding migrations"""
        from django.core.management import call_command
        from io import StringIO
        
        # Capture output from makemigrations --check
        out = StringIO()
        try:
            call_command('makemigrations', '--check', stdout=out)
        except SystemExit:
            self.fail(
                "Migrations are not in sync with models. "
                "Run 'python manage.py makemigrations' to generate missing migrations."
            )
        
        # Verify no migration files are missing
        output = out.getvalue()
        self.assertNotIn(
            "Your models have changes that are not yet reflected in a migration",
            output,
            "Models have changes that need new migrations"
        )

    def test_migrations_applied(self):
        """Test that all migrations have been applied to the database"""
        from django.core.management import call_command
        from io import StringIO
        
        # Capture output from migrate --check
        out = StringIO()
        try:
            call_command('migrate', '--check', stdout=out)
        except SystemExit:
            self.fail(
                "Not all migrations have been applied. "
                "Run 'python manage.py migrate' to apply pending migrations."
            )
        
        # Verify no migrations are pending
        output = out.getvalue()
        self.assertNotIn(
            "Your models have unapplied migrations",
            output,
            "There are unapplied migrations"
        )

class TestDepartmentModelConstraints(TestCase):
    """Test suite for Department model constraints and validations."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Organization',
            description='Test Description',
            created_by=self.user
        )
        self.dept_data = {
            'name': 'Test Department',
            'description': 'Test Description',
            'organization': self.org,
            'is_active': True,
            'created_by': self.user
        }

    def test_department_creation(self):
        """Test that a department can be created with valid data."""
        dept = Department.objects.create(**self.dept_data)
        self.assertEqual(dept.name, self.dept_data['name'])
        self.assertEqual(dept.organization, self.org)
        self.assertTrue(dept.is_active)
        self.assertIsNotNone(dept.created_at)
        self.assertIsNotNone(dept.updated_at)

    def test_organization_required(self):
        """Test that organization is required for department."""
        self.dept_data['organization'] = None
        with self.assertRaises(IntegrityError):
            Department.objects.create(**self.dept_data)

    def test_cascade_deletion(self):
        """Test that departments are deleted when organization is deleted."""
        dept = Department.objects.create(**self.dept_data)
        self.org.delete(hard_delete=True)
        with self.assertRaises(Department.DoesNotExist):
            Department.objects.get(pk=dept.pk)

    def test_parent_department_optional(self):
        """Test that parent department is optional."""
        dept1 = Department.objects.create(**self.dept_data)
        self.dept_data['name'] = 'Sub Department'
        dept2 = Department.objects.create(parent=dept1, **self.dept_data)
        self.assertEqual(dept2.parent, dept1)

class TestTeamModelConstraints(TestCase):
    """Test suite for Team model constraints and validations."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Organization',
            description='Test Description',
            created_by=self.user
        )
        self.dept = Department.objects.create(
            name='Test Department',
            description='Test Description',
            organization=self.org,
            created_by=self.user
        )
        self.team_data = {
            'name': 'Test Team',
            'description': 'Test Description',
            'department': self.dept,
            'is_active': True,
            'created_by': self.user
        }

    def test_team_creation(self):
        """Test that a team can be created with valid data."""
        team = Team.objects.create(**self.team_data)
        self.assertEqual(team.name, self.team_data['name'])
        self.assertEqual(team.department, self.dept)
        self.assertTrue(team.is_active)
        self.assertIsNotNone(team.created_at)
        self.assertIsNotNone(team.updated_at)

    def test_department_required(self):
        """Test that department is required for team."""
        self.team_data['department'] = None
        with self.assertRaises(IntegrityError):
            Team.objects.create(**self.team_data)

    def test_cascade_deletion_department(self):
        """Test that teams are deleted when department is deleted."""
        team = Team.objects.create(**self.team_data)
        self.dept.delete(hard_delete=True)
        with self.assertRaises(Team.DoesNotExist):
            Team.objects.get(pk=team.pk)

    def test_cascade_deletion_organization(self):
        """Test that teams are deleted when organization is deleted."""
        team = Team.objects.create(**self.team_data)
        self.org.delete(hard_delete=True)
        with self.assertRaises(Team.DoesNotExist):
            Team.objects.get(pk=team.pk)

    def test_parent_team_optional(self):
        """Test that parent team is optional."""
        team1 = Team.objects.create(**self.team_data)
        self.team_data['name'] = 'Sub Team'
        team2 = Team.objects.create(parent=team1, **self.team_data)
        self.assertEqual(team2.parent, team1)

class TestModelRelationships(TestCase):
    """Test suite for model relationships and hierarchy."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(
            name='Test Organization',
            description='Test Description',
            created_by=self.user
        )
        self.dept1 = Department.objects.create(
            name='Department 1',
            description='Test Description',
            organization=self.org,
            created_by=self.user
        )
        self.dept2 = Department.objects.create(
            name='Department 2',
            description='Test Description',
            organization=self.org,
            parent=self.dept1,
            created_by=self.user
        )
        self.team1 = Team.objects.create(
            name='Team 1',
            description='Test Description',
            department=self.dept2,
            created_by=self.user
        )
        self.team2 = Team.objects.create(
            name='Team 2',
            description='Test Description',
            department=self.dept2,
            parent=self.team1,
            created_by=self.user
        )

    def test_organization_departments(self):
        """Test organization-department relationship."""
        self.assertEqual(self.org.departments.count(), 2)
        self.assertIn(self.dept1, self.org.departments.all())
        self.assertIn(self.dept2, self.org.departments.all())

    def test_department_teams(self):
        """Test department-team relationship."""
        self.assertEqual(self.dept1.teams.count(), 0)
        self.assertEqual(self.dept2.teams.count(), 2)
        self.assertIn(self.team1, self.dept2.teams.all())
        self.assertIn(self.team2, self.dept2.teams.all())

    def test_department_hierarchy(self):
        """Test department parent-child relationship."""
        self.assertEqual(self.dept2.parent, self.dept1)
        self.assertIn(self.dept2, self.dept1.children.all())

    def test_team_hierarchy(self):
        """Test team parent-child relationship."""
        self.assertEqual(self.team2.parent, self.team1)
        self.assertIn(self.team2, self.team1.sub_teams.all())

class TestDatabaseSchema(TestCase):
    """Test suite to verify database schema matches model definitions"""
    
    def test_department_schema(self):
        """Test that Department model has all required database columns"""
        from django.db import connection
        
        # Get the database cursor
        with connection.cursor() as cursor:
            # Get table info for the department table
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='entity_department';
            """)
            table_schema = cursor.fetchone()[0]
            
            # Required fields that should exist in the schema
            required_fields = [
                'id', 'name', 'description', 'is_active',
                'created_at', 'updated_at', 'organization_id', 'parent_id'
            ]
            
            # Check each required field exists in the schema
            for field in required_fields:
                self.assertIn(
                    field,
                    table_schema.lower(),
                    f"Required field '{field}' is missing from Department table schema"
                )
    
    def test_department_parent_relationship(self):
        """Test that Department parent relationship works in database"""
        user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        org = Organization.objects.create(name="Test Org", created_by=user)
        parent_dept = Department.objects.create(
            name="Parent Department",
            organization=org,
            created_by=user
        )
        child_dept = Department.objects.create(
            name="Child Department",
            organization=org,
            parent=parent_dept,
            created_by=user
        )
        
        # Refresh from database to ensure relationship is saved
        child_dept.refresh_from_db()
        
        self.assertEqual(
            child_dept.parent.id,
            parent_dept.id,
            "Parent-child relationship not properly stored in database"
        ) 