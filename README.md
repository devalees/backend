## Migration Management

### Automated Migration Tools

The project includes automated tools to handle database migrations safely:

1. **Migration Management Script** (`scripts/manage_migrations.sh`):
   ```bash
   # Apply migrations with backup
   ./scripts/manage_migrations.sh apply
   
   # Rollback to a specific backup
   ./scripts/manage_migrations.sh rollback backups/db_backup_YYYYMMDD_HHMMSS.sql
   
   # Check migration status
   ./scripts/manage_migrations.sh status
   
   # Check for migration conflicts
   ./scripts/manage_migrations.sh check
   ```

2. **Pre-commit Hook**:
   - Automatically checks for migration conflicts before committing
   - Warns about unapplied migrations
   - Prevents commits with migration conflicts

### Best Practices for Database Changes

1. **Development Workflow**:
   - Always create migrations in a feature branch
   - Test migrations in a development environment first
   - Use the migration management script for applying changes
   - Keep migrations atomic and focused

2. **Production Deployment**:
   - Always backup the database before applying migrations
   - Apply migrations during low-traffic periods
   - Have a rollback plan ready
   - Monitor the application after migration

3. **Common Issues and Solutions**:
   - **Migration Conflicts**: Use `./scripts/manage_migrations.sh check` to detect conflicts
   - **Failed Migrations**: Use the rollback feature to restore from backup
   - **Data Loss Prevention**: The script automatically creates backups before applying changes

4. **Testing Migrations**:
   - Run migrations on a test database first
   - Verify data integrity after migration
   - Test application functionality with the new schema

### Migration Commands Reference

```bash
# Create new migrations
python3 manage.py makemigrations

# Apply migrations
python3 manage.py migrate

# Show migration status
python3 manage.py showmigrations

# Create a data migration
python3 manage.py makemigrations --empty app_name

# Fake a migration (mark as applied without running)
python3 manage.py migrate --fake
``` 