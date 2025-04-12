# Audit System

## Overview

The Audit system in the RBAC module provides comprehensive tracking and logging of all significant actions related to roles, permissions, and access control within the system. It enables organizations to maintain a detailed record of who performed what action on which resource, when it happened, and the outcome of the action.

The audit system is designed to support compliance requirements, security monitoring, and troubleshooting by providing a complete audit trail of all system activities.

## Model

The `Audit` model is the core component of the audit system. It inherits from `RBACBaseModel` and includes the following fields:

| Field | Type | Description |
|-------|------|-------------|
| user | ForeignKey | The user who performed the action (nullable) |
| action | CharField | The type of action performed (e.g., 'create', 'update', 'delete') |
| resource_type | CharField | The type of resource affected (e.g., 'role', 'permission', 'user_role') |
| resource_id | IntegerField | The ID of the affected resource |
| details | JSONField | Additional details about the action (stored as JSON) |
| status | CharField | The outcome of the action (default: 'success') |
| timestamp | DateTimeField | When the action occurred (default: current time) |
| ip_address | GenericIPAddressField | IP address of the user (nullable) |
| user_agent | TextField | User agent string from the request (optional) |
| session_id | CharField | Session identifier (optional) |
| retention_period | IntegerField | Number of days to retain this audit log (default: 365) |
| organization | ForeignKey | The organization this audit log belongs to |

### Key Methods

The Audit model provides several class methods for common operations:

- `log_action()`: Creates a new audit log entry
- `get_audit_logs()`: Retrieves audit logs with filtering options
- `cleanup_expired_audits()`: Removes audit logs that have exceeded their retention period
- `generate_compliance_report()`: Generates compliance reports based on audit data

## API Endpoints

The Audit system exposes the following API endpoints:

### GET /api/rbac/audit/

Lists all audit logs for the current organization with optional filtering.

**Query Parameters:**
- `resource_type`: Filter by resource type
- `action`: Filter by action type
- `user`: Filter by user ID
- `status`: Filter by status
- `start_date`: Filter by start date (ISO format)
- `end_date`: Filter by end date (ISO format)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "type": "audit",
      "attributes": {
        "action": "role_created",
        "resource_type": "role",
        "resource_id": 123,
        "details": {"role_name": "Admin Role"},
        "status": "success",
        "timestamp": "2023-04-12T14:30:00Z",
        "retention_period": 365
      }
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "pages": 5,
      "count": 42
    }
  }
}
```

### GET /api/rbac/audit/{id}/

Retrieves a specific audit log entry.

**Response:**
```json
{
  "data": {
    "id": 1,
    "type": "audit",
    "attributes": {
      "action": "role_created",
      "resource_type": "role",
      "resource_id": 123,
      "details": {"role_name": "Admin Role"},
      "status": "success",
      "timestamp": "2023-04-12T14:30:00Z",
      "retention_period": 365
    }
  }
}
```

### GET /api/rbac/audit/compliance_report/

Generates a compliance report based on audit data.

**Query Parameters:**
- `report_type`: Type of report to generate (default: 'comprehensive')
  - Options: 'comprehensive', 'role_changes', 'permission_changes', 'user_role_assignments', 'resource_access'
- `start_date`: Start date for the report period (ISO format)
- `end_date`: End date for the report period (ISO format)

**Response:**
```json
{
  "data": {
    "type": "compliance_report",
    "attributes": {
      "report_type": "comprehensive",
      "start_date": "2023-01-01T00:00:00Z",
      "end_date": "2023-04-12T23:59:59Z",
      "generated_at": "2023-04-12T15:00:00Z",
      "summary": {
        "total_actions": 150,
        "successful_actions": 145,
        "failed_actions": 5
      },
      "details": {
        "role_changes": [...],
        "permission_changes": [...],
        "user_role_assignments": [...],
        "resource_access": [...]
      }
    }
  }
}
```

### POST /api/rbac/audit/cleanup_expired/

Removes audit logs that have exceeded their retention period.

**Response:**
```json
{
  "data": {
    "type": "cleanup_result",
    "attributes": {
      "deleted_count": 42,
      "timestamp": "2023-04-12T15:30:00Z"
    }
  }
}
```

## Usage Examples

### Logging an Action

```python
from Apps.rbac.models import Audit

# Log a role creation
Audit.log_action(
    organization=request.user.organization,
    user=request.user,
    action='role_created',
    resource_type='role',
    resource_id=role.id,
    details={'role_name': role.name},
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT'),
    session_id=request.session.session_key
)

# Log a permission update
Audit.log_action(
    organization=request.user.organization,
    user=request.user,
    action='permission_updated',
    resource_type='permission',
    resource_id=permission.id,
    details={
        'permission_name': permission.name,
        'changes': {'description': 'Updated description'}
    }
)
```

### Retrieving Audit Logs

```python
from Apps.rbac.models import Audit
from datetime import datetime, timedelta

# Get all audit logs for the last 30 days
start_date = datetime.now() - timedelta(days=30)
audit_logs = Audit.get_audit_logs(
    organization=request.user.organization,
    start_date=start_date
)

# Get audit logs for a specific resource
resource_logs = Audit.get_audit_logs(
    organization=request.user.organization,
    resource_type='role',
    resource_id=role_id
)

# Get audit logs for a specific user
user_logs = Audit.get_audit_logs(
    organization=request.user.organization,
    user=user_id
)
```

### Generating Compliance Reports

```python
from Apps.rbac.models import Audit
from datetime import datetime, timedelta

# Generate a comprehensive report for the last quarter
start_date = datetime.now() - timedelta(days=90)
report = Audit.generate_compliance_report(
    organization=request.user.organization,
    report_type='comprehensive',
    start_date=start_date
)

# Generate a role changes report
role_report = Audit.generate_compliance_report(
    organization=request.user.organization,
    report_type='role_changes'
)
```

### Cleaning Up Expired Audit Logs

```python
from Apps.rbac.models import Audit

# Clean up expired audit logs
deleted_count = Audit.cleanup_expired_audits(
    organization=request.user.organization
)
```

## Compliance Reporting

The Audit system provides comprehensive compliance reporting capabilities to help organizations meet regulatory requirements and internal policies.

### Report Types

1. **Comprehensive Report**: Includes all audit data across all categories
2. **Role Changes Report**: Focuses on changes to roles and role assignments
3. **Permission Changes Report**: Tracks changes to permissions and permission assignments
4. **User Role Assignments Report**: Monitors user role assignments and changes
5. **Resource Access Report**: Tracks resource access grants and revocations

### Report Content

Each report includes:

- Summary statistics (total actions, successful/failed actions)
- Detailed logs of all relevant actions
- User information for each action
- Timestamps for all actions
- Outcome of each action

## Retention Policy

The Audit system implements a configurable retention policy to manage the lifecycle of audit logs.

### Default Retention

By default, audit logs are retained for 365 days (1 year). This can be customized per audit log entry.

### Custom Retention

Organizations can set custom retention periods for specific types of audit logs:

```python
# Create an audit log with a custom retention period (2 years)
Audit.log_action(
    organization=request.user.organization,
    user=request.user,
    action='sensitive_action',
    resource_type='sensitive_resource',
    resource_id=resource_id,
    retention_period=730  # 2 years in days
)
```

### Automatic Cleanup

The system provides an automatic cleanup mechanism to remove expired audit logs:

```python
# Clean up expired audit logs
Audit.cleanup_expired_audits(organization=request.user.organization)
```

This can be scheduled to run periodically using a task scheduler like Celery or cron. 