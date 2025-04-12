import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from Apps.rbac.models import OrganizationContext
from Apps.entity.models import Organization, Department, Team, TeamMember
from django.contrib.auth import get_user_model
import os
import re

User = get_user_model()

@pytest.mark.django_db
class TestOrganizationDocumentation:
    """Tests for the Organization documentation"""
    
    def test_organization_documentation_exists(self):
        """Test that organization documentation exists"""
        # Check if the documentation file exists
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'organization_context.md')
        assert os.path.exists(docs_path), "Organization documentation file does not exist"
    
    def test_organization_documentation_content(self):
        """Test that organization documentation has the required content"""
        # Read the documentation file
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'organization_context.md')
        with open(docs_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        assert '# Organization Context' in content, "Documentation missing title"
        assert '## Overview' in content, "Documentation missing overview section"
        assert '## Model Structure' in content, "Documentation missing model structure section"
        assert '## Usage Examples' in content, "Documentation missing usage examples section"
        assert '## API Reference' in content, "Documentation missing API reference section"
        assert '## Best Practices' in content, "Documentation missing best practices section"
    
    def test_organization_documentation_model_structure(self):
        """Test that organization documentation includes model structure details"""
        # Read the documentation file
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'organization_context.md')
        with open(docs_path, 'r') as f:
            content = f.read()
        
        # Check for model fields
        assert 'name' in content, "Documentation missing name field"
        assert 'description' in content, "Documentation missing description field"
        assert 'parent' in content, "Documentation missing parent field"
        assert 'is_active' in content, "Documentation missing is_active field"
        assert 'metadata' in content, "Documentation missing metadata field"
    
    def test_organization_documentation_methods(self):
        """Test that organization documentation includes method details"""
        # Read the documentation file
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'organization_context.md')
        with open(docs_path, 'r') as f:
            content = f.read()
        
        # Check for method documentation
        assert 'get_ancestors' in content, "Documentation missing get_ancestors method"
        assert 'get_descendants' in content, "Documentation missing get_descendants method"
        assert 'get_all_children' in content, "Documentation missing get_all_children method"
        assert 'get_all_parents' in content, "Documentation missing get_all_parents method"
        assert 'deactivate' in content, "Documentation missing deactivate method"
        assert 'activate' in content, "Documentation missing activate method"
    
    def test_organization_documentation_api_reference(self):
        """Test that organization documentation includes API reference"""
        # Read the documentation file
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'organization_context.md')
        with open(docs_path, 'r') as f:
            content = f.read()
        
        # Check for API endpoints
        assert 'GET /api/organization-contexts/' in content, "Documentation missing GET endpoint"
        assert 'POST /api/organization-contexts/' in content, "Documentation missing POST endpoint"
        assert 'GET /api/organization-contexts/{id}/' in content, "Documentation missing GET by ID endpoint"
        assert 'PUT /api/organization-contexts/{id}/' in content, "Documentation missing PUT endpoint"
        assert 'DELETE /api/organization-contexts/{id}/' in content, "Documentation missing DELETE endpoint"
    
    def test_organization_documentation_code_examples(self):
        """Test that organization documentation includes code examples"""
        # Read the documentation file
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'organization_context.md')
        with open(docs_path, 'r') as f:
            content = f.read()
        
        # Check for code blocks
        code_blocks = re.findall(r'```(?:python|json|bash)?\n(.*?)```', content, re.DOTALL)
        assert len(code_blocks) >= 3, "Documentation should include at least 3 code examples"
    
    def test_organization_documentation_formatting(self):
        """Test that organization documentation has proper formatting"""
        # Read the documentation file
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'organization_context.md')
        with open(docs_path, 'r') as f:
            content = f.read()
        
        # Check for proper markdown formatting
        assert re.search(r'#+\s+', content), "Documentation should use proper heading levels"
        assert re.search(r'\*\*.*?\*\*', content), "Documentation should use bold text"
        assert re.search(r'`.*?`', content), "Documentation should use inline code"
        assert re.search(r'```.*?```', content, re.DOTALL), "Documentation should use code blocks" 