# Time Management Business Logic

## Overview
The Time Management app handles time tracking, timesheets, and work schedules for users in the system. This document outlines the key business rules and logic implemented in the application.

## Core Components

### 1. Time Categories
- Categories represent different types of work (e.g., Development, Meeting, Break)
- Each category can be marked as billable or non-billable
- Categories are created by users and can be used across the system
- Categories cannot be deleted if they are in use (PROTECT constraint)

### 2. Time Entries
- Users must log their time against projects and categories
- Each time entry must have:
  - Start time and end time
  - Calculated hours (0-24 hours)
  - Project association
  - Category association
  - Description
- Business Rules:
  - End time must be after start time
  - Hours must be between 0 and 24
  - Each entry must be associated with a project
  - Each entry must have a category

### 3. Timesheets
- Users submit weekly or monthly timesheets
- Timesheet Status Flow:
  1. Draft (initial state)
  2. Submitted (user submits for approval)
  3. Approved (manager approves)
  4. Rejected (manager rejects)
- Business Rules:
  - End date must be after start date
  - Timesheets must be unique per user for the same date range
  - Total hours are calculated automatically
  - Entries cannot be added to submitted/approved/rejected timesheets
  - Only draft timesheets can be modified

### 4. Work Schedules
- Users can set their regular working hours
- Each schedule includes:
  - Start time and end time
  - Days of the week (0-6, where 0 is Monday)
  - Active status
- Business Rules:
  - End time must be after start time
  - Days must be valid (0-6)
  - Multiple schedules can exist per user
  - Active schedules determine user availability

## Data Validation Rules

### Time Entry Validation
```python
# Example validation rules
if end_time <= start_time:
    raise ValidationError("End time must be after start time")

if hours < 0 or hours > 24:
    raise ValidationError("Hours must be between 0 and 24")
```

### Timesheet Validation
```python
# Example validation rules
if end_date <= start_date:
    raise ValidationError("End date must be after start date")

if status not in ['draft', 'submitted', 'approved', 'rejected']:
    raise ValidationError("Invalid status")
```

### Work Schedule Validation
```python
# Example validation rules
if end_time <= start_time:
    raise ValidationError("End time must be after start time")

if not all(0 <= day <= 6 for day in days_of_week):
    raise ValidationError("Invalid day value")
```

## Status Transitions

### Timesheet Status Flow
1. Draft → Submitted
   - User submits timesheet for approval
   - Sets submitted_at timestamp
   - Locks entries from modification

2. Submitted → Approved
   - Manager approves timesheet
   - Sets approved_at timestamp
   - Sets approved_by user

3. Submitted → Rejected
   - Manager rejects timesheet
   - Sets status to rejected
   - Allows user to modify and resubmit

4. Rejected → Draft
   - User can modify rejected timesheet
   - Resets status to draft
   - Allows entry modifications

## Data Relationships

### User Relationships
- Users can have multiple time entries
- Users can have multiple timesheets
- Users can have multiple work schedules
- Users can be approvers for timesheets

### Project Relationships
- Projects can have multiple time entries
- Time entries must be associated with a project
- Projects belong to organizations

### Category Relationships
- Categories can be used in time entries
- Categories can be used in timesheet entries
- Categories are protected from deletion if in use

## Business Constraints

### Time Tracking
- Maximum 24 hours per day
- No overlapping time entries
- All time must be categorized
- All time must be associated with a project

### Timesheet Management
- One active timesheet per date range per user
- No modifications after submission
- Required approval workflow
- Automatic total hours calculation

### Work Schedule
- Multiple schedules per user allowed
- Active/inactive status management
- Day of week validation
- Time range validation

## Error Handling

### Validation Errors
- Time range validation
- Date range validation
- Status transition validation
- Required field validation

### Business Rule Violations
- Duplicate timesheet prevention
- Status transition restrictions
- Category deletion protection
- Entry modification restrictions

## Security Considerations

### Access Control
- Users can only view their own time entries
- Users can only modify their own timesheets
- Only managers can approve/reject timesheets
- Category management restricted to authorized users

### Data Protection
- Protected category deletion
- Read-only fields after submission
- Audit trail for status changes
- User tracking for all modifications 