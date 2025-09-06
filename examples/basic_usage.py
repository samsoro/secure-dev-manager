"""
Basic Usage Examples for Secure Development Manager
These examples demonstrate common development workflows
"""

# Example 1: Start a development server
# --------------------------------------
print("Starting React development server...")
# @secure-dev-manager execute_command "npm run dev" --cwd "C:/projects/my-app" --background


# Example 2: Find and kill a stuck process
# -----------------------------------------
print("Finding Python processes...")
# @secure-dev-manager find_process python

print("Killing stuck Django server on port 8000...")
# @secure-dev-manager check_ports 8000
# Get the PID from the output, then:
# @secure-dev-manager kill_process 12345


# Example 3: Check all development ports
# ---------------------------------------
print("Checking development ports...")
# @secure-dev-manager check_ports
# Shows status of ports: 3000, 5000, 8000, 8080, 5173, 4200


# Example 4: Virtual environment usage
# -------------------------------------
print("Installing packages in virtual environment...")
# @secure-dev-manager execute_command "pip install django" --cwd "C:/projects/django-app"
# Automatically uses C:/projects/django-app/.venv if it exists


# Example 5: Get server status
# -----------------------------
print("Getting status of all managed servers...")
# @secure-dev-manager server_status


# Example 6: List allowed commands
# ---------------------------------
print("Viewing all whitelisted commands...")
# @secure-dev-manager list_allowed


# Example 7: Find process by command arguments
# ---------------------------------------------
print("Finding specific Django management command...")
# @secure-dev-manager find_process "manage.py runserver" --include-args


# Example 8: Safe restart pattern
# --------------------------------
def safe_restart_server():
    """
    Pattern for safely restarting a development server
    """
    # 1. Check if port is in use
    # @secure-dev-manager check_ports 3000
    
    # 2. If in use, kill the process
    # @secure-dev-manager kill_process [pid]
    
    # 3. Start new server
    # @secure-dev-manager execute_command "npm run dev" --cwd "C:/projects/app" --background
    
    # 4. Verify it started
    # @secure-dev-manager check_ports 3000
    pass


# Example 9: Monitor resource usage
# ----------------------------------
def monitor_resources():
    """
    Check resource usage of development processes
    """
    # @secure-dev-manager find_process python
    # @secure-dev-manager find_process node
    # Look for high CPU % or memory_mb values
    pass


# Example 10: Multi-project setup
# --------------------------------
projects = {
    "frontend": {
        "path": "C:/projects/frontend",
        "start": "npm run dev",
        "port": 3000
    },
    "backend": {
        "path": "C:/projects/backend", 
        "start": "python manage.py runserver",
        "port": 8000
    },
    "database": {
        "path": "C:/projects",
        "start": "docker-compose up -d postgres",
        "port": 5432
    }
}

print("Starting all projects...")
for name, config in projects.items():
    print(f"Starting {name} on port {config['port']}...")
    # @secure-dev-manager execute_command "{config['start']}" --cwd "{config['path']}" --background