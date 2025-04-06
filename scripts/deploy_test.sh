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

# Install Elasticsearch
echo "Installing Elasticsearch..."

# Add retry mechanism for package installation
MAX_RETRIES=3
RETRY_COUNT=0
SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$SUCCESS" = false ]; do
    echo "Attempt $(($RETRY_COUNT + 1)) of $MAX_RETRIES to install Elasticsearch..."
    
    # Import the Elasticsearch GPG key with retry
    if ! wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg; then
        echo "Failed to import GPG key, retrying..."
        sleep 10
        RETRY_COUNT=$((RETRY_COUNT + 1))
        continue
    fi

    # Add the Elasticsearch repository
    echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list

    # Update package list and install Elasticsearch
    if sudo apt-get update && sudo apt-get install -y elasticsearch; then
        SUCCESS=true
    else
        echo "Failed to install Elasticsearch, retrying..."
        sleep 10
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if [ "$SUCCESS" = false ]; then
    echo "Failed to install Elasticsearch after $MAX_RETRIES attempts"
    exit 1
fi

# Configure Elasticsearch
echo "Configuring Elasticsearch..."

# Create Elasticsearch configuration with minimal settings
sudo tee /etc/elasticsearch/elasticsearch.yml > /dev/null << EOL
# Cluster Configuration
cluster.name: my-application
node.name: node-1

# Paths
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch

# Network
network.host: 127.0.0.1
http.port: 9200

# Discovery
discovery.type: single-node

# Security - Disabled for development
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false

# Memory Settings - Minimal configuration
bootstrap.memory_lock: false
indices.memory.index_buffer_size: 1%
indices.queries.cache.size: 1%
indices.fielddata.cache.size: 1%

# Thread Pool Settings
thread_pool.write.queue_size: 100
thread_pool.search.queue_size: 100
EOL

# Set minimal JVM heap size for small instances
sudo tee /etc/elasticsearch/jvm.options.d/heap.options > /dev/null << EOL
-Xms64m
-Xmx64m
EOL

# Set correct permissions
sudo chown -R elasticsearch:elasticsearch /etc/elasticsearch
sudo chmod -R 750 /etc/elasticsearch

# Start and enable Elasticsearch with better error handling and memory monitoring
echo "Starting Elasticsearch service..."
sudo systemctl daemon-reload
sudo systemctl enable elasticsearch.service

# Print memory status before starting
echo "Current memory status:"
free -h

if ! sudo systemctl start elasticsearch.service; then
    echo "Failed to start Elasticsearch. Checking logs..."
    echo "Memory status at failure:"
    free -h
    echo "Elasticsearch logs:"
    sudo journalctl -u elasticsearch.service --no-pager | tail -n 50
    exit 1
fi

# Wait for Elasticsearch to start with better verification and timeout
echo "Waiting for Elasticsearch to start (this may take a few minutes)..."
TIMEOUT=300
START_TIME=$(date +%s)

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED_TIME=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED_TIME -gt $TIMEOUT ]; then
        echo "Timeout waiting for Elasticsearch to start"
        echo "Elasticsearch logs:"
        sudo journalctl -u elasticsearch.service --no-pager | tail -n 50
        exit 1
    fi
    
    if curl -s http://localhost:9200 > /dev/null 2>&1; then
        echo "Elasticsearch is running successfully"
        break
    else
        echo "Waiting for Elasticsearch to start... (${ELAPSED_TIME}s elapsed)"
        sleep 10
    fi
done

# Final verification
echo "Verifying Elasticsearch installation..."
if curl -s http://localhost:9200; then
    echo "Elasticsearch verification successful"
else
    echo "Elasticsearch verification failed. Please check the logs:"
    sudo journalctl -u elasticsearch.service --no-pager | tail -n 50
    exit 1
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

# Install core packages first
echo "Installing core packages..."
pip install Django==4.2.0
pip install djangorestframework==3.14.0

# Special handling for djangorestframework-simplejwt
echo "Installing djangorestframework-simplejwt..."
pip uninstall -y djangorestframework-simplejwt || true
pip install djangorestframework-simplejwt==5.3.1

# Install remaining packages
pip install psycopg2-binary==2.9.9
pip install redis==5.0.1
pip install gunicorn==21.2.0
pip install django-cors-headers==4.3.1
pip install drf-yasg==1.21.7
pip install python-dotenv==1.0.0
pip install django-environ==0.11.2
pip install django-import-export==3.3.4
pip install django-celery-results==2.5.1
pip install celery==5.3.6
pip install django-celery-beat==2.5.0
pip install django-filter==23.5
pip install django-storages==1.14.2
pip install Pillow==10.2.0
pip install pyotp==2.9.0
pip install qrcode==7.4.2
pip install django-otp==1.2.2
pip install django-two-factor-auth==1.16.0
pip install beautifulsoup4==4.12.3
pip install lxml==5.1.0
pip install requests==2.31.0
pip install elasticsearch==8.11.1
pip install elasticsearch-dsl==8.11.1
pip install django-elasticsearch-dsl==7.2.2
pip install django-elasticsearch-dsl-drf==0.22.0

# Debug: Show installed packages
echo "Installed packages:"
pip freeze | grep -E "Django|djangorestframework|simplejwt|import_export|celery|django_celery|pyotp|qrcode|django-otp|beautifulsoup4|lxml|requests|elasticsearch|elasticsearch-dsl"

# Verify installation
echo "Verifying package installation..."
python -c "
import sys
print('Python path:', sys.path)
try:
    import rest_framework_simplejwt
    print('rest_framework_simplejwt imported successfully')
except ImportError as e:
    print('ImportError:', e)
    sys.exit(1)
"

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