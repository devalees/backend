# Project Management System

## Server Management Scripts

### 1. Starting the Server
To start the Django development server with error monitoring:

```bash
./run_server.sh
```

This script will:
- Activate the virtual environment
- Check for and apply any pending migrations
- Start the Django server
- Display server URL: http://<your-ip>:8000
- Monitor logs for errors
- Handle graceful shutdown on Ctrl+C

### 2. Monitoring Server Status
To monitor the server status and automatically restart if needed:

```bash
./check_server.sh
```

This script will:
- Check if the server is running
- Monitor logs for errors
- Automatically restart the server if:
  - The server is not running
  - Errors are detected in the logs
- Run checks every 5 minutes

### 3. Log Files
Server logs are stored in the `logs` directory:
- `logs/server.log`: Main server log file
- Errors are highlighted in red
- Server status changes are color-coded
- Server URL is displayed in blue

### 4. Error Handling
The scripts will:
- Detect and highlight errors in real-time
- Automatically restart the server if needed
- Maintain a log of all server activities
- Handle graceful shutdowns

### 5. Requirements
- Bash shell
- Python virtual environment
- Django installed in the virtual environment
- Proper permissions to execute scripts

### 6. Usage Example
```bash
# Terminal 1: Start the server
./run_server.sh

# Terminal 2: Monitor server status
./check_server.sh
```

### 7. Troubleshooting
If you encounter issues:
1. Check the logs in `logs/server.log`
2. Ensure the virtual environment is activated
3. Verify all dependencies are installed
4. Check file permissions on the scripts
5. Verify the server is accessible at the displayed URL 