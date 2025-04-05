# Deployment Guide for Django Project on EC2 (Testing Version)

## Prerequisites

1. AWS Account with appropriate permissions
2. SSH key pair for EC2 access

## Step 1: Launch EC2 Instance

1. Go to AWS Console > EC2 > Launch Instance
2. Choose Ubuntu 22.04 LTS AMI
3. Select instance type: t2.micro (for testing)
4. Configure instance details:
   - VPC: Default
   - Auto-assign Public IP: Enable
5. Add storage (minimum 8GB)
6. Configure security group:
   - SSH (port 22)
   - HTTP (port 80)
   - Custom TCP (port 8000 for development)
7. Review and launch
8. Select your SSH key pair

## Step 2: Deploy Application

1. SSH into your EC2 instance:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-ip
   ```

2. Create project directory with proper permissions:
   ```bash
   sudo mkdir -p /var/www/backend
   sudo chown ubuntu:ubuntu /var/www/backend
   ```

3. Clone your repository:
   ```bash
   git clone https://github.com/devalees/backend.git /var/www/backend
   ```

4. Make the deployment script executable:
   ```bash
   chmod +x /var/www/backend/scripts/deploy_test.sh
   ```

5. Run the deployment script:
   ```bash
   cd /var/www/backend
   ./scripts/deploy_test.sh
   ```

The deployment script will:
- Install all required system packages
- Set up Python virtual environment
- Install PostgreSQL locally
- Configure Redis locally
- Set up Nginx as reverse proxy
- Configure Gunicorn as application server
- Set up supervisor for process management
- Create necessary directories and set permissions
- Run database migrations
- Create a test admin user

## Step 3: Access the Application

After successful deployment, you can access:
- Admin panel: `http://your-ec2-public-ip/admin`
- API endpoints: `http://your-ec2-public-ip/api/`

Default admin credentials:
- Username: `admin`
- Password: `admin123`

## Step 4: Testing Configuration Details

The testing setup includes:

### Database Configuration
- PostgreSQL installed locally
- Database name: `project_db`
- Username: `project_user`
- Password: `test_password`

### Redis Configuration
- Redis installed locally
- Running on default port 6379
- Used for caching and session management

### File Storage
- Media files stored locally in `/var/www/backend/media`
- Static files collected in `/var/www/backend/static`

### Environment Variables
```
DEBUG=True
SECRET_KEY=test_secret_key_123
DATABASE_URL=postgres://project_user:test_password@localhost:5432/project_db
ALLOWED_HOSTS=localhost,127.0.0.1,ec2-public-ip
AWS_ACCESS_KEY_ID=test_key
AWS_SECRET_ACCESS_KEY=test_secret
AWS_STORAGE_BUCKET_NAME=test-bucket
REDIS_URL=redis://localhost:6379/0
```

## Troubleshooting

1. Check Nginx logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. Check application logs:
   ```bash
   sudo tail -f /var/log/project.err.log
   sudo tail -f /var/log/project.out.log
   ```

3. Check supervisor status:
   ```bash
   sudo supervisorctl status
   ```

4. Check PostgreSQL status:
   ```bash
   sudo systemctl status postgresql
   ```

5. Check Redis status:
   ```bash
   sudo systemctl status redis-server
   ```

## Important Notes

1. This setup is for testing purposes only and should not be used in production because:
   - Uses test credentials and keys
   - Has DEBUG mode enabled
   - Stores files locally
   - Uses less secure configurations
   - Limited resources (t2.micro instance)

2. For production deployment:
   - Use the production deployment script
   - Set up RDS for database
   - Configure S3 for media storage
   - Set up proper SSL certificates
   - Use secure credentials
   - Use appropriate instance type

## Maintenance

1. Regular updates:
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

2. Restart services if needed:
   ```bash
   sudo systemctl restart nginx
   sudo systemctl restart postgresql
   sudo systemctl restart redis-server
   sudo supervisorctl restart project
   ```

3. Backup database:
   ```bash
   pg_dump -U project_user project_db > backup.sql
   ```

4. Monitor disk space:
   ```bash
   df -h
   ```

5. Monitor memory usage:
   ```bash
   free -m
   ``` 