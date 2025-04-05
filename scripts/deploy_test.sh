#!/bin/bash

# Deployment script for Django project on EC2 (Testing Version)

# Get project name from user input
read -p "Enter your project name (e.g., backend): " PROJECT_NAME

# Get repository URL from user input
read -p "Enter your repository URL (e.g., https://github.com/username/repo.git): " REPO_URL

# Debug: Print current directory and environment
echo "Current directory: $(pwd)"
echo "Environment:"
env | grep -E 'PATH|HOME|USER'

# Clean up existing installations if directory exists
if [ -d "/var/www/$PROJECT_NAME" ]; then
    echo "Cleaning up existing installations..."
    # Remove project directory if it exists
    echo "Removing existing project directory: /var/www/$PROJECT_NAME"
    sudo rm -rf "/var/www/$PROJECT_NAME"
    
    # Remove all potential nginx configurations
    sudo rm -f "/etc/nginx/sites-enabled/$PROJECT_NAME"
    sudo rm -f "/etc/nginx/sites-available/$PROJECT_NAME"
    sudo rm -f /etc/nginx/sites-enabled/default

    # Remove all potential supervisor configurations
    sudo rm -f "/etc/supervisor/conf.d/$PROJECT_NAME.conf"
fi

# Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
echo "Installing required packages..."
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
echo "Creating project directory..."
sudo mkdir -p "/var/www/$PROJECT_NAME"
sudo chown ubuntu:ubuntu "/var/www/$PROJECT_NAME"

# Clone the repository
echo "Cloning repository..."
cd "/var/www/$PROJECT_NAME"
git clone "$REPO_URL" .

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    # Ensure djangorestframework-simplejwt is installed even if not in requirements.txt
    pip install djangorestframework-simplejwt
else
    echo "requirements.txt not found, installing basic dependencies"
    pip install django djangorestframework gunicorn psycopg2-binary redis djangorestframework-simplejwt django-cors-headers drf-yasg
fi

# Configure PostgreSQL
echo "Configuring PostgreSQL..."
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "${PROJECT_NAME}_db"; then
    sudo -u postgres psql -c "CREATE DATABASE ${PROJECT_NAME}_db;"
fi

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${PROJECT_NAME}_user'" | grep -q 1; then
    sudo -u postgres psql -c "CREATE USER ${PROJECT_NAME}_user WITH PASSWORD 'test_password';"
fi

sudo -u postgres psql -c "ALTER ROLE ${PROJECT_NAME}_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE ${PROJECT_NAME}_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE ${PROJECT_NAME}_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${PROJECT_NAME}_db TO ${PROJECT_NAME}_user;"

# Configure PostgreSQL to allow local connections
echo "Configuring PostgreSQL connections..."
POSTGRES_VERSION=$(ls /etc/postgresql)
if [ -d "/etc/postgresql/$POSTGRES_VERSION/main" ]; then
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/$POSTGRES_VERSION/main/postgresql.conf
    sudo sed -i "s/local   all             all                                     peer/local   all             all                                     md5/" /etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf
    sudo systemctl restart postgresql
else
    echo "Warning: PostgreSQL configuration directory not found. Please check PostgreSQL installation."
    echo "Available PostgreSQL versions:"
    ls /etc/postgresql
fi

# Configure Nginx
echo "Configuring Nginx..."
sudo tee "/etc/nginx/sites-available/$PROJECT_NAME" << EOF
server {
    listen 80;
    server_name localhost;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /var/www/$PROJECT_NAME;
    }

    location /media/ {
        root /var/www/$PROJECT_NAME;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
EOF

sudo rm -f "/etc/nginx/sites-enabled/$PROJECT_NAME"
sudo ln -s "/etc/nginx/sites-available/$PROJECT_NAME" "/etc/nginx/sites-enabled"
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Configure Gunicorn
echo "Configuring Gunicorn..."
sudo tee "/etc/supervisor/conf.d/$PROJECT_NAME.conf" << EOF
[program:$PROJECT_NAME]
directory=/var/www/$PROJECT_NAME
command=/var/www/$PROJECT_NAME/venv/bin/gunicorn Core.wsgi:application --workers 2 --bind unix:/run/gunicorn.sock
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/$PROJECT_NAME.err.log
stdout_logfile=/var/log/$PROJECT_NAME.out.log
EOF

sudo supervisorctl reread
sudo supervisorctl update

# Set up environment variables
echo "Setting up environment variables..."
sudo tee "/var/www/$PROJECT_NAME/.env" << EOF
DEBUG=True
SECRET_KEY=test_secret_key_123
DATABASE_URL=postgres://${PROJECT_NAME}_user:test_password@localhost:5432/${PROJECT_NAME}_db
ALLOWED_HOSTS=localhost,127.0.0.1,ec2-public-ip
AWS_ACCESS_KEY_ID=test_key
AWS_SECRET_ACCESS_KEY=test_secret
AWS_STORAGE_BUCKET_NAME=test-bucket
REDIS_URL=redis://localhost:6379/0
EOF

# Set proper permissions
echo "Setting permissions..."
sudo chown -R ubuntu:ubuntu "/var/www/$PROJECT_NAME"
sudo chmod -R 755 "/var/www/$PROJECT_NAME"

# Create media directory
echo "Creating media directory..."
sudo mkdir -p "/var/www/$PROJECT_NAME/media"
sudo chown -R ubuntu:ubuntu "/var/www/$PROJECT_NAME/media"

# Check if manage.py exists
echo "Checking for manage.py..."
if [ ! -f "/var/www/$PROJECT_NAME/manage.py" ]; then
    echo "Error: manage.py not found in /var/www/$PROJECT_NAME"
    echo "Current directory contents:"
    ls -la "/var/www/$PROJECT_NAME"
    echo "Please make sure the repository is cloned correctly"
    exit 1
fi

# Collect static files
echo "Collecting static files..."
cd "/var/www/$PROJECT_NAME"
python manage.py collectstatic --noinput

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser for testing
echo "Creating superuser..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell

echo "Testing deployment completed successfully!"
echo "You can access the admin panel at: http://your-ec2-public-ip/admin"
echo "Admin credentials:"
echo "Username: admin"
echo "Password: admin123" 