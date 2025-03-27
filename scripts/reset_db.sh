#!/bin/bash

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if last command was successful
check_status() {
    if [ $? -eq 0 ]; then
        print_message "$GREEN" "✓ Success: $1"
    else
        print_message "$RED" "✗ Error: $1"
        exit 1
    fi
}

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    check_status "Virtual environment activated"
else
    print_message "$YELLOW" "Warning: Virtual environment not found"
fi

# Find and remove all SQLite database files
print_message "$YELLOW" "Removing existing database files..."
find . -name "db.sqlite3" -delete
check_status "Removed existing database files"

# Remove all existing migrations except __init__.py
print_message "$YELLOW" "Removing existing migrations..."
find ./Apps -path "*/migrations/*.py" -not -name "__init__.py" -delete
find ./Apps -path "*/migrations/*.pyc" -delete
check_status "Removed existing migrations"

# Make migrations for all apps
print_message "$YELLOW" "Creating new migrations..."
python manage.py makemigrations contact
python manage.py makemigrations organizations
python manage.py makemigrations users
check_status "Created new migrations"

# Apply migrations
print_message "$YELLOW" "Applying migrations..."
python manage.py migrate
check_status "Applied migrations"

# Create superuser
print_message "$YELLOW" "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
"
check_status "Created superuser (username: admin, password: admin)"

print_message "$GREEN" "
Database reset complete!
--------------------
Superuser credentials:
Username: admin
Password: admin
Email: admin@example.com
"

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    check_status "Virtual environment deactivated"
fi 