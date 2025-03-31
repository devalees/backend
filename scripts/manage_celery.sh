#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if Redis is running
check_redis() {
    if ! redis-cli ping > /dev/null 2>&1; then
        echo -e "${RED}Redis is not running. Starting Redis...${NC}"
        redis-server --daemonize yes
        sleep 2
    else
        echo -e "${GREEN}Redis is running${NC}"
    fi
}

# Function to start Celery worker
start_worker() {
    echo -e "${YELLOW}Starting Celery worker...${NC}"
    celery -A Core worker -l INFO -Q default,high_priority,low_priority &
    echo $! > celery_worker.pid
}

# Function to start Celery beat
start_beat() {
    echo -e "${YELLOW}Starting Celery beat...${NC}"
    celery -A Core beat -l INFO &
    echo $! > celery_beat.pid
}

# Function to start Flower monitoring
start_flower() {
    echo -e "${YELLOW}Starting Flower monitoring...${NC}"
    celery -A Core flower --port=5555 &
    echo $! > flower.pid
}

# Function to stop all processes
stop_all() {
    echo -e "${YELLOW}Stopping all Celery processes...${NC}"
    for pid_file in celery_worker.pid celery_beat.pid flower.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            kill $pid 2>/dev/null
            rm "$pid_file"
        fi
    done
    echo -e "${GREEN}All processes stopped${NC}"
}

# Main script
case "$1" in
    start)
        check_redis
        start_worker
        start_beat
        start_flower
        echo -e "${GREEN}All services started${NC}"
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        check_redis
        start_worker
        start_beat
        start_flower
        echo -e "${GREEN}All services restarted${NC}"
        ;;
    status)
        if [ -f "celery_worker.pid" ] && [ -f "celery_beat.pid" ] && [ -f "flower.pid" ]; then
            echo -e "${GREEN}All services are running${NC}"
        else
            echo -e "${RED}Some services are not running${NC}"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0 