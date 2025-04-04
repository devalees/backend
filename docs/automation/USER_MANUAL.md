# Automation System User Manual

Welcome to the Automation System! This guide will help you understand how to use all the available features through our API endpoints.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Workflows](#workflows)
3. [Reports](#reports)
4. [Templates](#templates)

## Getting Started

Before using any endpoint, make sure you're authenticated. All requests require authentication.

Base URL: `/api/v1/automation/`

## Workflows

### Managing Workflows

1. **List All Workflows**
   - Endpoint: `GET /workflows/`
   - What it does: Shows you all your workflows
   - Example response:
     ```json
     {
       "results": [
         {
           "id": 1,
           "name": "My Workflow",
           "description": "Daily report workflow"
         }
       ]
     }
     ```

2. **Create a New Workflow**
   - Endpoint: `POST /workflows/`
   - What it does: Creates a new workflow
   - What to send:
     ```json
     {
       "name": "My New Workflow",
       "description": "Description of what this workflow does"
     }
     ```

3. **Validate a Workflow**
   - Endpoint: `POST /workflows/{id}/validate/`
   - What it does: Checks if your workflow is set up correctly
   - Example response:
     ```json
     {
       "is_valid": true,
       "errors": []
     }
     ```

### Managing Nodes

1. **Add a Node**
   - Endpoint: `POST /nodes/`
   - What it does: Adds a new node to your workflow
   - What to send:
     ```json
     {
       "name": "Start Node",
       "workflow": 1,
       "node_type": "trigger",
       "configuration": {
         "trigger_type": "time",
         "schedule": "daily"
       },
       "position_x": 100,
       "position_y": 200
     }
     ```

2. **Update Node Position**
   - Endpoint: `PATCH /nodes/{id}/position/`
   - What it does: Moves a node to a new position
   - What to send:
     ```json
     {
       "position_x": 150,
       "position_y": 250
     }
     ```

### Managing Connections

1. **Create a Connection**
   - Endpoint: `POST /connections/`
   - What it does: Connects two nodes in your workflow
   - What to send:
     ```json
     {
       "workflow": 1,
       "source_node": 1,
       "target_node": 2,
       "configuration": {
         "condition": "always"
       }
     }
     ```

## Reports

### Managing Report Templates

1. **List Report Templates**
   - Endpoint: `GET /report-templates/`
   - What it does: Shows all your report templates

2. **Create Report Template**
   - Endpoint: `POST /report-templates/`
   - What it does: Creates a new report template
   - What to send:
     ```json
     {
       "name": "Monthly Sales Report",
       "description": "Template for monthly sales analysis",
       "query": {
         "model": "Sales",
         "filters": {"status": "completed"},
         "aggregations": [
           {"type": "sum", "field": "amount"}
         ]
       },
       "format": "pdf"
     }
     ```

3. **Generate Report**
   - Endpoint: `POST /report-templates/{id}/generate-report/`
   - What it does: Creates a new report from a template
   - What to send:
     ```json
     {
       "name": "March 2025 Sales Report",
       "description": "Sales analysis for March 2025"
     }
     ```

4. **View Template Analytics**
   - Endpoint: `GET /report-templates/{id}/analytics/`
   - What it does: Shows usage statistics for the template

### Managing Reports

1. **List Reports**
   - Endpoint: `GET /reports/`
   - What it does: Shows all your generated reports

2. **Retry Failed Report**
   - Endpoint: `POST /reports/{id}/retry/`
   - What it does: Tries to generate a failed report again

### Managing Report Schedules

1. **List Schedules**
   - Endpoint: `GET /report-schedules/`
   - What it does: Shows all your report schedules

2. **Create Schedule**
   - Endpoint: `POST /report-schedules/`
   - What it does: Sets up automatic report generation
   - What to send:
     ```json
     {
       "name": "Daily Sales Report",
       "template": 1,
       "schedule": {
         "frequency": "daily",
         "time": "09:00",
         "timezone": "UTC"
       },
       "parameters": {
         "start_date": "2025-04-04",
         "end_date": "2025-04-11"
       }
     }
     ```

3. **Toggle Schedule**
   - Endpoint: `POST /report-schedules/{id}/toggle-active/`
   - What it does: Turns a schedule on or off

## Templates

### Managing Workflow Templates

1. **List Templates**
   - Endpoint: `GET /workflow-templates/`
   - What it does: Shows all available workflow templates

2. **Create Template**
   - Endpoint: `POST /workflow-templates/`
   - What it does: Creates a new workflow template
   - What to send:
     ```json
     {
       "name": "Email Notification Flow",
       "description": "Template for email notification workflow",
       "configuration": {
         "nodes": [
           {
             "type": "trigger",
             "name": "Start",
             "config": {
               "trigger_type": "time",
               "schedule": "daily"
             }
           },
           {
             "type": "action",
             "name": "Send Email",
             "config": {
               "action_type": "email"
             }
           }
         ],
         "connections": [
           {
             "from": "Start",
             "to": "Send Email"
           }
         ]
       }
     }
     ```

3. **Create Workflow from Template**
   - Endpoint: `POST /workflow-templates/{id}/instantiate/`
   - What it does: Creates a new workflow based on a template
   - What to send:
     ```json
     {
       "name": "My Email Workflow",
       "description": "Daily email notification workflow"
     }
     ```

## Tips and Best Practices

1. **Always Validate Workflows**
   - Use the validate endpoint before running a workflow
   - Fix any errors reported in the validation response

2. **Report Generation**
   - Reports are generated asynchronously
   - Check the report status to know when it's ready
   - Use retry for failed reports

3. **Scheduling Reports**
   - Set schedules in UTC time
   - Use toggle-active to pause/resume schedules
   - Monitor schedule analytics for performance

4. **Template Usage**
   - Start with templates for common workflows
   - Customize templates to your needs
   - Share successful workflow patterns as templates

## Error Handling

Common error responses and what they mean:

- `400 Bad Request`: Check your input data
- `401 Unauthorized`: You need to log in
- `403 Forbidden`: You don't have permission
- `404 Not Found`: The resource doesn't exist
- `500 Server Error`: Contact support

## Need Help?

If you encounter any issues or need assistance:
1. Check the validation response for specific errors
2. Review the error message in the response
3. Contact support with the specific endpoint and error details 