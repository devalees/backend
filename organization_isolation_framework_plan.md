# Entity App Upgrade Plan: Organization Isolation Framework

## 1. Executive Summary

This plan outlines the steps to upgrade the Entity app to implement a robust organization isolation framework for the API-based system. The upgrade will enable automatic organization context management, eliminating the need for users to manually select organizations for each operation while maintaining strict data isolation between organizations.

## 2. Current Architecture Analysis

### 2.1 Current Entity App Structure

- **Organization model**: Core entity representing a company/business unit
- **Department model**: Division within an organization
- **Team model**: Group within a department
- **TeamMember model**: Links users to teams

### 2.2 Current Limitations

- Users must explicitly select an organization for each record
- Organization validation happens after data submission
- No persistent organization context between API requests
- Inconsistent organization handling across different endpoints

## 3. Upgrade Implementation Plan

### Phase 1: API Authentication Enhancement (Week 1-2)

#### 1.1 JWT Token Extensions
- Extend JWT payload to include `active_organization_id` field
- Add `organizations` array with IDs and roles to user info endpoint
- Create API endpoint for switching active organization

```
POST /api/auth/set-organization/
{
  "organization_id": 123
}
```

#### 1.2 Entity App Middleware
- Create `organization_context.py` in Entity app
- Implement organization extraction and validation from JWT/headers
- Develop thread-local storage for organization context

#### 1.3 User-Organization Access Manager
- Add `UserOrganizationAccess` model to track organization access rights
- Create manager methods for organization membership validation
- Implement caching for frequent organization access checks

### Phase 2: Model & Manager Updates (Week 3-4)

#### 2.1 Organization-Aware Model Managers
- Extend `OrganizationIsolationManager` in Entity app
- Create automatic filtering based on active organization
- Add bypass mechanisms for admin/system operations

#### 2.2 Database Constraints
- Review all organization foreign keys for consistency
- Add database-level constraints to enforce organization isolation
- Create migration to verify all existing data is properly associated

#### 2.3 Query Optimization
- Add indexes for organization-related queries
- Implement eager loading patterns for organization hierarchies
- Create caching strategy for frequently-accessed organization data

### Phase 3: API Layer Enhancements (Week 5-6)

#### 3.1 Serializer Mixins
- Create `OrganizationContextSerializerMixin` for Entity serializers
- Auto-assign organization based on context for create operations
- Add validation to prevent changing organization on updates
- Hide organization field from regular API users

#### 3.2 ViewSet Enhancements
- Implement `OrganizationContextViewSetMixin` for Entity viewsets
- Auto-filter querysets by active organization
- Add permissions for cross-organization operations
- Create mechanisms for explicit organization override

#### 3.3 Error Handling & Validation
- Standardize organization access error responses
- Add clear error messages for organization validation failures
- Implement consistent logging for organization access events

### Phase 4: User Experience & Client Development (Week 7-8)

#### 4.1 Organization Management Endpoints
- Enhance organization listing with additional metadata
- Add endpoints for organization user management
- Create endpoints for organization hierarchy navigation

#### 4.2 Client SDK Updates
- Document organization context handling for client applications
- Create helper methods for organization switching
- Add organization context awareness to SDK examples

#### 4.3 API Documentation
- Update OpenAPI documentation with organization context details
- Add examples for multi-organization scenarios
- Document security implications and best practices

## 4. Technical Specifications

### 4.1 Entity App Model Changes

```python
# New models to add

class OrganizationContext(models.Model):
    """Tracks and validates user-organization access"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    roles = models.JSONField(default=list)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'organization']
```

### 4.2 Organization Authentication Middleware

The middleware will:
1. Extract organization ID from JWT token or request header
2. Validate user has access to the requested organization
3. Set organization context in thread-local storage
4. Handle fallback to default/primary organization

### 4.3 API Response Format Updates

Organization-related error responses:
```json
{
  "error": "organization_access_denied",
  "message": "You do not have access to the requested organization",
  "available_organizations": [
    {"id": 1, "name": "Org A"},
    {"id": 2, "name": "Org B"}
  ]
}
```

### 4.4 Database Migration Strategy

The following migrations will be needed:
1. Add indexes to organization foreign keys
2. Create the new OrganizationContext model
3. Populate OrganizationContext from existing TeamMember data
4. Validate organization consistency across all models

## 5. Testing Strategy

### 5.1 Unit Tests
- Test organization context extraction from tokens/headers
- Validate organization access permission checks
- Test automatic organization assignment in serializers

### 5.2 Integration Tests
- End-to-end API tests with organization context
- Verify organization isolation across all endpoints
- Test organization switching and access control

### 5.3 Performance Testing
- Benchmark organization context overhead
- Test caching effectiveness for organization access checks
- Load test with multiple organizations and users

## 6. Rollout Plan

### 6.1 Development Phase
- Implement changes in a feature branch
- Review code with security team focus
- Document all breaking changes

### 6.2 Staging Deployment
- Deploy to staging environment
- Run automated test suite
- Perform manual testing of critical flows

### 6.3 Production Deployment
- Create backward compatibility layer
- Deploy in phases (authentication first, then filtering)
- Monitor closely for organization isolation issues

### 6.4 Post-Deployment
- Audit organization access patterns
- Address any performance issues
- Document lessons learned

## 7. Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes to API | High | Version new endpoints, maintain compat layer |
| Performance degradation | Medium | Implement caching, optimize queries |
| Data inconsistency | High | Run validation scripts before/after migration |
| Security vulnerabilities | Critical | Security review, penetration testing |

## 8. Success Criteria

- Users no longer need to select organization explicitly
- All API requests automatically scoped to active organization
- Zero data leakage between organizations
- No significant performance impact (<10ms added latency)
- Improved developer experience with clear organization context

This upgrade will transform the Entity app from manual organization selection to an automatic, context-aware system that maintains strict isolation while improving the user and developer experience. 