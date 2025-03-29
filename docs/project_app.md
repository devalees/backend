# Project App Documentation

## Overview
The project app is a comprehensive project management system that allows organizations to manage projects, tasks, and templates. It includes features for project and task creation, team management, and template-based project generation.

## Models

### 1. Project
- **Core Fields**:
  - `title`: Project name
  - `description`: Detailed project description
  - `start_date`: Project start date
  - `end_date`: Project end date
  - `status`: New, In Progress, On Hold, Completed
  - `priority`: Low, Medium, High
  - `owner`: Project owner (User)
  - `team_members`: Project team members (Many-to-Many with User)
  - `organization`: Associated organization

### 2. Task
- **Core Fields**:
  - `title`: Task name
  - `description`: Task description
  - `due_date`: Task deadline
  - `status`: Todo, In Progress, Done
  - `priority`: Low, Medium, High
  - `project`: Associated project
  - `assigned_to`: Task assignee
  - `parent_task`: Parent task (for subtasks)

### 3. ProjectTemplate
- **Core Fields**:
  - `title`: Template name
  - `description`: Template description
  - `estimated_duration`: Duration in days
  - `default_status`: Default project status
  - `default_priority`: Default project priority
  - `organization`: Associated organization

### 4. TaskTemplate
- **Core Fields**:
  - `title`: Template name
  - `description`: Template description
  - `estimated_duration`: Duration in days
  - `default_status`: Default task status
  - `default_priority`: Default task priority
  - `project_template`: Associated project template
  - `parent_task_template`: Parent template (for subtask templates)
  - `order`: Execution order

## API Endpoints

### 1. Projects API (`/api/v1/projects/`)

#### List/Create Projects
- `GET /api/v1/projects/`
  - Lists all projects accessible to the user
  - Supports search, filtering, and ordering
  - Filtered by user's organization membership

- `POST /api/v1/projects/`
  - Creates a new project
  - Required fields: title, start_date, end_date, organization_id, owner_id

#### Project Operations
- `GET /api/v1/projects/{id}/`
  - Retrieves project details

- `PUT/PATCH /api/v1/projects/{id}/`
  - Updates project details

- `DELETE /api/v1/projects/{id}/`
  - Deletes a project

#### Project Team Management
- `POST /api/v1/projects/{id}/add_team_members/`
  - Adds team members to the project
  - Payload: `{"user_ids": [1, 2, 3]}`

- `POST /api/v1/projects/{id}/remove_team_members/`
  - Removes team members from the project
  - Payload: `{"user_ids": [1, 2, 3]}`

### 2. Tasks API (`/api/v1/tasks/`)

#### List/Create Tasks
- `GET /api/v1/tasks/`
  - Lists all tasks accessible to the user
  - Supports search, filtering, and ordering
  - Filtered by user's project access

- `POST /api/v1/tasks/`
  - Creates a new task
  - Required fields: title, due_date, project

#### Task Operations
- `GET /api/v1/tasks/{id}/`
  - Retrieves task details

- `PUT/PATCH /api/v1/tasks/{id}/`
  - Updates task details

- `DELETE /api/v1/tasks/{id}/`
  - Deletes a task

#### Task Management
- `POST /api/v1/tasks/{id}/assign/`
  - Assigns task to a user
  - Payload: `{"user_id": 1}`

- `POST /api/v1/tasks/{id}/change_status/`
  - Updates task status
  - Payload: `{"status": "done"}`

### 3. Project Templates API (`/api/v1/project-templates/`)

#### List/Create Templates
- `GET /api/v1/project-templates/`
  - Lists all project templates accessible to the user
  - Filtered by organization membership

- `POST /api/v1/project-templates/`
  - Creates a new project template
  - Required fields: title, estimated_duration, organization

#### Template Operations
- `GET /api/v1/project-templates/{id}/`
  - Retrieves template details

- `PUT/PATCH /api/v1/project-templates/{id}/`
  - Updates template details

- `DELETE /api/v1/project-templates/{id}/`
  - Deletes a template

#### Create Project from Template
- `POST /api/v1/project-templates/{id}/create_project/`
  - Creates a new project from template
  - Payload:
    ```json
    {
        "start_date": "2024-03-29T00:00:00Z",
        "end_date": "2024-04-29T00:00:00Z",
        "owner_id": 1
    }
    ```

### 4. Task Templates API (`/api/v1/task-templates/`)

#### List/Create Task Templates
- `GET /api/v1/task-templates/`
  - Lists all task templates accessible to the user
  - Filtered by organization membership

- `POST /api/v1/task-templates/`
  - Creates a new task template
  - Required fields: title, estimated_duration, project_template

#### Task Template Operations
- `GET /api/v1/task-templates/{id}/`
  - Retrieves task template details

- `PUT/PATCH /api/v1/task-templates/{id}/`
  - Updates task template details

- `DELETE /api/v1/task-templates/{id}/`
  - Deletes a task template

## Permission System

### Organization-based Access
- Users can only access projects and templates within their organizations
- Organization membership is determined through team memberships

### Special Permissions
1. Project Permissions:
   - `view_all_projects`: Access to all projects
   - `manage_project_members`: Manage project team members

2. Task Permissions:
   - `view_all_tasks`: Access to all tasks
   - `manage_task_assignments`: Manage task assignments

3. Template Permissions:
   - `view_all_project_templates`: Access to all project templates
   - `manage_project_templates`: Manage project templates
   - `view_all_task_templates`: Access to all task templates
   - `manage_task_templates`: Manage task templates

## Business Logic

### Project Creation
1. From Scratch:
   - User provides project details
   - System validates dates and permissions
   - Project is created with initial team members

2. From Template:
   - User selects template and provides dates
   - System creates project with template settings
   - Tasks are created based on task templates
   - Task due dates are calculated based on estimated durations

### Task Management
1. Task Creation:
   - Tasks can be created independently or as subtasks
   - System validates due dates against project end date
   - Parent-child relationships are maintained

2. Task Assignment:
   - Tasks can be assigned to team members
   - Status changes are tracked
   - Task hierarchy is maintained

### Template System
1. Project Templates:
   - Define project structure and defaults
   - Include task templates
   - Organization-specific templates

2. Task Templates:
   - Define task structure and defaults
   - Support task hierarchy
   - Maintain execution order 