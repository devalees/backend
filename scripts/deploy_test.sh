#!/bin/bash

# Exit on error
set -e

echo "Starting deployment process..."

# Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    redis-server \
    supervisor \
    git \
    build-essential \
    libpq-dev \
    python3-venv \
    curl \
    wget

# Create project directory
echo "Setting up project directory..."
if [ -d "/var/www/backend" ]; then
    echo "Project directory already exists. Using existing directory..."
else
    sudo mkdir -p /var/www/backend
    sudo chown ubuntu:ubuntu /var/www/backend
    # Clone repository only if directory doesn't exist
    echo "Cloning repository..."
    git clone https://github.com/devalees/backend.git /var/www/backend
fi

# Check for requirements.txt
if [ ! -f "/var/www/backend/requirements.txt" ]; then
    echo "Creating requirements.txt..."
    cat > /var/www/backend/requirements.txt << EOL
Django>=4.2.0
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.1
psycopg2-binary>=2.9.9
redis>=5.0.1
gunicorn>=21.2.0
django-cors-headers>=4.3.1
drf-yasg>=1.21.7
python-dotenv>=1.0.0
django-environ>=0.11.2
EOL
fi

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
cd /var/www/backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Configure PostgreSQL
echo "Configuring PostgreSQL..."
POSTGRES_VERSION=$(ls /etc/postgresql)
if [ -d "/etc/postgresql/$POSTGRES_VERSION/main" ]; then
    sudo -u postgres psql -c "CREATE DATABASE project_db;" || echo "Database might already exist, continuing..."
    sudo -u postgres psql -c "CREATE USER project_user WITH PASSWORD 'test_password';" || echo "User might already exist, continuing..."
    sudo -u postgres psql -c "ALTER ROLE project_user SET client_encoding TO 'utf8';"
    sudo -u postgres psql -c "ALTER ROLE project_user SET default_transaction_isolation TO 'read committed';"
    sudo -u postgres psql -c "ALTER ROLE project_user SET timezone TO 'UTC';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE project_db TO project_user;"
    
    # Configure PostgreSQL to allow local connections
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/$POSTGRES_VERSION/main/postgresql.conf
    sudo sed -i "s/local   all             all                                     peer/local   all             all                                     md5/" /etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf
    sudo systemctl restart postgresql
else
    echo "Warning: PostgreSQL configuration directory not found. Please check PostgreSQL installation."
fi

# Configure Redis
echo "Configuring Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Create environment file
echo "Creating environment file..."
cat > /var/www/backend/.env << EOL
DEBUG=True
SECRET_KEY=test_secret_key_123
DATABASE_URL=postgres://project_user:test_password@localhost:5432/project_db
ALLOWED_HOSTS=localhost,127.0.0.1,ec2-public-ip
REDIS_URL=redis://localhost:6379/0
EOL

# Set up media and static directories
echo "Setting up media and static directories..."
mkdir -p /var/www/backend/media
mkdir -p /var/www/backend/static

# Check for manage.py
if [ ! -f "/var/www/backend/manage.py" ]; then
    echo "Error: manage.py not found in /var/www/backend"
    echo "Current directory contents:"
    ls -la /var/www/backend
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
cd /var/www/backend
python manage.py migrate

# Create superuser (only if it doesn't exist)
echo "Creating superuser..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.get_or_create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell

# Configure Gunicorn
echo "Configuring Gunicorn..."
cat > /var/www/backend/gunicorn_config.py << EOL
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
timeout = 120
EOL

# Configure Supervisor
echo "Configuring Supervisor..."
sudo cat > /etc/supervisor/conf.d/backend.conf << EOL
[program:backend]
command=/var/www/backend/venv/bin/gunicorn -c /var/www/backend/gunicorn_config.py core.wsgi:application
directory=/var/www/backend
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/project.err.log
stdout_logfile=/var/log/project.out.log
environment=PYTHONPATH="/var/www/backend"
EOL

# Configure Nginx
echo "Configuring Nginx..."
sudo cat > /etc/nginx/sites-available/backend << EOL
server {
    listen 80;
    server_name localhost;

    location /static/ {
        alias /var/www/backend/static/;
    }

    location /media/ {
        alias /var/www/backend/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

# Enable Nginx configuration
sudo rm -f /etc/nginx/sites-enabled/backend
sudo ln -s /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Restart services
echo "Restarting services..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart backend
sudo systemctl restart nginx
sudo systemctl restart postgresql
sudo systemctl restart redis-server

echo "Deployment completed successfully!"
echo "You can access the application at: http://localhost"
echo "Admin credentials:"
echo "Username: admin"
echo "Password: admin123" 