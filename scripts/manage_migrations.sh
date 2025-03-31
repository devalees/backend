#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to create backup
create_backup() {
    print_message "Creating database backup..." "$YELLOW"
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="backups/db_backup_${timestamp}.sql"
    
    # Create backups directory if it doesn't exist
    mkdir -p backups
    
    # Create backup (adjust the command based on your database type)
    python3 manage.py dumpdata --exclude auth.permission --exclude contenttypes > "${backup_file}"
    
    if [ $? -eq 0 ]; then
        print_message "Backup created successfully: ${backup_file}" "$GREEN"
    else
        print_message "Failed to create backup!" "$RED"
        exit 1
    fi
}

# Function to restore backup
restore_backup() {
    backup_file=$1
    if [ -f "$backup_file" ]; then
        print_message "Restoring backup from: ${backup_file}" "$YELLOW"
        python3 manage.py loaddata "${backup_file}"
        if [ $? -eq 0 ]; then
            print_message "Backup restored successfully" "$GREEN"
        else
            print_message "Failed to restore backup!" "$RED"
            exit 1
        fi
    else
        print_message "Backup file not found: ${backup_file}" "$RED"
        exit 1
    fi
}

# Function to check for migration conflicts
check_migration_conflicts() {
    print_message "Checking for migration conflicts..." "$YELLOW"
    python3 manage.py makemigrations --dry-run
    
    if [ $? -ne 0 ]; then
        print_message "Migration conflicts detected!" "$RED"
        exit 1
    fi
}

# Function to apply migrations
apply_migrations() {
    print_message "Applying migrations..." "$YELLOW"
    python3 manage.py migrate
    
    if [ $? -eq 0 ]; then
        print_message "Migrations applied successfully" "$GREEN"
    else
        print_message "Failed to apply migrations!" "$RED"
        exit 1
    fi
}

# Function to show migration status
show_migration_status() {
    print_message "Current migration status:" "$YELLOW"
    python3 manage.py showmigrations
}

# Main script logic
case "$1" in
    "apply")
        create_backup
        check_migration_conflicts
        apply_migrations
        ;;
    "rollback")
        if [ -z "$2" ]; then
            print_message "Please specify backup file to restore" "$RED"
            exit 1
        fi
        restore_backup "$2"
        ;;
    "status")
        show_migration_status
        ;;
    "check")
        check_migration_conflicts
        ;;
    *)
        print_message "Usage:" "$YELLOW"
        print_message "  ./manage_migrations.sh apply    - Apply migrations with backup" "$NC"
        print_message "  ./manage_migrations.sh rollback <backup_file> - Restore from backup" "$NC"
        print_message "  ./manage_migrations.sh status   - Show migration status" "$NC"
        print_message "  ./manage_migrations.sh check    - Check for migration conflicts" "$NC"
        exit 1
        ;;
esac 