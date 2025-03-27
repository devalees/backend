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
    pgrep -f "runserver.*8000" > /dev/null
    return $?
}

# Function to reset database
reset_db() {
    log_message "Starting database reset..." "$YELLOW"
    
    # Change to the project root directory
    cd "$(dirname "$0")/.." || {
        log_message "Failed to change to project root directory!" "$RED"
        return 1
    }
    
    # Execute the reset_db.sh script
    ./scripts/reset_db.sh
    
    if [ $? -eq 0 ]; then
        log_message "Database reset completed successfully!" "$GREEN"
        return 0
    else
        log_message "Database reset failed!" "$RED"
        return 1
    fi
}

# Function to start server
start_server() {
    if check_process; then
        log_message "Server is already running!" "$YELLOW"
        return 1
    fi
    
    log_message "Starting Django server..." "$YELLOW"
    
    # Change to the Apps directory
    cd "$(dirname "$0")/../Apps" || {
        log_message "Failed to change to Apps directory!" "$RED"
        return 1
    }
    
    # Add parent directory to PYTHONPATH
    export PYTHONPATH="$(dirname "$0")/..:$PYTHONPATH"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Start the server in the background
    nohup python manage.py runserver 8000 > ../server.log 2>&1 &
    
    # Wait for server to start
    for i in {1..5}; do
        if check_process; then
            log_message "Server started successfully! Showing logs..." "$GREEN"
            # Show server logs in real-time
            tail -f ../server.log
            return 0
        fi
        sleep 1
    done
    
    log_message "Failed to start server. Check server.log for details." "$RED"
    return 1
}

# Function to kill server process
kill_server() {
    if ! check_process; then
        log_message "No server process is running!" "$YELLOW"
        return 0
    fi
    
    log_message "Attempting to kill existing server process..." "$YELLOW"
    
    # Find and kill the Django server process
    pkill -f "runserver.*8000"
    
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
        pkill -9 -f "runserver.*8000"
        sleep 2
    fi
}

# Main execution
case "$1" in
    "start")
        start_server
        ;;
    "stop")
        kill_server
        ;;
    "reset_db")
        reset_db
        ;;
    *)
        echo "Usage: django {start|stop|restart|reset_db}"
        echo "  start    - Start the Django server and show logs"
        echo "  stop     - Stop the Django server"
        echo "  restart  - Restart the Django server"
        echo "  reset_db - Reset the database and create superuser"
        exit 1
        ;;
esac 