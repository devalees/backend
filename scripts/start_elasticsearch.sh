#!/bin/bash

# Script to start Elasticsearch on port 9201 for the backend project
# This script should be run with sudo

# Get the path to the elasticsearch config directory
ES_CONFIG_DIR=$(find /etc/elasticsearch -type d -name "elasticsearch" 2>/dev/null | head -1)

if [ -z "$ES_CONFIG_DIR" ]; then
    echo "Elasticsearch config directory not found."
    exit 1
fi

# Create a backup of the original elasticsearch.yml file if it doesn't exist
if [ ! -f "${ES_CONFIG_DIR}/elasticsearch.yml.original" ]; then
    echo "Creating backup of original elasticsearch.yml file..."
    sudo cp "${ES_CONFIG_DIR}/elasticsearch.yml" "${ES_CONFIG_DIR}/elasticsearch.yml.original"
fi

# Update the elasticsearch.yml file to use port 9201
echo "Updating elasticsearch.yml to use port 9201..."
sudo tee "${ES_CONFIG_DIR}/elasticsearch.yml" > /dev/null << EOL
# Custom configuration for backend project
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
http.port: 9201

# Completely disable security for development
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false

# Disable warning about disk space
cluster.routing.allocation.disk.threshold_enabled: false
EOL

# Restart Elasticsearch service
echo "Restarting Elasticsearch service..."
sudo systemctl daemon-reload
sudo systemctl restart elasticsearch.service

# Wait for Elasticsearch to start
echo "Waiting for Elasticsearch to start on port 9201..."
max_attempts=30
attempts=0
while ! curl -s "http://localhost:9201" > /dev/null; do
    attempts=$((attempts+1))
    if [ $attempts -ge $max_attempts ]; then
        echo "Elasticsearch failed to start on port 9201 after $max_attempts attempts."
        echo "Check Elasticsearch logs with: sudo journalctl -u elasticsearch.service"
        exit 1
    fi
    echo "Waiting for Elasticsearch to start... (attempt $attempts/$max_attempts)"
    sleep 2
done

echo "Elasticsearch is now running on port 9201"
echo "You can check the status with: curl -X GET 'http://localhost:9201'" 