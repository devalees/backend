#!/bin/bash

# Deployment script for Django project on EC2

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    supervisor \
    git \
    build-essential \
    libpq-dev \
    python3-venv

# Create project directory
sudo mkdir -p /var/www/project
sudo chown ubuntu:ubuntu /var/www/project

# Set up Python virtual environment
cd /var/www/project
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn

# Configure PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE project_db;"
sudo -u postgres psql -c "CREATE USER project_user WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "ALTER ROLE project_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE project_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE project_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE project_db TO project_user;"

# Configure Nginx
sudo tee /etc/nginx/sites-available/project << EOF
server {
    listen 80;
    server_name your_domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /var/www/project;
    }

    location /media/ {
        root /var/www/project;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/project /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Configure Gunicorn
sudo tee /etc/supervisor/conf.d/project.conf << EOF
[program:project]
directory=/var/www/project
command=/var/www/project/venv/bin/gunicorn Core.wsgi:application --workers 3 --bind unix:/run/gunicorn.sock
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/project.err.log
stdout_logfile=/var/log/project.out.log
EOF

sudo supervisorctl reread
sudo supervisorctl update

# Set up environment variables
sudo tee /var/www/project/.env << EOF
DEBUG=False
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgres://project_user:your_secure_password@localhost:5432/project_db
ALLOWED_HOSTS=your_domain.com,localhost,127.0.0.1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
REDIS_URL=redis://localhost:6379/0
EOF

# Set proper permissions
sudo chown -R ubuntu:ubuntu /var/www/project
sudo chmod -R 755 /var/www/project

# Collect static files
cd /var/www/project
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

echo "Deployment completed successfully!" 