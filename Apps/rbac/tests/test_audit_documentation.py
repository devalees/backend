import pytest
import os
from pathlib import Path

@pytest.mark.django_db
class TestAuditDocumentation:
    """Test suite for Audit documentation"""
    
    def test_audit_documentation_file_exists(self):
        """Test that the audit documentation file exists"""
        docs_dir = Path("Apps/rbac/docs")
        audit_doc_file = docs_dir / "audit.md"
        
        assert audit_doc_file.exists(), "Audit documentation file does not exist"
    
    def test_audit_documentation_content(self):
        """Test that the audit documentation contains required sections"""
        docs_dir = Path("Apps/rbac/docs")
        audit_doc_file = docs_dir / "audit.md"
        
        with open(audit_doc_file, 'r') as f:
            content = f.read()
        
        # Check for required sections
        assert "# Audit System" in content, "Documentation missing title"
        assert "## Overview" in content, "Documentation missing overview section"
        assert "## Model" in content, "Documentation missing model section"
        assert "## API Endpoints" in content, "Documentation missing API endpoints section"
        assert "## Usage Examples" in content, "Documentation missing usage examples section"
        assert "## Compliance Reporting" in content, "Documentation missing compliance reporting section"
        assert "## Retention Policy" in content, "Documentation missing retention policy section"
    
    def test_audit_documentation_model_fields(self):
        """Test that the audit documentation includes all model fields"""
        docs_dir = Path("Apps/rbac/docs")
        audit_doc_file = docs_dir / "audit.md"
        
        with open(audit_doc_file, 'r') as f:
            content = f.read()
        
        # Check for required model fields
        required_fields = [
            "user", "action", "resource_type", "resource_id", "details", 
            "status", "timestamp", "ip_address", "user_agent", "session_id", 
            "retention_period", "organization"
        ]
        
        for field in required_fields:
            assert field in content, f"Documentation missing field: {field}"
    
    def test_audit_documentation_api_endpoints(self):
        """Test that the audit documentation includes all API endpoints"""
        docs_dir = Path("Apps/rbac/docs")
        audit_doc_file = docs_dir / "audit.md"
        
        with open(audit_doc_file, 'r') as f:
            content = f.read()
        
        # Check for required API endpoints
        required_endpoints = [
            "GET /api/rbac/audit/", "GET /api/rbac/audit/{id}/", 
            "GET /api/rbac/audit/compliance_report/", 
            "POST /api/rbac/audit/cleanup_expired/"
        ]
        
        for endpoint in required_endpoints:
            assert endpoint in content, f"Documentation missing endpoint: {endpoint}"
    
    def test_audit_documentation_examples(self):
        """Test that the audit documentation includes usage examples"""
        docs_dir = Path("Apps/rbac/docs")
        audit_doc_file = docs_dir / "audit.md"
        
        with open(audit_doc_file, 'r') as f:
            content = f.read()
        
        # Check for code examples
        assert "```python" in content, "Documentation missing code examples"
        assert "```json" in content, "Documentation missing JSON examples" 