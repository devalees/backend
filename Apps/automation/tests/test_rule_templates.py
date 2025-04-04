from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from Apps.automation.models import RuleTemplate, Rule, Workflow, Trigger, Action
from Core.models.base import TaskStatus

User = get_user_model()

class RuleTemplateTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Create a test workflow
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            created_by=self.user
        )
        
        # Create test trigger and action
        self.trigger = Trigger.objects.create(
            name='Test Trigger',
            workflow=self.workflow,
            trigger_type='event',
            created_by=self.user
        )
        
        self.action = Action.objects.create(
            name='Test Action',
            workflow=self.workflow,
            action_type='notification',
            created_by=self.user
        )

        # Default valid conditions for tests
        self.valid_conditions = {
            'condition_type': 'test',
            'operator': 'equals',
            'value': 'test'
        }

    def test_create_rule_template(self):
        """Test creating a rule template with valid data."""
        template = RuleTemplate.objects.create(
            name='Test Template',
            description='Test Description',
            conditions=self.valid_conditions,
            created_by=self.user
        )
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.description, 'Test Description')
        self.assertEqual(template.conditions, self.valid_conditions)
        self.assertTrue(template.is_active)
        self.assertEqual(template.task_status, TaskStatus.PENDING.value)

    def test_rule_template_str(self):
        """Test the string representation of a rule template."""
        template = RuleTemplate.objects.create(
            name='Test Template',
            conditions=self.valid_conditions,
            created_by=self.user
        )
        self.assertEqual(str(template), 'Test Template')

    def test_rule_template_without_name(self):
        """Test that creating a rule template without a name raises ValidationError."""
        with self.assertRaises(ValidationError):
            template = RuleTemplate(
                conditions=self.valid_conditions,
                created_by=self.user
            )
            template.full_clean()

    def test_rule_template_without_user(self):
        """Test that creating a rule template without a user raises ValidationError."""
        with self.assertRaises(ValidationError):
            template = RuleTemplate(
                name='Test Template',
                conditions=self.valid_conditions
            )
            template.full_clean()

    def test_create_rule_from_template(self):
        """Test creating a new rule from a template."""
        template = RuleTemplate.objects.create(
            name='Test Template',
            description='Test Description',
            conditions=self.valid_conditions,
            created_by=self.user
        )
        
        rule = template.create_rule(
            workflow=self.workflow,
            trigger=self.trigger,
            action=self.action
        )
        
        self.assertEqual(rule.name, f"Rule from template: {template.name}")
        self.assertEqual(rule.conditions, template.conditions)
        self.assertEqual(rule.workflow, self.workflow)
        self.assertEqual(rule.trigger, self.trigger)
        self.assertEqual(rule.action, self.action)
        self.assertEqual(rule.created_by, template.created_by)

    def test_update_rules_from_template(self):
        """Test updating existing rules when template is updated."""
        template = RuleTemplate.objects.create(
            name='Test Template',
            conditions=self.valid_conditions,
            created_by=self.user
        )
        
        rule = template.create_rule(
            workflow=self.workflow,
            trigger=self.trigger,
            action=self.action
        )
        
        # Update template conditions
        updated_conditions = self.valid_conditions.copy()
        updated_conditions['value'] = 'updated'
        template.conditions = updated_conditions
        template.save()
        template.update_rules()
        
        # Refresh rule from database
        rule.refresh_from_db()
        self.assertEqual(rule.conditions, updated_conditions)

    def test_template_validation(self):
        """Test template validation for invalid conditions."""
        with self.assertRaises(ValidationError):
            template = RuleTemplate(
                name='Test Template',
                conditions='invalid',  # Should be a dict
                created_by=self.user
            )
            template.full_clean()

    def test_template_deactivation(self):
        """Test deactivating a template."""
        template = RuleTemplate.objects.create(
            name='Test Template',
            conditions=self.valid_conditions,
            created_by=self.user
        )
        
        template.is_active = False
        template.save()
        
        self.assertFalse(RuleTemplate.objects.get(id=template.id).is_active)
        
        # Test that we cannot create rules from inactive template
        with self.assertRaises(ValidationError):
            template.create_rule(
                workflow=self.workflow,
                trigger=self.trigger,
                action=self.action
            ) 