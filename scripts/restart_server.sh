#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="server_restart.log"

# Function to log messages
log_message() {
    echo -e "${2}${1}${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to check if a process is running
check_process() {
    pgrep -f "python manage.py runserver" > /dev/null
    return $?
}

# Function to kill server process
kill_server() {
    log_message "Attempting to kill existing server process..." "$YELLOW"
    
    # Find and kill the Django server process
    pkill -f "python manage.py runserver"
    
    # Wait for process to terminate
    for i in {1..5}; do
        if ! check_process; then
            log_message "Server process terminated successfully." "$GREEN"
            return 0
        fi
        sleep 1
    done
    
    # If process is still running, force kill it
    if check_process; then
        log_message "Force killing server process..." "$RED"
        pkill -9 -f "python manage.py runserver"
        sleep 2
    fi
}

# Function to start server
start_server() {
    log_message "Starting Django server..." "$YELLOW"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Start the server in the background
    nohup python manage.py runserver > server.log 2>&1 &
    
    # Wait for server to start
    for i in {1..5}; do
        if check_process; then
            log_message "Server started successfully!" "$GREEN"
            return 0
        fi
        sleep 1
    done
    
    log_message "Failed to start server. Check server.log for details." "$RED"
    return 1
}

# Main execution
log_message "Starting server restart process..." "$YELLOW"

# Kill existing server if running
if check_process; then
    kill_server
fi

# Start new server
start_server

# Check final status
if check_process; then
    log_message "Server restart completed successfully!" "$GREEN"
else
    log_message "Server restart failed. Please check the logs." "$RED"
    exit 1
fi 